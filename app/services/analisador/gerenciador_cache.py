"""
Módulo responsável pelo gerenciamento de cache de classificações.
"""

import hashlib
from typing import Any, Dict, Optional
from app.core.metrics import classificacao_cache, metricas
from app.core.config import logger
from .normalizador import normalizar_texto


class GerenciadorDeCache:
    """Gerencia operações de cache para classificações de mensagens."""

    @staticmethod
    def gerar_cache_key(mensagem: str) -> str:
        """
        Gera uma chave de cache baseada no hash da mensagem normalizada.

        Args:
            mensagem: Mensagem original

        Returns:
            Hash MD5 da mensagem normalizada
        """
        mensagem_normalizada = normalizar_texto(mensagem)
        return hashlib.md5(mensagem_normalizada.encode()).hexdigest()

    @staticmethod
    def obter_do_cache(cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Busca um resultado no cache.

        Args:
            cache_key: Chave do cache

        Returns:
            Resultado cacheado ou None se não encontrado
        """
        resultado = classificacao_cache.get(cache_key)
        if resultado:
            metricas["cache_hits"] += 1
            logger.info(
                "Classificação recuperada do cache",
                log_type="cache_hit",
                cache_key=cache_key[:20],
            )
        else:
            metricas["cache_misses"] += 1
        return resultado

    @staticmethod
    def salvar_no_cache(cache_key: str, resultado: Dict[str, Any]) -> None:
        """
        Salva um resultado no cache.

        Args:
            cache_key: Chave do cache
            resultado: Resultado a ser cacheado
        """
        classificacao_cache[cache_key] = resultado
