"""
HelpDesk Inteligente — Fases 1 e 2.

Endpoints:
  GET  /             -> página HTML de teste (abas Fase 1 e Fase 2)
  POST /classificar  -> FASE 1: categoria + prioridade + resposta base
  POST /atender      -> FASE 2: classifica e gera resposta humanizada (Gemini)

Rode assim (dentro da pasta do projeto, com o modelo já treinado):
    python app.py
Depois abra:  http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template

from servicos.classificador import classificar
from servicos.llm import gerar_resposta, llm_disponivel

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", llm_ok=llm_disponivel())


# ---------------------------------------------------------------------------
# FASE 1 — classificar
# ---------------------------------------------------------------------------
@app.route("/classificar", methods=["POST"])
def rota_classificar():
    dados = request.get_json(silent=True) or {}
    mensagem = (dados.get("mensagem") or "").strip()
    if not mensagem:
        return jsonify({"erro": "Envie o campo 'mensagem'."}), 400

    return jsonify(classificar(mensagem))


# ---------------------------------------------------------------------------
# FASE 2 — atender (classificador + LLM)
# ---------------------------------------------------------------------------
@app.route("/atender", methods=["POST"])
def rota_atender():
    dados = request.get_json(silent=True) or {}
    mensagem = (dados.get("mensagem") or "").strip()
    if not mensagem:
        return jsonify({"erro": "Envie o campo 'mensagem'."}), 400

    # 1) Classifica (Fase 1)
    c = classificar(mensagem)

    # 2) Gera resposta humanizada (Fase 2)
    resposta = gerar_resposta(
        mensagem=mensagem,
        categoria=c["categoria"],
        prioridade=c["prioridade"],
        resposta_base=c["resposta_base"],
    )

    return jsonify({
        "categoria": c["categoria"],
        "prioridade": c["prioridade"],
        "resposta_base": c["resposta_base"],
        "resposta_cliente": resposta,
        "usou_llm": llm_disponivel(),
    })


if __name__ == "__main__":
    print("=" * 60)
    print("HelpDesk Inteligente — Fases 1 e 2")
    print("Rodando em http://localhost:5000")
    print(f"LLM (Gemini) disponível: {llm_disponivel()}")
    if not llm_disponivel():
        print("  -> Sem chave do Gemini (ou SDK 'google-genai' não instalado):")
        print("     o /atender roda em modo FALLBACK (usa a resposta base da Fase 1).")
        print("     Configure o arquivo .env e rode: pip install -r requirements.txt")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
