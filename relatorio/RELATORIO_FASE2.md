# Relatório — Fase 2: Geração de resposta passo a passo com LLM

> Material-base para o seu relatório/apresentação. Reescreva com suas palavras.

## 1. Objetivo da fase

Na Fase 1, o sistema já identifica a **categoria**, a **prioridade** e uma **resposta
base** da dúvida do cliente. O problema é que a resposta base é um texto fixo, sempre
igual. O objetivo da Fase 2 é usar uma **LLM (modelo de linguagem)** para transformar
esse contexto em uma resposta mais **humana, cordial e em passos numerados**, adaptada à
mensagem do cliente.

## 2. Qual LLM foi usada e por quê

Escolhemos o **Google Gemini** (modelo `gemini-2.5-flash`). Motivos práticos:

1. A API do Gemini tem **camada gratuita** (com limite de requisições), o que é adequado
   para um projeto de estudo e dispensa cadastro de pagamento. (Havíamos começado com o
   DeepSeek, mas ele exige pagamento para uso da API.)
2. Usamos o **SDK oficial** (`google-genai`), com uma interface simples: um prompt de
   sistema (`system_instruction`) separado do conteúdo do usuário.
3. O modelo é configurável pela variável `GEMINI_MODEL` no `.env`, então dá para trocar
   de versão sem alterar o código.

Trecho central da integração (`servicos/llm.py`):

```python
from google import genai
from google.genai import types

cliente = genai.Client(api_key=GEMINI_API_KEY)

resposta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents=conteudo_usuario,
    config=types.GenerateContentConfig(
        system_instruction=INSTRUCAO_SISTEMA,
        temperature=0.4,
    ),
)
texto = resposta.text
```

## 3. Como o sistema funciona na Fase 2

O endpoint `POST /atender` faz duas etapas:

1. **Classifica** a mensagem (reaproveita a Fase 1): obtém categoria, prioridade e
   resposta base.
2. **Gera a resposta** com o Gemini, enviando esse contexto. A LLM devolve um texto
   cordial, em passos numerados.

Ou seja: o **Machine Learning entende** a dúvida e a **LLM escreve** a resposta. Cada um
faz o que faz de melhor.

## 4. Como controlamos o que a LLM responde

Esse é o ponto mais importante da fase. Uma LLM "solta" pode inventar informação ou
prometer coisas que a empresa não cumpre. Para evitar isso, usamos várias camadas de
controle:

- **Prompt de sistema (regras fixas):** definimos que ela deve falar em português, com
  tom cordial, responder em passos e — principalmente — **nunca prometer** prazos,
  reembolsos ou descontos que não estejam no contexto. Se faltar informação, ela deve
  orientar o cliente a procurar um atendente humano.
- **Contexto controlado:** enviamos à LLM apenas o que o sistema já sabe (categoria,
  prioridade, resposta base). Ela não busca dados por conta própria nem toma decisões.
- **`temperature=0.4`:** um valor baixo deixa as respostas mais previsíveis e menos
  "criativas".
- **Fallback:** se a LLM falhar (erro de rede, chave inválida, API fora do ar), o sistema
  devolve a resposta base da Fase 1. O atendimento nunca fica sem resposta.

## 5. Exemplo de resultado

Entrada:
```json
{ "mensagem": "Paguei via Pix mas meu pedido continua aguardando pagamento" }
```

A Fase 1 classifica como `categoria=pagamento`, `prioridade=alta`. A Fase 2 (Gemini)
gera algo como:

```
1. Olá! Entendo a sua preocupação com o pagamento, vou te ajudar.
2. Pagamentos via Pix costumam ser confirmados em alguns minutos; às vezes há um pequeno atraso.
3. Verifique na sua conta, em "Meus Pedidos", se o status já mudou para "pago".
4. Se depois de alguns minutos continuar como "aguardando pagamento", responda esta
   mensagem que um atendente vai verificar o seu caso.
```

Repare que a resposta é cordial e em passos, mas **não promete** prazo exato nem
confirma o pagamento — exatamente como as regras pedem.

> No relatório, inclua um print da resposta real gerada na sua máquina (pode variar a cada
> execução, pois a LLM reescreve o texto).

## 6. Segurança da chave de API

A chave do Gemini fica **apenas** no arquivo `.env`, que é ignorado pelo Git
(`.gitignore`). Ela nunca aparece no código. Se a chave vazar, basta gerar uma nova no
Google AI Studio (https://aistudio.google.com/apikey) e apagar a antiga.

## 7. Perguntas de reflexão (Fase 2)

**A LLM deve decidir sozinha?**
Não. No nosso sistema, a LLM recebe o contexto e apenas redige a resposta. Quem classifica
é o Machine Learning e quem define as regras é o código. A LLM não busca dados, não
consulta pedidos e não decide ações — isso evita erros e respostas imprevisíveis.

**Uma resposta automática pode prometer algo que a empresa não cumpre?**
Não, e esse é o maior risco de usar LLM em atendimento. Por isso o prompt de sistema
proíbe explicitamente promessas de prazo, reembolso ou desconto fora do contexto.

**Qual a diferença entre a Fase 1 e a Fase 2?**
A Fase 1 **classifica** (escolhe um rótulo entre categorias fixas) — é determinística e
rápida. A Fase 2 **gera texto** (produz uma resposta nova em linguagem natural) — é mais
flexível, porém precisa de controle. As duas se complementam.

## 8. Conclusão

A Fase 2 adiciona a camada de linguagem natural ao HelpDesk: o sistema deixa de responder
com um texto fixo e passa a conversar de forma mais humana, sem abrir mão do controle. A
combinação "ML classifica + LLM redige + regras no código" é segura e escalável, e serve
de base para a Fase 3, que vai acrescentar a análise de imagem e a consulta de pedidos.
