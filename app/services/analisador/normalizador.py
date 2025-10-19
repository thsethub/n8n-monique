"""
Módulo responsável pela normalização de texto.
"""

from functools import lru_cache
from unidecode import unidecode


@lru_cache(maxsize=512)
def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removendo acentos e convertendo para minúsculas.
    Usa LRU cache para evitar reprocessamento de textos idênticos.

    Args:
        texto: Texto a ser normalizado

    Returns:
        Texto normalizado (minúsculas, sem acentos)
    """
    texto_minusculo = texto.lower()
    texto_sem_acentos = unidecode(texto_minusculo)
    return texto_sem_acentos
