# HelpDesk Inteligente para Sistema de Vendas Online

Projeto completo de atendimento automático para uma loja online, em **3 fases**:

- **Fase 1 — Classificação com Machine Learning** (TF-IDF + Naive Bayes): identifica a
  categoria da dúvida, a prioridade e uma resposta base.
- **Fase 2 — Resposta passo a passo com LLM** (Google Gemini): gera uma resposta
  cordial e humanizada a partir do contexto da Fase 1.
- **Fase 3 — Atendimento avançado**: recebe também o **número do pedido** e uma
  **imagem** (print do erro), consulta o pedido, analisa a imagem, **decide
  automaticamente se abre um chamado** e gera a resposta final.

**LLM usada:** Google Gemini (`gemini-2.5-flash`) — tem nível gratuito e é
**multimodal**, ou seja, aceita texto e imagem no mesmo pedido, o que é essencial
para a Fase 3.

---

## 1. Como rodar

```bash
# 1. Entrar na pasta
cd helpdesk_fase3

# 2. (recomendado) ambiente virtual
python -m venv venv
# Windows:   venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Gerar a base e treinar o modelo (Fase 1)
python dados/gerar_base.py
python modelo/treinar.py

# 5. Colocar a chave do Gemini no arquivo .env
#    Abra o .env e cole sua chave em GEMINI_API_KEY=
#    Crie a chave gratuita em: https://aistudio.google.com/apikey

# 6. (opcional) Testar só a LLM, inclusive a leitura da imagem
python -m servicos.llm

# 7. Rodar a API
python app.py
# depois abra http://localhost:5000
```

> **Sem a chave o sistema ainda funciona** em "modo fallback": ele usa as respostas
> base da Fase 1 e avisa que não conseguiu analisar a imagem. Isso garante que o
> atendimento nunca fica mudo se a LLM falhar.

---

## 2. Estrutura do projeto

```
helpdesk_fase3/
├── app.py                      # API Flask com as 3 fases
├── .env                        # SUA CHAVE do Gemini (não versionar)
├── .env.example                # modelo de configuração
├── requirements.txt
├── dados/
│   ├── gerar_base.py           # gera a base fictícia de chamados
│   ├── chamados.csv            # base gerada (mensagem, categoria, prioridade)
│   ├── respostas.py            # respostas base por categoria
│   └── pedidos.json            # banco fake de pedidos (Fase 3)
├── modelo/
│   ├── treinar.py              # treino (Pipeline TF-IDF + Naive Bayes) + métricas
│   └── modelo_categoria.pkl    # modelo salvo
├── servicos/
│   ├── classificador.py        # Fase 1
│   ├── llm.py                  # Fases 2 e 3: Gemini (texto + imagem) + fallback
│   └── pedidos.py              # Fase 3: consulta pedido + regras de decisão
├── templates/
│   └── index.html              # página web de teste (3 abas)
├── exemplos/
│   └── erro_pagamento.png      # print de erro fictício para testar a Fase 3
├── uploads/                    # imagens recebidas
└── relatorio/
    ├── RELATORIO_FASE1.md
    ├── RELATORIO_FASE2.md
    ├── RELATORIO_FASE3.md
    ├── metricas.txt
    └── matriz_confusao.png
```

---

## 3. Endpoints

### `POST /classificar` — Fase 1
Entrada: `{ "mensagem": "..." }`
Saída: `categoria`, `prioridade`, `confianca`, `resposta_base`.

### `POST /atender` — Fase 2
Entrada: `{ "mensagem": "..." }`
Saída: `categoria`, `prioridade`, `resposta_cliente` (texto da LLM), `usou_llm`.

### `POST /atender-completo` — Fase 3
Entrada (formulário / `multipart/form-data`):
- `mensagem` (texto)
- `numero_pedido` (ex.: `1001`)
- `imagem` (arquivo PNG/JPG/WEBP, opcional, até 8 MB)

Saída:
```json
{
  "categoria": "pagamento",
  "prioridade": "alta",
  "dados_pedido": { "informado": true, "encontrado": true, "dados": { "...": "..." } },
  "analise_imagem": "A imagem mostra uma tela de checkout com erro PAY-4012...",
  "chamado": {
    "aberto": true,
    "numero_chamado": "CH-1001",
    "motivo": "Pagamento pendente: cliente não consegue concluir a compra."
  },
  "resposta_cliente": "1. Olá! Verifiquei o seu pedido 1001...",
  "usou_llm": true
}
```

Teste pelo terminal:
```bash
curl -X POST localhost:5000/atender-completo \
  -F "mensagem=Paguei via Pix mas continua aguardando pagamento" \
  -F "numero_pedido=1001" \
  -F "imagem=@exemplos/erro_pagamento.png"
```

---

## 4. Pedidos de teste (banco fake)

| Pedido | Situação |
|---|---|
| 1001 | Pagamento **pendente** (Pix) |
| 1002 | Pago, em separação |
| 1003 | Enviado, em transporte |
| 1004 | Entregue |
| 1005 | Entrega **atrasada** |
| 1006 | Cancelado / estornado |
| 1007 | Pagamento **recusado** |
| 1008 | Entregue **com avaria** |

---

## 5. Regras de abertura de chamado (Fase 3)

A decisão é feita **pelo código**, não pela IA, nesta ordem:

| # | Situação | Abre chamado? |
|---|---|---|
| 0 | Número de pedido informado mas **não encontrado** | ❌ Não — pede para conferir o número |
| 1 | Prioridade **crítica** (cancelamento/reembolso) | ✅ Sim |
| 2 | Pagamento **pendente** ou **recusado** | ✅ Sim |
| 3 | Entrega **atrasada** ou produto **com avaria** | ✅ Sim |
| 4 | Prioridade **alta** | ✅ Sim |
| 5 | Demais casos (dúvida simples) | ❌ Não |

---

## 6. Decisões de projeto (importante para a apresentação)

- **Por que a prioridade não é um segundo modelo de ML?**
  Nesta base, a prioridade depende da categoria (pagamento = alta, cancelamento =
  crítica). Treinar um classificador de texto só para prioridade daria resultado
  instável e sem ganho. Então ela é **derivada da categoria por regra**.

- **Quem decide abrir o chamado?**
  O **sistema**, por regras explícitas (`servicos/pedidos.py`). A IA generativa
  escreve a resposta; a decisão de negócio fica no código, previsível e auditável.

- **Como a resposta da LLM é controlada?**
  Por um *system prompt* rígido em `servicos/llm.py`: tom cordial, resposta em passos
  e **proibição de prometer** prazos, reembolsos ou descontos fora do contexto.

- **Fallback:** se a LLM falhar ou não houver chave, o sistema devolve a resposta base
  da Fase 1 somada aos dados reais do pedido. O atendimento nunca fica sem resposta.

---

## 7. Segurança da chave

- A chave do Gemini fica **só no arquivo `.env`**, nunca no código. O `.gitignore` já
  ignora o `.env`, então ele **não vai para o GitHub**.
- Se a chave vazar, gere uma nova em https://aistudio.google.com/apikey e apague a antiga.

---

## 8. Observações

- A acurácia do classificador fica em torno de **71%** com a base atual (152 frases).
  Para melhorar, adicione mais frases variadas em `dados/gerar_base.py` e treine de novo.
- A imagem `exemplos/erro_pagamento.png` é um print **fictício**, criado só para teste.
