"""
Middleware de monitoramento de latência e logging estruturado.
"""
import time
from fastapi import Request
from app.core.config import logger
from app.core.metrics import metricas


async def log_request_latency_middleware(request: Request, call_next):
    """
    Middleware que mede o tempo de processamento de cada requisição
    e registra logs estruturados com métricas de performance.
    """
    start_time = time.time()
    metricas["total_requests"] += 1

    # Captura informações da requisição
    method = request.method
    path = request.url.path
    user_agent = request.headers.get("user-agent", "unknown")
    content_length = request.headers.get("content-length", "0")

    try:
        # Processa a requisição
        response = await call_next(request)

        # Calcula métricas de performance
        duration_ms = round((time.time() - start_time) * 1000, 2)
        metricas["total_latency_ms"] += duration_ms

        # Log estruturado com todas as métricas importantes para o dashboard
        logger.info(
            "Requisição processada com sucesso",
            log_type="api_performance",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_size_bytes=int(content_length) if content_length.isdigit() else 0,
            user_agent=user_agent[:50],  # Limita o tamanho para não poluir os logs
        )

        # Adiciona o header com a duração na resposta (útil para debugging)
        response.headers["X-Process-Time"] = str(duration_ms)

        return response

    except Exception as e:
        # Em caso de erro, ainda registra o tempo de processamento
        duration_ms = round((time.time() - start_time) * 1000, 2)
        metricas["error_count"] += 1

        logger.error(
            "Erro durante processamento da requisição",
            log_type="api_performance",
            method=method,
            path=path,
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e)[:100],  # Limita a mensagem de erro
        )

        # Re-levanta a exceção para que o FastAPI a trate normalmente
        raise
