"""
FASE 2 — Serviço de LLM com Google Gemini.

Pega o resultado do classificador (Fase 1) e gera uma resposta amigável,
em passos numerados, para o cliente.

Por que Gemini?
  A API do Gemini tem camada GRATUITA (com limite de requisições por minuto/dia),
  o que serve bem para um projeto de estudo. Usamos o SDK oficial `google-genai`.
  A chave é gerada em https://aistudio.google.com/apikey
  Modelo padrão: "gemini-2.5-flash" (rápido e barato). Para trocar de modelo, basta
  definir GEMINI_MODEL no .env — sem mexer no código.

Controle da resposta (responde às dicas do enunciado):
  - A chave fica no arquivo .env (NUNCA no código).
  - Um "prompt de sistema" rígido define tom cordial, resposta em passos e
    PROÍBE prometer prazo, reembolso ou desconto fora do contexto.
  - Enviamos à LLM apenas o contexto confiável vindo da Fase 1; ela não decide nada.
  - Se a LLM falhar ou não houver chave, caímos no FALLBACK: devolvemos a
    resposta base da Fase 1. Assim o atendimento nunca fica mudo.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_TIMEOUT_S = 30  # evita que a requisição fique pendurada se a API demorar

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

# Importa o SDK do Gemini. Se não estiver instalado, o sistema ainda roda em modo fallback.
try:
    from google import genai
    from google.genai import types
    _SDK_OK = True
except Exception:
    _SDK_OK = False

_cliente = None


def _get_cliente():
    """Cria (uma vez) o cliente do Gemini. None se não for possível."""
    global _cliente
    if not _SDK_OK or not GEMINI_API_KEY:
        return None
    if _cliente is None:
        _cliente = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_S * 1000),  # em ms
        )
    return _cliente


def llm_disponivel() -> bool:
    """True se há SDK instalado E chave configurada."""
    return _get_cliente() is not None


def gerar_resposta(mensagem: str, categoria: str, prioridade: str, resposta_base: str) -> str:
    """Gera uma resposta amigável, passo a passo, a partir do contexto da Fase 1.

    Se a LLM não estiver disponível ou falhar, retorna a resposta_base (fallback).
    """
    cliente = _get_cliente()
    if cliente is None:
        return resposta_base  # fallback

    conteudo_usuario = (
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
            model=GEMINI_MODEL,
            contents=conteudo_usuario,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCAO_SISTEMA,
                temperature=0.4,  # mais baixa = respostas mais previsíveis
            ),
        )
        # .text pode vir vazio/None se a resposta for bloqueada pelos filtros de segurança
        texto = (resposta.text or "").strip()
        return texto if texto else resposta_base
    except Exception as e:
        print(f"[LLM] Falha ao gerar resposta, usando fallback: {e}")
        return resposta_base


if __name__ == "__main__":
    # Teste direto da LLM:  python -m servicos.llm
    print(f"LLM (Gemini · {GEMINI_MODEL}) disponível:", llm_disponivel())
    if not llm_disponivel():
        print("Configure GEMINI_API_KEY no arquivo .env e instale: pip install google-genai")
    else:
        texto = gerar_resposta(
            mensagem="Paguei via Pix mas meu pedido continua aguardando pagamento",
            categoria="pagamento",
            prioridade="alta",
            resposta_base="Verifique o status do pagamento na sua conta. Pix pode levar alguns minutos.",
        )
        print("\nResposta gerada pela LLM:\n")
        print(texto)
