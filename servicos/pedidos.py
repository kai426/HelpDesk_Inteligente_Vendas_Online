"""
FASE 3 — Serviço de pedidos.

- Consulta um "banco fake" de pedidos (dados/pedidos.json).
- Decide, por REGRAS (não por IA), se um chamado deve ser aberto.

Por que a decisão é por regra e não pela LLM?
  Abrir chamado é uma ação do negócio. O sistema deve controlar isso de forma
  previsível e auditável: a mesma situação sempre gera a mesma decisão, e é
  possível testar e justificar cada caso. A LLM ajuda a ESCREVER a resposta,
  mas quem DECIDE é o código.
"""

import os
import json

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_PEDIDOS = os.path.join(PASTA_PROJETO, "dados", "pedidos.json")

_pedidos = None


def _carregar_pedidos() -> dict:
    global _pedidos
    if _pedidos is None:
        with open(ARQ_PEDIDOS, "r", encoding="utf-8") as f:
            _pedidos = json.load(f)
    return _pedidos


def consultar_pedido(numero_pedido) -> dict:
    """Procura o pedido pelo número.

    Sempre retorna um dicionário com:
      - 'informado': se o cliente enviou algum número
      - 'encontrado': se o número existe na base
      - 'numero_pedido' e 'dados'
    """
    informado = numero_pedido is not None and str(numero_pedido).strip() != ""
    if not informado:
        return {"informado": False, "encontrado": False, "numero_pedido": None, "dados": None}

    numero = str(numero_pedido).strip()
    dados = _carregar_pedidos().get(numero)

    if dados is None:
        return {"informado": True, "encontrado": False, "numero_pedido": numero, "dados": None}

    return {"informado": True, "encontrado": True, "numero_pedido": numero, "dados": dados}


def decidir_abertura_chamado(categoria: str, prioridade: str, pedido: dict) -> dict:
    """Decide se abre um chamado e explica o motivo.

    Regras, avaliadas nesta ordem:
      0. Número de pedido informado mas NÃO encontrado -> NÃO abre.
         (Não dá para agir sobre um pedido que não existe; primeiro o cliente
          precisa conferir o número.)
      1. Prioridade crítica (cancelamento/reembolso)   -> abre.
      2. Pagamento pendente ou recusado                -> abre.
      3. Entrega atrasada ou produto com avaria        -> abre.
      4. Prioridade alta                               -> abre.
      5. Caso contrário                                -> não abre (orientação resolve).

    Retorna {'abrir': bool, 'motivo': str, 'numero_chamado': str|None}.
    """
    # Regra 0: pedido informado e inexistente -> não abre.
    if pedido.get("informado") and not pedido.get("encontrado"):
        return {
            "abrir": False,
            "motivo": "Número de pedido não encontrado na base. O cliente precisa conferir o número.",
            "numero_chamado": None,
        }

    dados = pedido.get("dados") or {}
    status_pagamento = (dados.get("status_pagamento") or "").lower()
    status_entrega = (dados.get("status_entrega") or "").lower()

    abrir = False
    motivo = "Dúvida simples: pode ser resolvida com orientação automática."

    if prioridade == "critica":
        abrir, motivo = True, "Prioridade crítica (ex.: cancelamento/reembolso)."
    elif status_pagamento in ("pendente", "recusado"):
        abrir, motivo = True, f"Pagamento {status_pagamento}: cliente não consegue concluir a compra."
    elif "atras" in status_entrega or "avaria" in status_entrega:
        abrir, motivo = True, f"Problema na entrega (status: {status_entrega})."
    elif prioridade == "alta":
        abrir, motivo = True, "Prioridade alta."

    numero_chamado = None
    if abrir:
        # Número de chamado fictício: usa o pedido quando existe, senão um genérico.
        base = pedido.get("numero_pedido") if pedido.get("encontrado") else "SP"
        numero_chamado = f"CH-{base}"

    return {"abrir": abrir, "motivo": motivo, "numero_chamado": numero_chamado}


if __name__ == "__main__":
    # Teste rápido:  python -m servicos.pedidos
    casos = [
        ("pagamento", "alta", "1001", "pagamento pendente -> deve abrir"),
        ("entrega", "alta", "1005", "entrega atrasada -> deve abrir"),
        ("entrega", "alta", "1008", "entregue com avaria -> deve abrir"),
        ("cupom", "baixa", "1002", "duvida simples -> NAO abre"),
        ("cancelamento", "critica", "1002", "critica -> deve abrir"),
        ("cancelamento", "critica", "9999", "pedido inexistente -> NAO abre"),
        ("cupom", "baixa", "", "sem numero de pedido -> NAO abre"),
    ]
    for categoria, prioridade, numero, esperado in casos:
        p = consultar_pedido(numero)
        d = decidir_abertura_chamado(categoria, prioridade, p)
        marca = "ABRE " if d["abrir"] else "nao  "
        print(f"[{marca}] pedido={numero or '(vazio)':6s} {categoria:13s} | {esperado}")
        print(f"          -> {d['motivo']} chamado={d['numero_chamado']}")
