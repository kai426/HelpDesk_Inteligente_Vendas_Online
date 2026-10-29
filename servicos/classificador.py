"""
FASE 1 — Serviço de classificação.

Carrega o modelo de categoria treinado e, a partir da mensagem do cliente,
retorna: categoria prevista, prioridade e resposta base.

A PRIORIDADE é derivada da categoria por uma regra de negócio simples, deixando
a decisão previsível e fácil de explicar.
"""

import os
import joblib

from dados.respostas import resposta_base

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_MODELO = os.path.join(PASTA_PROJETO, "modelo", "modelo_categoria.pkl")

# Prioridade padrão de cada categoria (mesma lógica usada ao gerar a base).
PRIORIDADE_POR_CATEGORIA = {
    "login": "media",
    "cadastro": "baixa",
    "produto": "baixa",
    "estoque": "media",
    "carrinho": "media",
    "pagamento": "alta",
    "cupom": "baixa",
    "pedido": "media",
    "entrega": "alta",
    "cancelamento": "critica",
}

_modelo = None


def _carregar_modelo():
    global _modelo
    if _modelo is None:
        if not os.path.exists(ARQ_MODELO):
            raise FileNotFoundError(
                f"Modelo não encontrado em {ARQ_MODELO}.\n"
                f"Treine primeiro:  python modelo/treinar.py"
            )
        _modelo = joblib.load(ARQ_MODELO)
    return _modelo


def classificar(mensagem: str) -> dict:
    """Recebe a mensagem do cliente e devolve categoria, prioridade e resposta base.

    Também devolve a confiança (probabilidade) da categoria prevista, útil para
    decidir se vale encaminhar para um humano quando o modelo está em dúvida.
    """
    modelo = _carregar_modelo()

    categoria = modelo.predict([mensagem])[0]

    try:
        probs = modelo.predict_proba([mensagem])[0]
        confianca = float(max(probs))
    except Exception:
        confianca = None

    prioridade = PRIORIDADE_POR_CATEGORIA.get(categoria, "media")

    return {
        "categoria": categoria,
        "prioridade": prioridade,
        "confianca": confianca,
        "resposta_base": resposta_base(categoria),
    }


if __name__ == "__main__":
    # Teste rápido no terminal:  python -m servicos.classificador
    exemplos = [
        "Paguei via Pix mas meu pedido continua aguardando pagamento",
        "Meu cupom não funciona na hora de pagar",
        "Quero cancelar meu pedido e receber o reembolso",
        "O rastreio diz entregue mas eu não recebi",
        "Esqueci minha senha e não consigo entrar",
        "Esse produto tem no tamanho 42?",
    ]
    for ex in exemplos:
        r = classificar(ex)
        conf = f"{r['confianca']:.0%}" if r["confianca"] is not None else "-"
        print(f"\n> {ex}")
        print(f"  categoria={r['categoria']} | prioridade={r['prioridade']} | confiança={conf}")
        print(f"  resposta_base: {r['resposta_base']}")
