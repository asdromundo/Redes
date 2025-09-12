import multiprocessing
import requests
from flask import Flask, request, jsonify
from werkzeug.serving import run_simple


def start_server(q: multiprocessing.Queue):
    app = Flask(__name__)

    @app.post("/api/v1/endpoint")
    def endpoint():
        data = request.get_json(force=True)
        valor = data.get("valor")
        name = data.get("name")

        if valor >= 50:
            status = "FIN"
            q.put({"valor": valor, "name": name, "status": status})
            return jsonify({"status": "finished"}), 200
        else:
            payload = {"valor": valor + 1, "name": name}
            requests.post("http://localhost:5000/api/v1/endpoint", json=payload)
            return jsonify({"status": "forwarded", "payload": payload}), 200

    run_simple("localhost", 5000, app)


if __name__ == "__main__":
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start_server, args=(q,))
    p.start()
    print("Esperando resultado...")

    result = q.get(block=True)  # se desbloquea cuando el server hace q.put
    print("Recibido:", result)

    p.terminate()
    print("Servidor apagado")
