# HelpDesk Inteligente — Fase 1 (Classificação com Machine Learning)

Primeira entrega do projeto de HelpDesk Inteligente para uma loja online.

Nesta fase, o sistema recebe a **mensagem de um cliente** e usa **Machine Learning**
para identificar:
- a **categoria** da dúvida (login, pagamento, entrega, cancelamento...),
- a **prioridade** do atendimento,
- e uma **resposta base** adequada.

> As Fases 2 (resposta com LLM) e 3 (imagem + pedido) serão entregues depois e
> **não** fazem parte deste pacote.

**Algoritmo:** `TfidfVectorizer` (transforma texto em números) + `MultinomialNB`
(Naive Bayes), montados em um `Pipeline` do scikit-learn.

---

## Como rodar

```bash
# 1. Clonar o repositório e entrar na pasta
git clone https://github.com/kai426/HelpDesk_Inteligente_Vendas_Online.git
cd HelpDesk_Inteligente_Vendas_Online

# 2. (recomendado) ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Gerar a base de dados fictícia
python dados/gerar_base.py

# 5. Treinar o modelo (gera o .pkl, as métricas e a matriz de confusão)
python modelo/treinar.py

# 6. (opção A) Testar direto no terminal
python -m servicos.classificador

# 6. (opção B) Rodar a API web
python app.py
# depois abra http://localhost:5000
```

---

## Estrutura

```
HelpDesk_Inteligente_Vendas_Online/
├── app.py                      # API Flask com o endpoint /classificar
├── requirements.txt
├── dados/
│   ├── gerar_base.py           # gera a base fictícia de chamados
│   ├── chamados.csv            # base gerada (mensagem, categoria, prioridade)
│   └── respostas.py            # respostas base por categoria
├── modelo/
│   ├── treinar.py              # treino (Pipeline TF-IDF + Naive Bayes) + métricas
│   └── modelo_categoria.pkl    # modelo salvo (gerado pelo treino)
├── servicos/
│   └── classificador.py        # carrega o modelo e classifica a mensagem
├── templates/
│   └── index.html              # página web de teste
└── relatorio/
    ├── metricas.txt            # acurácia e relatório por classe
    └── matriz_confusao.png     # imagem da matriz de confusão (para o relatório)
```

---

## Endpoint `POST /classificar`

Entrada (JSON):
```json
{ "mensagem": "Paguei via Pix mas meu pedido continua aguardando pagamento" }
```

Saída (JSON):
```json
{
  "categoria": "pagamento",
  "prioridade": "alta",
  "confianca": 0.30,
  "resposta_base": "Verifique o status do pagamento na sua conta..."
}
```

Teste pelo terminal:
```bash
curl -X POST localhost:5000/classificar -H "Content-Type: application/json" \
  -d '{"mensagem":"Meu pedido está atrasado"}'
```

---

## A base de dados

- **152 chamados fictícios**, divididos em **10 categorias** (cada uma com ~15 frases).
- As frases foram escritas de formas variadas — formais, informais, com gírias e com
  erros de digitação — de propósito, porque uma base mais variada ajuda o modelo a
  generalizar melhor para mensagens reais.
- Colunas: `mensagem`, `categoria`, `prioridade`.

Categorias: `login`, `cadastro`, `produto`, `estoque`, `carrinho`, `pagamento`,
`cupom`, `pedido`, `entrega`, `cancelamento`.

---

## Resultados

- **Acurácia no teste: ~71%** (com uma base pequena de 152 frases).
- Métricas completas por classe: `relatorio/metricas.txt`.
- Matriz de confusão: `relatorio/matriz_confusao.png`.

Para melhorar a acurácia, basta adicionar mais frases variadas em
`dados/gerar_base.py` e treinar de novo — o modelo aprende melhor com mais exemplos.

---

## Observação sobre a prioridade

A **categoria** é prevista pelo Machine Learning. Já a **prioridade** é definida por
uma regra a partir da categoria (ex.: `pagamento` = alta, `cancelamento` = crítica),
porque nesta base a prioridade depende diretamente da categoria. Treinar um segundo
modelo de texto só para prioridade daria um resultado instável e sem ganho real.
Essa decisão está explicada no relatório.
