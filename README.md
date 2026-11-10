# HelpDesk Inteligente — Fases 1 e 2

Segunda entrega do projeto de HelpDesk Inteligente para uma loja online.

- **Fase 1 — Classificação com Machine Learning** (TF-IDF + Naive Bayes): identifica a
  categoria da dúvida, a prioridade e uma resposta base.
- **Fase 2 — Resposta passo a passo com LLM** (Google Gemini): pega o resultado da Fase 1 e
  gera uma resposta cordial e humanizada, em passos numerados.

> A Fase 3 (imagem + consulta de pedido) será entregue depois e **não** faz parte deste pacote.

**LLM escolhida:** Google Gemini (`gemini-2.5-flash`), usado através do SDK oficial
**`google-genai`**. A API do Gemini tem **camada gratuita**, o que atende bem a um projeto
de estudo. O modelo pode ser trocado pela variável `GEMINI_MODEL` no `.env`.

---

## Como rodar

```bash
# 1. Entrar na pasta
cd helpdesk_fase2

# 2. (recomendado) ambiente virtual
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/Mac:  source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Gerar a base e treinar o modelo (Fase 1)
python dados/gerar_base.py
python modelo/treinar.py

# 5. Configurar a chave do Gemini (Fase 2)
#    Gere uma chave gratuita em https://aistudio.google.com/apikey, copie o modelo
#    de configuração e cole a chave em GEMINI_API_KEY:
#      cp .env.example .env        (no Windows: copy .env.example .env)

# 6. (opcional) Testar só a LLM
python -m servicos.llm

# 7. Rodar a API
python app.py
# depois abra http://localhost:5000
```

> **Sem a chave (ou sem o pacote `google-genai`), o sistema ainda funciona** em "modo fallback":
> o `/atender` devolve a resposta base da Fase 1. Isso garante que o atendimento nunca
> fica mudo se a LLM falhar.

---

## ⚠️ Segurança da chave

- A chave do Gemini fica **só no arquivo `.env`**, nunca no código. O `.gitignore` já
  ignora o `.env`, então ele **não vai para o GitHub**.
- **Não compartilhe** o `.env` nem publique a chave. Se ela vazar, gere uma nova em
  https://aistudio.google.com/apikey e apague a antiga.

---

## Endpoints

### `POST /classificar` — Fase 1
Entrada: `{ "mensagem": "..." }`
Saída: `categoria`, `prioridade`, `confianca`, `resposta_base`.

### `POST /atender` — Fase 2
Entrada: `{ "mensagem": "Meu cupom não funciona na hora de pagar" }`
Saída:
```json
{
  "categoria": "cupom",
  "prioridade": "baixa",
  "resposta_base": "Confira se o cupom...",
  "resposta_cliente": "1. Olá! Vamos resolver isso juntos...\n2. ...",
  "usou_llm": true
}
```
- `resposta_cliente` é o texto gerado pela LLM (passo a passo).
- `usou_llm` indica se a resposta veio do Gemini (`true`) ou do fallback (`false`).

Teste pelo terminal:
```bash
curl -X POST localhost:5000/atender -H "Content-Type: application/json" \
  -d '{"mensagem":"Meu pedido está atrasado"}'
```

---

## Estrutura (novidades da Fase 2 em destaque)

```
helpdesk_fase2/
├── app.py                      # agora com /classificar (F1) e /atender (F2)
├── .env                        # chave do Gemini (NÃO versionar)
├── .env.example                # modelo de configuração
├── requirements.txt            # + google-genai, python-dotenv
├── dados/ ...                  # base e respostas (Fase 1)
├── modelo/ ...                 # treino e modelo .pkl (Fase 1)
├── servicos/
│   ├── classificador.py        # Fase 1
│   └── llm.py                  # >>> NOVO: integração com Gemini + fallback
├── templates/
│   └── index.html              # agora com abas Fase 1 e Fase 2
└── relatorio/
    ├── RELATORIO_FASE1.md
    └── RELATORIO_FASE2.md      # >>> NOVO
```

---

## Como a resposta da LLM é controlada (importante p/ apresentação)

- **Prompt de sistema rígido** (`servicos/llm.py`): tom cordial, resposta em passos, e
  **proibição** de prometer prazo, reembolso ou desconto fora do contexto.
- A LLM recebe **apenas o contexto confiável** da Fase 1 (categoria, prioridade, resposta
  base). Ela **não decide** nada — só redige melhor.
- `temperature=0.4` para respostas mais previsíveis.
- **Fallback**: se a LLM falhar, devolve a resposta base da Fase 1.
