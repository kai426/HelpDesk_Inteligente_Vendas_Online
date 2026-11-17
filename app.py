"""
HelpDesk Inteligente — API Flask reunindo as 3 fases.

Endpoints:
  GET  /                  -> página HTML de teste (3 abas)
  POST /classificar       -> FASE 1: categoria + prioridade + resposta base
  POST /atender           -> FASE 2: resposta humanizada com LLM (Gemini)
  POST /atender-completo  -> FASE 3: texto + nº do pedido + imagem + decisão

Rode assim (dentro da pasta do projeto, com o modelo já treinado):
    python app.py
Depois abra:  http://localhost:5000
"""

import os
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template

from servicos.classificador import classificar
from servicos.llm import gerar_resposta, analisar_imagem, gerar_resposta_final, llm_disponivel
from servicos.pedidos import consultar_pedido, decidir_abertura_chamado

app = Flask(__name__)

PASTA_UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(PASTA_UPLOADS, exist_ok=True)

EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
TAMANHO_MAXIMO = 8 * 1024 * 1024  # 8 MB por imagem
app.config["MAX_CONTENT_LENGTH"] = TAMANHO_MAXIMO


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

    c = classificar(mensagem)
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


# ---------------------------------------------------------------------------
# FASE 3 — atender-completo (texto + pedido + imagem + decisão)
# ---------------------------------------------------------------------------
@app.route("/atender-completo", methods=["POST"])
def rota_atender_completo():
    # Os dados chegam como formulário (multipart), porque pode haver imagem.
    mensagem = (request.form.get("mensagem") or "").strip()
    numero_pedido = (request.form.get("numero_pedido") or "").strip()

    if not mensagem:
        return jsonify({"erro": "Envie o campo 'mensagem'."}), 400

    # 1) Classifica a dúvida (Fase 1)
    c = classificar(mensagem)

    # 2) Consulta o pedido no banco fake (Fase 3)
    pedido = consultar_pedido(numero_pedido)

    # 3) Analisa a imagem, se o cliente enviou uma (Fase 3, multimodal)
    analise = None
    arquivo = request.files.get("imagem")
    if arquivo and arquivo.filename:
        ext = os.path.splitext(arquivo.filename)[1].lower()
        if ext not in EXTENSOES_IMAGEM:
            return jsonify({
                "erro": f"Formato de imagem não suportado: {ext or '(sem extensão)'}. "
                        f"Use PNG, JPG ou WEBP."
            }), 400
        nome_seguro = secure_filename(arquivo.filename) or "imagem.png"
        caminho_imagem = os.path.join(PASTA_UPLOADS, nome_seguro)
        arquivo.save(caminho_imagem)
        analise = analisar_imagem(caminho_imagem, mensagem)

    # 4) Decide se abre chamado (REGRA do sistema, não a LLM)
    decisao = decidir_abertura_chamado(c["categoria"], c["prioridade"], pedido)

    # 5) Gera a resposta final juntando tudo (LLM, com fallback)
    resposta = gerar_resposta_final(
        mensagem=mensagem,
        categoria=c["categoria"],
        prioridade=c["prioridade"],
        resposta_base=c["resposta_base"],
        pedido=pedido,
        decisao=decisao,
        analise_imagem=analise,
    )

    # Resposta no formato do enunciado + campos extras úteis
    return jsonify({
        "categoria": c["categoria"],
        "prioridade": c["prioridade"],
        "dados_pedido": pedido,
        "analise_imagem": analise,
        "chamado": {
            "aberto": decisao["abrir"],
            "numero_chamado": decisao["numero_chamado"],
            "motivo": decisao["motivo"],
        },
        "resposta_cliente": resposta,
        "usou_llm": llm_disponivel(),
    })


@app.errorhandler(413)
def arquivo_grande(_):
    return jsonify({"erro": "Imagem muito grande. O limite é 8 MB."}), 413


if __name__ == "__main__":
    print("=" * 60)
    print("HelpDesk Inteligente — Fases 1, 2 e 3")
    print("Rodando em http://localhost:5000")
    print(f"LLM (Gemini) disponível: {llm_disponivel()}")
    if not llm_disponivel():
        print("  -> Sem chave do Gemini (ou SDK 'google-genai' não instalado):")
        print("     o sistema roda em modo FALLBACK (respostas base da Fase 1).")
        print("     Configure o .env e rode: pip install -r requirements.txt")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
