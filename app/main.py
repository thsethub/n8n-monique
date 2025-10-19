"""
Ponto de entrada da aplicação FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

# from app.core.config import logger
from app.core.middleware import log_request_latency_middleware
from app.api.routes import router as api_router

app = FastAPI(
    title="Serviço de Análise e Preparação de Mensagens para IA",
    description="Uma API que recebe uma mensagem, a classifica e prepara um payload otimizado para a IA.",
)

# Adiciona middleware de compressão GZip para reduzir latência de transferência
app.add_middleware(GZipMiddleware, minimum_size=500)

# Adiciona middleware de monitoramento de latência
app.middleware("http")(log_request_latency_middleware)

# Registra as rotas da API
app.include_router(api_router)
