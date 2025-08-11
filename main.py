import os
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
from unidecode import unidecode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Serviço de Pré‑processamento de Mensagens WhatsApp")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

def preprocess_text(text: str) -> str:
    if text is None:
        return ""
    # 1. Remoção de espaços
    processed = text.strip()
    # 2. Conversão para minúsculas
    processed = processed.lower()
    # 3. Remoção de acentos
    processed = unidecode(processed)
    # 4. Remoção de pontuação (tudo o que não for palavra ou espaço)
    processed = re.sub(r"[^\w\s]", "", processed)
    # 5. Compactação de espaços múltiplos
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed


# @app.get("/health", response_class=PlainTextResponse)
# async def health_check() -> str:
#     """Endpoint de saúde para monitoramento.

#     Retorna uma string simples indicando que o serviço está em execução.
#     """
#     return "OK"


# @app.get("/webhook", response_class=PlainTextResponse)
# async def verify_webhook(request: Request) -> PlainTextResponse:
#     """Endpoint de verificação do webhook.

#     O WhatsApp envia uma requisição GET quando você registra o webhook. É
#     necessário verificar se o modo (`hub.mode`) é 'subscribe' e se o
#     `hub.verify_token` corresponde ao token definido. Caso positivo,
#     retornamos `hub.challenge`; caso contrário, respondemos com erro 400.
#     A lógica segue o exemplo da documentação oficial【282973114446148†L145-L160】.
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     verify_token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")
#     if mode == "subscribe" and verify_token == VERIFY_TOKEN:
#         if challenge:
#             logger.info("Webhook verificado com sucesso.")
#             return PlainTextResponse(content=challenge, status_code=200)
#         else:
#             raise HTTPException(status_code=400, detail="Missing challenge parameter.")
#     logger.warning("Falha ao verificar webhook: modo=%s token=%s", mode, verify_token)
#     raise HTTPException(status_code=400, detail="Verificação inválida.")


async def forward_to_n8n(payload: Dict[str, Any]) -> None:
    """Encaminha a mensagem pré‑processada para a URL configurada do n8n.

    Se a variável de ambiente N8N_WEBHOOK_URL estiver definida, este método
    envia uma requisição POST assíncrona contendo o payload fornecido. Caso
    contrário, nenhuma ação é realizada. O uso de httpx permite que as
    requisições sejam feitas de forma assíncrona dentro do FastAPI.
    """
    if not N8N_WEBHOOK_URL:
        logger.info("N8N_WEBHOOK_URL não configurado; nenhuma mensagem encaminhada.")
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(N8N_WEBHOOK_URL, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info("Mensagem encaminhada para n8n com status %s", response.status_code)
    except Exception as exc:
        logger.error("Erro ao encaminhar mensagem para n8n: %s", exc)


# @app.post("/webhook")
# async def receive_message(request: Request) -> JSONResponse:
#     """Recebe notificações de mensagens da API do WhatsApp e processa o conteúdo.

#     **Atenção:** Este endpoint espera o payload no formato bruto enviado pela
#     API do WhatsApp (objeto `entry -> changes -> value -> messages`). Se o
#     seu fluxo n8n já estiver recebendo a notificação do WhatsApp e apenas
#     encaminhar uma mensagem simples para o serviço, use o endpoint
#     :func:`preprocess_from_n8n` abaixo.

#     Para cada mensagem de texto (`type == 'text'`), o serviço extrai o campo
#     `text.body`【306868418922723†L88-L99】, aplica `preprocess_text` e monta
#     um dicionário com o número do remetente (`from`), o ID da mensagem, o
#     timestamp, o texto original e o texto processado. Opcionalmente,
#     encaminha o resultado para outro fluxo do n8n por meio de
#     :func:`forward_to_n8n`.
#     """
#     try:
#         body: Dict[str, Any] = await request.json()
#     except Exception:
#         raise HTTPException(status_code=400, detail="Payload inválido ou não JSON.")

#     processed_messages: List[Dict[str, Any]] = []
#     logger.debug("Payload recebido (webhook WhatsApp): %s", body)

#     entries = body.get("entry") or []
#     if not isinstance(entries, list):
#         entries = []

#     for entry in entries:
#         for change in entry.get("changes", []) if isinstance(entry, dict) else []:
#             value = change.get("value", {})
#             for message in value.get("messages", []):
#                 if message.get("type") != "text":
#                     continue
#                 text_obj = message.get("text", {})
#                 original_text: Optional[str] = text_obj.get("body")
#                 processed_text = preprocess_text(original_text)
#                 result = {
#                     "from": message.get("from"),
#                     "id": message.get("id"),
#                     "timestamp": message.get("timestamp"),
#                     "original": original_text,
#                     "processed": processed_text,
#                 }
#                 processed_messages.append(result)
#                 await forward_to_n8n(result)

#     return JSONResponse(
#         content={"status": "received", "processed_messages": processed_messages},
#         status_code=200,
#     )


@app.post("/preprocess")
async def preprocess_from_n8n(payload: Dict[str, Any]) -> JSONResponse:

    original = payload.get("message") or payload.get("text") or payload.get("body")
    if original is None:
        raise HTTPException(status_code=400, detail="Campo 'message' obrigatório.")
    processed = preprocess_text(original)
    result = {
        "from": payload.get("from"),
        "original": original,
        "processed": processed,
    }
    # Encaminha o resultado para outro fluxo, se configurado
    await forward_to_n8n(result)
    return JSONResponse(result)