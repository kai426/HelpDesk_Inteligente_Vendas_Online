"""
FASES 2 e 3 — Serviço de LLM com Google Gemini.

Funções:
  - gerar_resposta(...)        -> FASE 2: resposta humanizada, passo a passo.
  - analisar_imagem(...)       -> FASE 3: descreve o erro visível numa imagem (multimodal).
  - gerar_resposta_final(...)  -> FASE 3: resposta final juntando todo o contexto.

Por que Gemini?
  Tem nível gratuito no Google AI Studio e é MULTIMODAL (aceita texto e imagem no
  mesmo pedido), o que é essencial para a Fase 3 analisar o print enviado pelo cliente.

Controle da resposta (responde às dicas do enunciado):
  - A chave fica no arquivo .env (NUNCA no código).
  - Um "prompt de sistema" rígido define tom cordial, resposta em passos e
    PROÍBE prometer prazo, reembolso ou desconto fora do contexto.
  - Enviamos à LLM apenas o contexto confiável; ela NÃO decide nada.
  - Se a LLM falhar ou não houver chave, caímos no FALLBACK, para o atendimento
    nunca ficar mudo.

SDK: google-genai  (pip install google-genai)
Modelo padrão: gemini-2.5-flash (gratuito e multimodal).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Regras fixas que a LLM deve sempre seguir.
INSTRUCAO_SISTEMA = (
    "Você é um atendente de suporte de uma loja virtual brasileira. "
    "Fale em português do Brasil, com tom cordial, claro e humano. "
    "Responda SEMPRE em passos numerados, curtos e práticos. "
    "Use apenas as informações do contexto fornecido. "
    "NUNCA prometa prazos, reembolsos, descontos ou resultados que não estejam "
    "explicitamente no contexto. "
    "Se faltar informação ou houver dúvida, oriente o cliente a falar com um "
    "atendente humano. "
    "Não invente número de pedido, valor ou status."
)

# Importa o SDK. Se não estiver instalado, o sistema ainda roda em modo fallback.
try:
    from google import genai
    from google.genai import types as genai_types
    _SDK_OK = True
except Exception:
    _SDK_OK = False

_cliente = None


def _get_cliente():
    """Cria (uma vez) o cliente Gemini. Retorna None se não for possível."""
    global _cliente
    if not _SDK_OK or not GEMINI_API_KEY:
        return None
    if _cliente is None:
        _cliente = genai.Client(api_key=GEMINI_API_KEY)
    return _cliente


def llm_disponivel() -> bool:
    """True se há SDK instalado E chave configurada."""
    return _get_cliente() is not None


def _config():
    """Configuração padrão das chamadas (regras + temperatura baixa)."""
    return genai_types.GenerateContentConfig(
        system_instruction=INSTRUCAO_SISTEMA,
        temperature=0.4,
    )


# ---------------------------------------------------------------------------
# FASE 2 — resposta humanizada a partir do resultado do classificador
# ---------------------------------------------------------------------------
def gerar_resposta(mensagem: str, categoria: str, prioridade: str, resposta_base: str) -> str:
    """Gera uma resposta amigável, passo a passo, usando o contexto da Fase 1.

    Se a LLM não estiver disponível ou falhar, retorna a resposta_base (fallback).
    """
    cliente = _get_cliente()
    if cliente is None:
        return resposta_base  # fallback

    prompt = (
        f"Dúvida do cliente: {mensagem}\n\n"
        f"Contexto identificado pelo sistema (fonte de verdade — use só isto):\n"
        f"- Categoria: {categoria}\n"
        f"- Prioridade: {prioridade}\n"
        f"- Orientação base: {resposta_base}\n\n"
        f"Escreva uma resposta cordial ao cliente, em passos numerados, baseada na "
        f"orientação base acima. Finalize oferecendo ajuda de um atendente humano se "
        f"o problema continuar."
    )

    try:
        resposta = cliente.models.generate_content(
            model=GEMINI_MODEL, contents=prompt, config=_config()
        )
        texto = (resposta.text or "").strip()
        return texto if texto else resposta_base
    except Exception as e:
        print(f"[LLM] Falha ao gerar resposta, usando fallback: {e}")
        return resposta_base


# ---------------------------------------------------------------------------
# FASE 3 — análise de imagem (multimodal)
# ---------------------------------------------------------------------------
def analisar_imagem(caminho_imagem: str, mensagem_cliente: str = "") -> str:
    """Descreve o que aparece na imagem enviada pelo cliente (ex.: print de erro).

    É aqui que entra a parte MULTIMODAL: enviamos os bytes da imagem junto com um
    texto, no mesmo pedido, e o Gemini "lê" a imagem.

    Retorna um texto curto. Se não houver LLM ou falhar, retorna um aviso neutro.
    """
    cliente = _get_cliente()
    if cliente is None:
        return "Não foi possível analisar a imagem automaticamente (LLM indisponível)."

    if not os.path.exists(caminho_imagem):
        return "Imagem não encontrada para análise."

    # Descobre o tipo da imagem pela extensão do arquivo.
    ext = os.path.splitext(caminho_imagem)[1].lower()
    mimes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mimes.get(ext, "image/jpeg")

    try:
        with open(caminho_imagem, "rb") as f:
            dados_imagem = f.read()

        prompt = (
            "A imagem a seguir foi enviada por um cliente de uma loja online. "
            f"O cliente disse: '{mensagem_cliente}'. "
            "Descreva objetivamente o que a imagem mostra, em especial qualquer "
            "mensagem de erro, código ou tela de problema. Responda em 1 a 3 frases, "
            "sem inventar nada que não esteja visível."
        )

        resposta = cliente.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                genai_types.Part.from_bytes(data=dados_imagem, mime_type=mime),
                prompt,
            ],
        )
        texto = (resposta.text or "").strip()
        return texto if texto else "A imagem foi recebida, mas não foi possível descrevê-la."
    except Exception as e:
        print(f"[LLM] Falha ao analisar imagem: {e}")
        return "A imagem foi recebida, mas houve um erro ao analisá-la automaticamente."


# ---------------------------------------------------------------------------
# FASE 3 — resposta final juntando todo o contexto
# ---------------------------------------------------------------------------
def gerar_resposta_final(mensagem, categoria, prioridade, resposta_base,
                         pedido, decisao, analise_imagem=None) -> str:
    """Gera a resposta final da Fase 3, com todo o contexto reunido.

    pedido  -> dicionário devolvido por consultar_pedido()
    decisao -> dicionário devolvido por decidir_abertura_chamado()
    """
    cliente = _get_cliente()

    # Monta um resumo do pedido em texto.
    if pedido.get("encontrado"):
        d = pedido["dados"]
        resumo_pedido = (
            f"Pedido {d.get('numero_pedido')} - cliente {d.get('cliente')}, "
            f"produto {d.get('produto')}, status do pedido {d.get('status_pedido')}, "
            f"pagamento {d.get('status_pagamento')} ({d.get('metodo_pagamento')}), "
            f"entrega {d.get('status_entrega')}."
        )
    else:
        resumo_pedido = "Pedido não encontrado na base."

    if decisao.get("abrir"):
        info_chamado = (
            f"Um chamado foi aberto (nº {decisao.get('numero_chamado')}). "
            f"Motivo: {decisao.get('motivo')}"
        )
    else:
        info_chamado = "Nenhum chamado foi aberto; o caso pode ser resolvido com orientação."

    # Fallback sem LLM: resposta montada com os dados que já temos.
    if cliente is None:
        partes = [resposta_base]
        if pedido.get("encontrado"):
            partes.append(f"Sobre o seu pedido: {resumo_pedido}")
        else:
            partes.append("Não localizamos esse número de pedido. Confira o número e tente novamente.")
        if analise_imagem:
            partes.append(f"Sobre a imagem enviada: {analise_imagem}")
        partes.append(info_chamado)
        return "\n".join(partes)

    prompt = (
        f"Dúvida do cliente: {mensagem}\n\n"
        f"Contexto reunido pelo sistema (fonte de verdade — use só isto):\n"
        f"- Categoria: {categoria}\n"
        f"- Prioridade: {prioridade}\n"
        f"- Orientação base: {resposta_base}\n"
        f"- Dados do pedido: {resumo_pedido}\n"
        f"- Análise da imagem enviada: {analise_imagem or 'nenhuma imagem enviada'}\n"
        f"- Situação do chamado: {info_chamado}\n\n"
        f"Escreva a resposta final ao cliente, cordial e em passos numerados. "
        f"Mencione os dados reais do pedido quando ajudarem. "
        f"Se um chamado foi aberto, informe o número ao cliente. "
        f"Se o pedido não foi encontrado, peça gentilmente que confira o número. "
        f"Não prometa prazos ou valores que não estejam no contexto."
    )

    try:
        resposta = cliente.models.generate_content(
            model=GEMINI_MODEL, contents=prompt, config=_config()
        )
        texto = (resposta.text or "").strip()
        return texto if texto else resposta_base
    except Exception as e:
        print(f"[LLM] Falha na resposta final, usando fallback: {e}")
        return "\n".join([resposta_base, info_chamado])


if __name__ == "__main__":
    # Teste direto da LLM:  python -m servicos.llm
    print("LLM (Gemini) disponível:", llm_disponivel())
    if not llm_disponivel():
        print("Configure GEMINI_API_KEY no arquivo .env e rode: pip install google-genai")
    else:
        print("\n--- Teste de texto (Fase 2) ---")
        print(gerar_resposta(
            mensagem="Paguei via Pix mas meu pedido continua aguardando pagamento",
            categoria="pagamento",
            prioridade="alta",
            resposta_base="Verifique o status do pagamento na sua conta. Pix pode levar alguns minutos.",
        ))
        # Teste de imagem (se existir a imagem de exemplo)
        exemplo = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "exemplos", "erro_pagamento.png",
        )
        if os.path.exists(exemplo):
            print("\n--- Teste de imagem (Fase 3) ---")
            print(analisar_imagem(exemplo, "o site deu esse erro quando fui pagar"))
