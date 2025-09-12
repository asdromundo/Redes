import os
import signal
import time
import requests
from flask import Flask, request, jsonify, url_for
from decouple import config, Choices


PID = os.getpid()
HOST_ROLE = config(
    "HOST_ROLE", default="worker", cast=Choices(["starter", "worker"])
)  # 'starter' or 'worker'
HOST_USERNAME = config(
    "HOST_USERNAME", default="none"
)  # "Nombre del miembro del equipo"
HOST_URL = config("HOST_URL", default="http://localhost:5000")
PORT = config("PORT", default=5000, cast=int)
STARTING_VAR = config("STARTING_VAR", default=0, cast=int)
ENDPOINT = config("ENDPOINT", default="http://localhost:5000/")

STOP = False

app = Flask(__name__)
app.config["SERVER_NAME"] = HOST_URL.replace("http://", "").replace("https://", "")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.post("/api/v1/endpoint")
def endpoint():
    data = request.get_json(force=True)
    valor = data.get("valor")
    name = data.get("name")

    if valor is None or name is None:
        return jsonify({"error": "Faltan campos 'valor' o 'name'"}), 400

    if STOP:
        return jsonify({"error": "No se aceptan nuevas solicitudes"}), 400

    if valor >= 50:
        status = "Terminado"
        payload = {"valor": valor, "name": name, "status": status}
        url = ENDPOINT + url_for("finish")

        return "OK", 200

    else:
        payload = {"valor": valor + 1, "name": name}
        url = ENDPOINT

    try:
        requests.post(f"{url}/", json=payload, timeout=3)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "OK", "forwarded": payload}), 200


@app.post("/api/v1/finish")
def finish():
    data = request.get_json(force=True)
    valor = data.get("valor")
    name = data.get("name")
    status = data.get("status")

    if valor is None or name is None or status is None:
        return jsonify({"error": "Faltan campos 'valor', 'name' o 'status'"}), 400

    return "OK", 200


def stop_server():
    global STOP
    STOP = True


if __name__ == "__main__":
    app.run()  # Sets the port to 8000
