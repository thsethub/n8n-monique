"""
Módulo responsável pela detecção de idioma.
"""

from app.utils.regex import REGEX_PT_INDICADORES, REGEX_PT_PALAVRAS, REGEX_EN_PALAVRAS


class DetectorDeIdioma:
    """Detecta o idioma de uma mensagem."""

    @staticmethod
    def determinar_idioma(texto: str) -> str:
        """
        Determina o idioma usando regex pré-compiladas.

        Args:
            texto: Texto a ser analisado

        Returns:
            'pt' para português ou 'en' para inglês
        """
        tem_pt = bool(REGEX_PT_INDICADORES.search(texto)) or bool(
            REGEX_PT_PALAVRAS.search(texto)
        )
        tem_en = bool(REGEX_EN_PALAVRAS.search(texto))

        return "en" if tem_en and not tem_pt else "pt"
