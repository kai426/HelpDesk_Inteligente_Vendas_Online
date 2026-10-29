"""
Respostas BASE por categoria (Fase 1).

Essas respostas são "prontas", escritas por humanos. Elas servem para dois casos:
  1) Resposta rápida quando usamos só a Fase 1 (sem LLM).
  2) Contexto enviado para a LLM na Fase 2/3, para ela gerar algo mais humano
     SEM inventar informação.
"""

RESPOSTAS_BASE = {
    "login": "Verifique se o email e a senha estão corretos. "
             "Se esqueceu a senha, use a opção 'Esqueci minha senha' para redefinir.",
    "cadastro": "Confira se todos os campos obrigatórios foram preenchidos corretamente. "
                "Se o email já estiver cadastrado, tente recuperar o acesso.",
    "produto": "As informações completas do produto estão na página de descrição. "
               "Se faltar algum detalhe, podemos verificar para você.",
    "estoque": "Vamos verificar a disponibilidade desse item no estoque. "
               "Você pode ativar o aviso de reposição na página do produto.",
    "carrinho": "Tente atualizar a página ou limpar o cache. "
                "Se o item sumir do carrinho, adicione novamente e confira a quantidade.",
    "pagamento": "Verifique o status do pagamento na sua conta. "
                 "Pagamentos via Pix e cartão podem levar alguns minutos para serem confirmados; "
                 "boletos podem levar até alguns dias úteis.",
    "cupom": "Confira se o cupom foi digitado corretamente, se está dentro da validade, "
             "se o produto participa da promoção e se atende ao valor mínimo.",
    "pedido": "Você pode acompanhar o status do pedido em 'Meus Pedidos'. "
              "Informe o número do pedido para que possamos localizar com rapidez.",
    "entrega": "Acompanhe sua entrega pelo código de rastreio em 'Meus Pedidos'. "
               "Se o prazo passou, vamos verificar o que aconteceu com a transportadora.",
    "cancelamento": "Pedidos ainda não enviados geralmente podem ser cancelados. "
                    "Vamos verificar o status e, se possível, iniciar o cancelamento e o reembolso.",
}


def resposta_base(categoria: str) -> str:
    """Retorna a resposta base da categoria, ou uma genérica se não existir."""
    return RESPOSTAS_BASE.get(
        categoria,
        "Recebemos sua mensagem e vamos te ajudar. Um atendente pode dar continuidade se necessário.",
    )
