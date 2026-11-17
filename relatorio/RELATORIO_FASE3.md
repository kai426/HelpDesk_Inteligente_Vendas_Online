# Relatório — Fase 3: Atendimento avançado com imagem, pedido e decisão automática

> Material-base para o seu relatório/apresentação. Reescreva com suas palavras.

## 1. Objetivo da fase

Nas fases anteriores, o sistema só trabalhava com o **texto** da mensagem. A Fase 3
transforma o HelpDesk em um atendimento realmente completo, acrescentando três
capacidades:

1. **Consultar o pedido** do cliente em uma base de dados.
2. **Analisar uma imagem** enviada pelo cliente (por exemplo, o print de uma tela de erro).
3. **Decidir automaticamente** se o caso precisa de um chamado para atendimento humano.

Tudo isso é reunido em uma única resposta final, personalizada com os dados reais do pedido.

## 2. O fluxo completo

O endpoint `POST /atender-completo` executa cinco etapas em ordem:

| Etapa | O que acontece | Quem faz |
|---|---|---|
| 1 | Classifica a mensagem (categoria + prioridade) | Machine Learning (Fase 1) |
| 2 | Consulta o pedido pelo número | Código (`servicos/pedidos.py`) |
| 3 | Analisa a imagem enviada | LLM multimodal (Gemini) |
| 4 | Decide se abre chamado | **Código, por regras** |
| 5 | Gera a resposta final ao cliente | LLM (Gemini) |

Repare na divisão de papéis: a IA **entende e escreve**, mas quem **decide** é o código.

## 3. O banco de pedidos (fictício)

Como não temos um sistema real de vendas, criamos um banco fake em `dados/pedidos.json`
com 8 pedidos, cada um em uma situação diferente, para conseguirmos testar todos os
caminhos do sistema:

| Pedido | Situação |
|---|---|
| 1001 | Pagamento pendente (Pix) |
| 1002 | Pago, em separação |
| 1003 | Enviado, em transporte |
| 1004 | Entregue |
| 1005 | Entrega atrasada |
| 1006 | Cancelado / estornado |
| 1007 | Pagamento recusado |
| 1008 | Entregue com avaria |

Cada pedido tem cliente, produto, status do pedido, status do pagamento, método de
pagamento, status da entrega e valor — como no exemplo do enunciado.

## 4. Análise de imagem (parte multimodal)

Esta é a novidade técnica mais interessante da fase. O Gemini é um modelo **multimodal**,
ou seja, aceita texto e imagem no mesmo pedido. Enviamos os bytes da imagem junto com uma
instrução, e ele descreve o que está vendo:

```python
with open(caminho_imagem, "rb") as f:
    dados_imagem = f.read()

resposta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        genai_types.Part.from_bytes(data=dados_imagem, mime_type="image/png"),
        "Descreva objetivamente o que a imagem mostra, em especial qualquer "
        "mensagem de erro, código ou tela de problema...",
    ],
)
```

O prompt pede explicitamente que o modelo **não invente** nada que não esteja visível na
imagem — pelo mesmo motivo das outras fases: evitar alucinação.

Para testar, o projeto inclui um print fictício em `exemplos/erro_pagamento.png`,
simulando uma tela de checkout com o erro "PAY-4012 — não foi possível confirmar a
transação via Pix".

Também tratamos os erros possíveis: formato de arquivo não suportado (aceita apenas PNG,
JPG e WEBP), imagem acima de 8 MB e falha na análise.

## 5. A decisão automática de abrir chamado

Esta é a parte mais importante do ponto de vista de projeto. A decisão é feita por
**regras no código** (`servicos/pedidos.py`), avaliadas nesta ordem:

| # | Situação | Abre chamado? |
|---|---|---|
| 0 | Número informado mas **não encontrado** | ❌ Não — pede para conferir o número |
| 1 | Prioridade **crítica** (cancelamento/reembolso) | ✅ Sim |
| 2 | Pagamento **pendente** ou **recusado** | ✅ Sim |
| 3 | Entrega **atrasada** ou produto **com avaria** | ✅ Sim |
| 4 | Prioridade **alta** | ✅ Sim |
| 5 | Demais casos (dúvida simples) | ❌ Não |

A regra 0 merece destaque: se o cliente informou um número que não existe, **não faz
sentido abrir um chamado** sobre um pedido inexistente. O certo é pedir que ele confira o
número. Esse detalhe mostra que a decisão foi pensada, e não apenas "abre se for urgente".

Quando um chamado é aberto, o sistema gera um número fictício no formato `CH-1001`
(baseado no pedido) e informa esse número ao cliente na resposta.

## 6. A resposta final

Por fim, o sistema envia ao Gemini **todo o contexto reunido** — categoria, prioridade,
orientação base, dados reais do pedido, a análise da imagem e a situação do chamado — e
pede uma resposta cordial em passos numerados.

O resultado é uma resposta personalizada, que cita o produto e o status reais do pedido,
menciona o que apareceu na imagem e informa o número do chamado quando houver.

Exemplo de saída (formato do enunciado, com campos extras):

```json
{
  "categoria": "pagamento",
  "prioridade": "alta",
  "dados_pedido": { "encontrado": true, "dados": { "cliente": "João Silva", "...": "..." } },
  "analise_imagem": "A imagem mostra uma tela de checkout com o erro PAY-4012...",
  "chamado": {
    "aberto": true,
    "numero_chamado": "CH-1001",
    "motivo": "Pagamento pendente: cliente não consegue concluir a compra."
  },
  "resposta_cliente": "1. Olá, João! Verifiquei o seu pedido 1001...",
  "usou_llm": true
}
```

## 7. Tratamento de erros e fallback

O sistema continua funcionando mesmo quando algo dá errado:

- **Pedido não encontrado** → responde pedindo que o cliente confira o número, sem abrir chamado.
- **Imagem inválida ou grande demais** → retorna uma mensagem de erro clara.
- **LLM fora do ar ou sem chave** → cai no fallback: monta a resposta com a orientação
  base da Fase 1 **somada aos dados reais do pedido** e à situação do chamado. O cliente
  recebe uma resposta útil mesmo sem a IA generativa.

## 8. Reflexão: por que a IA não decide sozinha?

Abrir um chamado é uma **ação concreta no negócio**: gera trabalho para a equipe, cria
expectativa no cliente e precisa ser auditável. Uma regra em código (`if prioridade ==
"critica"...`) sempre faz a mesma coisa, pode ser testada e é fácil de justificar para a
empresa. Uma LLM pode variar de uma execução para outra.

Por isso a divisão: **a IA entende e escreve; o código decide**. A LLM melhora muito a
experiência do cliente, mas não assume responsabilidade por decisões de negócio.

Vale acrescentar que, mesmo com tudo automatizado, os casos sensíveis (pagamento,
cancelamento, avaria) são justamente os que **geram chamado para um humano** — ou seja, o
sistema sabe reconhecer quando não deve resolver sozinho.

## 9. Conclusão

A Fase 3 fecha o projeto unindo as três tecnologias: **Machine Learning** para entender a
dúvida, **LLM multimodal** para ler a imagem e escrever a resposta, e **regras de negócio**
para decidir o que fazer. O resultado é um atendimento que consulta dados reais, entende
um print de erro e sabe quando escalar para um atendente — tudo com controle e sem
depender da IA para tomar decisões.

Como melhorias futuras, seria possível: ligar o sistema a um banco de dados real em vez do
JSON fictício, aumentar a base de treino para elevar a acurácia da Fase 1, registrar
histórico de atendimentos e criar um painel para a equipe acompanhar os chamados abertos.
