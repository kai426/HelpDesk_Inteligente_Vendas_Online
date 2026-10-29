# Relatório — Fase 1: Classificação da dúvida com Machine Learning

> Material-base para o seu relatório/apresentação. Reescreva com suas palavras.

## 1. Objetivo da fase

Construir a primeira parte do HelpDesk Inteligente: um sistema que recebe a mensagem
de um cliente de uma loja online e, usando Machine Learning, identifica a **categoria**
da dúvida, define a **prioridade** do atendimento e sugere uma **resposta base**.

## 2. A base de dados

Como não temos chamados reais, criamos uma base **fictícia** com 152 mensagens,
distribuídas em 10 categorias (~15 frases cada):

`login`, `cadastro`, `produto`, `estoque`, `carrinho`, `pagamento`, `cupom`,
`pedido`, `entrega`, `cancelamento`.

As frases foram escritas de propósito de formas diferentes: formais, informais, com
gírias e com erros de digitação (ex.: "nao consigo logar", "paguei via pix e nao
reconheceu"). Isso é importante porque, no mundo real, os clientes escrevem de jeitos
muito variados — uma base diversa faz o modelo acertar mais em mensagens novas.

A base fica no arquivo `dados/chamados.csv`, com as colunas `mensagem`, `categoria` e
`prioridade`. Ela é gerada pelo script `dados/gerar_base.py`.

## 3. O modelo de Machine Learning

Usamos um `Pipeline` do scikit-learn com duas etapas:

1. **TfidfVectorizer** — transforma o texto em números. Ele dá mais peso às palavras
   que são características de cada categoria (ex.: "pix", "boleto", "rastreio"). Usamos
   `ngram_range=(1,2)` para o modelo olhar também pares de palavras, como
   "aguardando pagamento".
2. **MultinomialNB (Naive Bayes)** — algoritmo de classificação que, a partir desses
   números, escolhe a categoria mais provável. É simples, rápido e funciona bem com texto.

Dividimos a base em **80% treino / 20% teste** (`train_test_split`, com `stratify`
para manter a proporção das categorias). Treinamos no conjunto de treino e medimos a
acurácia no conjunto de teste, que o modelo nunca viu — assim a avaliação é honesta.

Por fim, o modelo é re-treinado com 100% da base e salvo em
`modelo/modelo_categoria.pkl` (com `joblib`), para a API carregar sem treinar toda vez.

## 4. Resultados

- **Acurácia no conjunto de teste: ~71%**.
- O relatório por classe (precisão, recall e f1) está em `relatorio/metricas.txt`.
- A **matriz de confusão** está em `relatorio/matriz_confusao.png` — ela mostra onde o
  modelo acerta (diagonal) e onde confunde categorias parecidas.

Para uma base pequena (152 frases) e 10 categorias, é um resultado coerente. As maiores
confusões acontecem entre categorias com vocabulário parecido (por exemplo, "pedido" e
"entrega", ou "estoque" e "produto"). O caminho para melhorar é simples: adicionar mais
frases variadas por categoria e treinar novamente.

## 5. Sobre a prioridade

A **categoria** é prevista pelo Machine Learning. A **prioridade** (baixa, média, alta,
crítica) é definida por uma regra a partir da categoria — por exemplo, `pagamento` é
sempre "alta" e `cancelamento` é sempre "crítica".

Optamos por isso porque, nesta base, a prioridade depende diretamente da categoria.
Treinar um segundo classificador de texto só para prever a prioridade daria um resultado
instável e sem ganho real, já que a informação já está na categoria. Dessa forma, a
decisão fica previsível e fácil de explicar.

## 6. Como testar

- **Terminal:** `python -m servicos.classificador` (classifica várias frases de exemplo).
- **API web:** `python app.py` e acesse `http://localhost:5000`, ou chame
  `POST /classificar` com `{"mensagem": "..."}`.

## 7. Perguntas de reflexão (Fase 1)

**Uma resposta automática precisa parecer humana?**
Precisa ser clara e acolhedora, mas não precisa fingir ser uma pessoa. O melhor é um tom
cordial, deixando claro que é um atendimento automático e que existe a opção de falar com
um atendente.

**Qual a diferença entre classificar e gerar texto?**
Classificar (esta fase) é escolher um rótulo dentro de um conjunto fixo de categorias —
é Machine Learning tradicional, rápido e previsível. Gerar texto (fase seguinte) é produzir
uma resposta nova em linguagem natural, o que exige uma LLM e mais controle. Nesta fase o
foco é classificar corretamente.

**Toda resposta automática deve ser aceita sem revisão?**
Não. Em casos sensíveis (pagamento, cancelamento), o ideal é tratar com mais atenção —
por isso esses casos recebem prioridade alta ou crítica, para serem acompanhados de perto.

## 8. Conclusão

A Fase 1 entrega um classificador funcional que identifica a categoria da dúvida, define a
prioridade e sugere uma resposta base, tudo acessível por uma API. A acurácia de ~71% é um
bom ponto de partida e pode crescer com mais dados. Esta base servirá de fundação para a
Fase 2 (resposta humanizada com LLM) e a Fase 3 (imagem + consulta de pedido).
