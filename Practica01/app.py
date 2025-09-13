from enum import Enum
import uuid
import requests
from flask import Flask, request, jsonify, url_for
from decouple import config

HOST_USERNAME = config("HOST_USERNAME", default="none")  # Team member's name
STARTING_VAL = config("STARTING_VAR", default=0, cast=int)
ENDPOINT = config("ENDPOINT", default="http://localhost:5000/")


class Role(Enum):
    STARTER = "starter"
    WORKER = "worker"
    UNDEFINED = "undefined"


STOP = False  # When True, the server will not accept new requests
HOST_ROLE = Role.UNDEFINED
ID = uuid.uuid4()  # When set defines the STARTER role by consensus

app = Flask(__name__)
app.config["SERVER_NAME"] = config("HOST_URL", default="localhost:5000")


@app.route("/api/v1/leader", methods=["POST"])
def leader():
    global HOST_ROLE
    if HOST_ROLE != Role.UNDEFINED:
        return jsonify({"error": "The leader is already set"}), 400

    data = request.get_json(force=True)
    incoming_id = data.get("id")
    leader_found = data.get("leaderFound", False)

    if incoming_id is None or leader_found is None:
        return jsonify({"error": "Falta el campo 'id'"}), 400

    url = ENDPOINT + url_for("leader")

    if leader_found:
        HOST_ROLE = Role.WORKER
        payload = {"id": incoming_id, "leaderFound": True}
        requests.post(url, json=payload, timeout=3)
        return "OK", 200

    incoming_id = uuid.UUID(incoming_id)
    if incoming_id == ID:
        print("I am the leader")
        HOST_ROLE = Role.STARTER
        payload = {"id": str(ID), "leaderFound": True}
        requests.post(url, json=payload, timeout=3)
        url = ENDPOINT + url_for("counter")
        requests.post(
            url,
            json={"valor": STARTING_VAL, "name": HOST_USERNAME},
            timeout=3,
        )
        return "OK", 200

    next_id = incoming_id if incoming_id > ID else ID
    payload = {"id": str(next_id)}
    try:
        requests.post(url, json=payload, timeout=3)
    except requests.RequestException:
        pass
    return jsonify({"id": str(ID), "role": HOST_ROLE.value})


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.post("/api/v1/counter")
def counter():
    data = request.get_json(force=True)
    valor = data.get("valor")
    name = data.get("name")
    if valor is None or name is None:
        return jsonify({"error": "Faltan campos 'valor' o 'name'"}), 400

    if STOP:
        return jsonify({"error": "No se aceptan nuevas solicitudes"}), 400

    if valor >= 50:
        stop_task()
        message = f"Proceso finalizado en {HOST_USERNAME} con valor {valor}"
        payload = {"valor": valor, "name": HOST_USERNAME, "status": message}
        url = ENDPOINT + url_for("finish")
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.RequestException as e:
            print(f"Error al enviar la solicitud: {e}")
        print(message)
        return payload, 200

    else:
        payload = {"valor": valor + 1, "name": HOST_USERNAME}
        url = ENDPOINT + url_for("counter")

    try:
        requests.post(url, json=payload, timeout=3)
    except requests.RequestException:
        pass

    return jsonify({"status": "OK", "forwarded": payload}), 200


@app.post("/api/v1/finish")
def finish():
    if STOP:
        return jsonify({"error": "No se aceptan nuevas solicitudes"}), 400

    data = request.get_json(force=True)
    valor = data.get("valor")
    name = data.get("name")
    status = data.get("status")

    if valor is None or name is None or status is None:
        return jsonify({"error": "Faltan campos 'valor', 'name' o 'status'"}), 400

    print(f"Proceso finalizado en {name} con valor {valor}")
    stop_task()
    return "OK", 200


def stop_task():
    global STOP
    STOP = True


if __name__ == "__main__":
    app.run()  # Sets the port to 8000
