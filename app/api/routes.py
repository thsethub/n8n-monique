"""
Rotas da API FastAPI.
"""

import time
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse

from app.core.config import logger
from app.core.metrics import metricas, classificacao_cache
from app.services.analisador import AnalisadorDeMensagem

router = APIRouter()


@router.post("/webhook", summary="Webhook para receber mensagens do WhatsApp")
async def webhook_whatsapp(payload: Dict[str, Any] = Body(...)) -> JSONResponse:
    """
    Endpoint simplificado para receber mensagens via webhook (ngrok).
    Recebe JSON com 'from' (número) e 'message' (mensagem).
    
    Exemplo de uso com curl:
    curl -X POST http://localhost:8181/webhook \
      -H "Content-Type: application/json" \
      -d '{"from": "5511999999999", "message": "agendar reunião amanhã"}'
    """
    # Extrai os dados do payload
    from_number = payload.get("from", "unknown")
    message = payload.get("message", "")

    logger.info(
        "Webhook recebido",
        log_type="webhook",
        from_number=from_number,
        message_length=len(message),
    )

    # Converte para o formato esperado pelo preprocessador
    payload_processado = {
        "message": message,
        "ctx": {"lang": "pt", "temperature": 0.3},
        "from": from_number,
        "history": [],
    }

    # Processa a mensagem
    analisador = AnalisadorDeMensagem(payload_processado)
    resultado_final = await analisador.processar_mensagem()  # pylint: disable=no-member

    # Adiciona informações do webhook
    resultado_final["webhook"] = {"from": from_number, "received_at": time.time()}

    logger.info(
        "Webhook processado",
        log_type="webhook_response",
        from_number=from_number,
        bucket=resultado_final.get("classification", {}).get("bucket"),
    )

    return JSONResponse(content=resultado_final)


@router.post("/preprocess", summary="Processa e prepara uma mensagem para a IA")
async def rota_de_preprocessamento(payload: Dict[str, Any] = Body(...)) -> JSONResponse:
    """
    Endpoint otimizado com cache e medição de latência.
    Agora é completamente assíncrono para melhor performance.
    """
    if not payload:
        logger.warning("Recebido payload vazio.", log_type="request_validation")
        raise HTTPException(status_code=400, detail="O payload não pode ser vazio.")

    # 1. Cria o Analisador (O "Gerente") para cuidar do pedido.
    analisador = AnalisadorDeMensagem(payload)

    # 2. Pede para o Analisador processar a mensagem e preparar o resultado (assíncrono).
    resultado_final = await analisador.processar_mensagem()  # pylint: disable=no-member

    # 3. Retorna o resultado completo para o n8n.
    return JSONResponse(content=resultado_final)


@router.get("/health", summary="Verifica o status do serviço")
async def health_check():
    """
    Endpoint de health check para monitoramento.
    """
    return {
        "status": "healthy",
        "service": "preproc-api",
        "version": "2.0.0",
        "timestamp": time.time(),
    }


@router.get("/metrics", summary="Retorna métricas de performance do serviço")
async def metrics_endpoint():
    """
    Expõe métricas importantes para monitoramento:
    - Total de requisições processadas
    - Cache hits/misses
    - Latência média
    - Taxa de erro
    """
    total_requests = metricas["total_requests"]
    cache_hits = metricas["cache_hits"]
    cache_misses = metricas["cache_misses"]

    # Calcula taxa de cache hit
    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

    # Calcula latência média
    avg_latency_ms = (
        metricas["total_latency_ms"] / total_requests if total_requests > 0 else 0
    )

    # Calcula taxa de erro
    error_rate = (
        metricas["error_count"] / total_requests * 100 if total_requests > 0 else 0
    )

    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate_percent": round(cache_hit_rate, 2),
        "cache_size": len(classificacao_cache),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "error_count": metricas["error_count"],
        "error_rate_percent": round(error_rate, 2),
        "timestamp": time.time(),
    }
