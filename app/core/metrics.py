"""
Métricas globais e cache do microserviço.
"""

from cachetools import TTLCache

# Cache em memória para classificações (TTL de 1 hora)
# Reduz drasticamente tempo de resposta para mensagens similares
classificacao_cache = TTLCache(maxsize=1000, ttl=3600)

# Contador de métricas globais
metricas = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_latency_ms": 0.0,
    "error_count": 0,
}
