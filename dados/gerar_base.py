"""
Gera a base de dados FICTÍCIA de chamados (Fase 1).

Saída: dados/chamados.csv  ->  colunas: mensagem, categoria, prioridade

Como funciona:
  - Para cada categoria temos várias frases "modelo", escritas de jeitos diferentes
    (formal, informal, com gíria e com erro de digitação), porque uma base variada
    faz o modelo de Machine Learning generalizar melhor.
  - Cada categoria tem uma prioridade típica (ex.: pagamento = alta).

Rode assim (dentro da pasta do projeto):
    python dados/gerar_base.py
"""

import csv
import os

# Pasta onde este arquivo está (para salvar o CSV ao lado dele)
PASTA = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(PASTA, "chamados.csv")

# ---------------------------------------------------------------------------
# Prioridade típica de cada categoria.
# (A prioridade NÃO é prevista por ML: é uma regra derivada da categoria,
#  espelhada em servicos/classificador.py.)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Frases por categoria. Quanto mais variado, melhor o modelo aprende.
# ---------------------------------------------------------------------------
FRASES = {
    "login": [
        "Não consigo entrar na minha conta",
        "Esqueci minha senha e não consigo logar",
        "Minha senha não está funcionando",
        "O site diz que meu login está incorreto",
        "Não recebo o email para redefinir a senha",
        "Minha conta foi bloqueada depois de tentar entrar",
        "Como faço login com o Google?",
        "Tento acessar minha conta mas fica carregando",
        "nao consigo fazer login de jeito nenhum",
        "quero recuperar meu acesso, esqueci a senha",
        "o codigo de verificacao nao chega pra eu entrar",
        "login dando erro toda vez que coloco minha senha",
        "Perdi acesso à minha conta, como recupero?",
        "A autenticação de dois fatores não está chegando",
        "Entrei com a senha certa e mesmo assim nao loga",
    ],
    "cadastro": [
        "Como faço para criar uma conta?",
        "Não consigo finalizar meu cadastro",
        "O site não aceita meu CPF no cadastro",
        "Meu email já está cadastrado e não sei por quê",
        "Quero atualizar meus dados cadastrais",
        "Como mudo meu endereço no cadastro?",
        "Preciso trocar meu número de telefone na conta",
        "o formulario de cadastro nao envia",
        "nao recebo o email de confirmacao do cadastro",
        "quero me cadastrar mas da erro no CEP",
        "Como altero meu nome no perfil?",
        "Meu cadastro ficou incompleto, como termino?",
        "Posso ter duas contas com o mesmo email?",
        "Erro ao salvar meus dados pessoais",
        "nao consigo concluir o registro no app",
    ],
    "produto": [
        "Esse produto tem garantia?",
        "Qual a voltagem desse aparelho?",
        "Esse notebook vem com carregador?",
        "Quais as dimensões do produto?",
        "Esse tênis tem no tamanho 42?",
        "Qual a diferença entre esses dois modelos?",
        "O produto é original?",
        "quero saber a cor desse celular",
        "esse produto serve para qual uso?",
        "tem manual em portugues?",
        "De que material é feito esse item?",
        "Esse produto é compatível com meu aparelho?",
        "Qual a capacidade dessa geladeira?",
        "vem quantas unidades na caixa?",
        "esse monitor tem quantas polegadas",
    ],
    "estoque": [
        "Esse produto está disponível?",
        "Quando vai voltar ao estoque?",
        "O item que eu quero está esgotado",
        "Tem em estoque na cor azul?",
        "Vocês vão repor esse produto?",
        "Avisa quando chegar mais unidades?",
        "esse tamanho ta disponivel ainda?",
        "quero saber se ainda tem em estoque",
        "o produto sumiu do site, acabou?",
        "tem previsao de reposicao desse item?",
        "Ainda há unidades disponíveis para compra?",
        "esgotou bem na hora que eu ia comprar",
        "quantas pecas ainda tem no estoque",
        "esse modelo esta indisponivel, vai voltar?",
        "preciso de 10 unidades, tem no estoque?",
    ],
    "carrinho": [
        "Adicionei um produto mas sumiu do carrinho",
        "Não consigo adicionar itens ao carrinho",
        "Meu carrinho esvaziou sozinho",
        "O botão de adicionar ao carrinho não funciona",
        "Quero remover um item do carrinho",
        "O carrinho não atualiza a quantidade",
        "coloquei no carrinho e nao salvou",
        "meu carrinho ta travado, nao deixa mexer",
        "o valor no carrinho esta errado",
        "nao consigo mudar a quantidade no carrinho",
        "Os itens que escolhi não aparecem no carrinho",
        "carrinho some quando eu troco de pagina",
        "da erro quando tento ir pro carrinho",
        "quero juntar dois produtos no mesmo carrinho",
        "o frete no carrinho nao esta calculando",
    ],
    "pagamento": [
        "Paguei via Pix mas o pedido continua aguardando pagamento",
        "Meu pagamento no cartão foi recusado",
        "Gerei o boleto mas não consigo pagar",
        "O site cobrou duas vezes no meu cartão",
        "Fiz o pagamento e não foi confirmado",
        "Como parcelo no cartão de crédito?",
        "o pix caiu mas o sistema nao reconheceu",
        "paguei o boleto e ainda consta como pendente",
        "meu cartao foi negado sem motivo",
        "fui cobrado mas o pedido nao foi aprovado",
        "Posso pagar com dois cartões?",
        "o pagamento ficou processando e nao sai disso",
        "cobraram um valor diferente do que estava no site",
        "paguei via pix e nao recebi confirmacao nenhuma",
        "meu boleto venceu, consigo gerar outro?",
        "o checkout nao aceita meu cartao de credito",
    ],
    "cupom": [
        "Meu cupom de desconto não funciona",
        "Onde coloco o código do cupom?",
        "O cupom aparece como inválido",
        "Esse cupom ainda está valendo?",
        "Apliquei o cupom mas o preço não mudou",
        "O cupom expirou antes do prazo?",
        "meu cupom nao da desconto nenhum",
        "o campo de cupom nao aceita meu codigo",
        "ganhei um cupom mas nao sei usar",
        "o desconto do cupom nao apareceu no total",
        "Posso usar dois cupons na mesma compra?",
        "cupom dando erro na hora de pagar",
        "esse produto aceita cupom de desconto?",
        "digitei o cupom certo e diz que é invalido",
        "o cupom some quando finalizo a compra",
    ],
    "pedido": [
        "Quero ver o status do meu pedido",
        "Onde acompanho meu pedido?",
        "Meu pedido ainda não foi confirmado",
        "Qual o número do meu pedido?",
        "Fiz um pedido e não recebi email nenhum",
        "Meu pedido está como em separação há dias",
        "quero saber se meu pedido foi aprovado",
        "nao encontro meu pedido no site",
        "meu pedido consta como processando ainda",
        "fiz o pedido errado, queria conferir",
        "Preciso alterar o endereço do meu pedido",
        "o historico de pedidos nao esta carregando",
        "meu pedido sumiu da minha conta",
        "quero o comprovante do meu pedido",
        "quando meu pedido vai ser separado?",
    ],
    "entrega": [
        "Meu pedido está atrasado na entrega",
        "Quero rastrear minha encomenda",
        "O código de rastreio não atualiza",
        "A entrega não chegou no prazo",
        "O produto chegou danificado",
        "Recebi o produto errado",
        "quando meu pedido vai ser entregue?",
        "o rastreamento esta parado faz dias",
        "minha entrega esta muito atrasada",
        "o entregador nao encontrou meu endereco",
        "Qual a previsão de entrega do meu pedido?",
        "a encomenda foi devolvida, e agora?",
        "meu produto nao chegou ainda e ja passou do prazo",
        "nao recebi minha compra e o prazo venceu",
        "como mudo o endereco de entrega?",
        "o rastreio diz entregue mas eu nao recebi",
    ],
    "cancelamento": [
        "Quero cancelar meu pedido",
        "Como faço para cancelar a compra?",
        "Pedi por engano, quero cancelar",
        "Preciso cancelar e pedir reembolso",
        "Comprei errado e quero cancelar agora",
        "Como solicito o estorno do valor?",
        "quero devolver o produto e receber meu dinheiro",
        "cancelei mas nao recebi o reembolso",
        "da pra cancelar antes de enviar?",
        "quero desistir da compra, como cancelo?",
        "Me arrependi da compra, quero o dinheiro de volta",
        "preciso cancelar urgente, comprei o item errado",
        "como funciona o reembolso de um cancelamento?",
        "quero cancelar a assinatura e ser reembolsado",
        "pedido duplicado, preciso cancelar um deles",
    ],
}


def gerar():
    linhas = []
    for categoria, frases in FRASES.items():
        prioridade = PRIORIDADE_POR_CATEGORIA[categoria]
        for frase in frases:
            linhas.append({
                "mensagem": frase,
                "categoria": categoria,
                "prioridade": prioridade,
            })

    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["mensagem", "categoria", "prioridade"])
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"Base gerada com {len(linhas)} chamados em: {SAIDA}")
    # Mostra quantos exemplos por categoria
    from collections import Counter
    contagem = Counter(l["categoria"] for l in linhas)
    for cat, qtd in contagem.items():
        print(f"  - {cat:14s}: {qtd} frases")


if __name__ == "__main__":
    gerar()
