"""
FASE 1 — API Flask (apenas classificação).

Endpoints:
  GET  /             -> página HTML simples de teste
  POST /classificar  -> recebe a mensagem do cliente e devolve
                        categoria + prioridade + resposta base

Rode assim (dentro da pasta do projeto, com o modelo já treinado):
    python app.py
Depois abra:  http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template

from servicos.classificador import classificar

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classificar", methods=["POST"])
def rota_classificar():
    dados = request.get_json(silent=True) or {}
    mensagem = (dados.get("mensagem") or "").strip()
    if not mensagem:
        return jsonify({"erro": "Envie o campo 'mensagem'."}), 400

    resultado = classificar(mensagem)
    return jsonify(resultado)


if __name__ == "__main__":
    print("=" * 60)
    print("HelpDesk Inteligente — FASE 1 (classificação)")
    print("Rodando em http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
