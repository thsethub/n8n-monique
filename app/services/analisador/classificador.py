"""
Módulo responsável pela classificação de mensagens em categorias.
"""

from typing import List, Tuple
from app.utils.regex import (
    REGEX_PERGUNTA_FACTUAL,
    REGEX_REFERENCIAS_PESSOAIS,
    REGEX_PLANO_ESTRATEGIA,
    REGEX_MULTIPLAS_FRASES,
)
from .constantes import PALAVRAS_CHAVE_DE_SISTEMA


class Classificador:
    """Classifica mensagens em categorias (system, messages, user)."""

    @staticmethod
    def determinar_categoria(
        mensagem_original: str, texto_normalizado: str
    ) -> Tuple[str, List[str]]:
        """
        Determina a categoria da mensagem (system, messages, user).
        Otimizado com buscas 'in' ao invés de regex onde possível.

        Args:
            mensagem_original: Mensagem original do usuário
            texto_normalizado: Texto normalizado para análise

        Returns:
            Tupla com (categoria, lista de motivos)
        """

        # Prioridade 1: É um pedido que envolve sistemas/integrações?
        palavras_encontradas = [
            p for p in PALAVRAS_CHAVE_DE_SISTEMA if p in texto_normalizado
        ]
        if palavras_encontradas:
            motivo = f"Palavras-chave de sistemas/APIs: {', '.join(palavras_encontradas[:6])}"
            return "system", [motivo]

        # Prioridade 2: É uma pergunta direta e objetiva?
        if Classificador._e_pergunta_direta_e_objetiva(
            mensagem_original, texto_normalizado
        ):
            return "messages", ["Pergunta direta/fechada detectada."]

        # Prioridade 3: É uma mensagem complexa ou pessoal?
        if Classificador._e_mensagem_complexa_ou_pessoal(mensagem_original):
            return "user", ["Mensagem com necessidade de personalização/contexto."]

        # Se não se encaixar em nenhuma regra, decide pelo tamanho.
        if len(mensagem_original) < 60:
            return "messages", ["Curta e objetiva; sem necessidade clara de contexto."]
        else:
            return "user", ["Mensagem requer elaboração moderada."]

    @staticmethod
    def _e_pergunta_direta_e_objetiva(texto: str, texto_normalizado: str) -> bool:
        """
        Verifica se é uma pergunta direta usando regex pré-compilada.

        Args:
            texto: Texto original
            texto_normalizado: Texto normalizado

        Returns:
            True se for pergunta direta e objetiva
        """
        e_curta_e_termina_com_interrogacao = len(texto) <= 80 and texto.endswith("?")
        contem_termos_factuais = bool(REGEX_PERGUNTA_FACTUAL.search(texto_normalizado))
        return e_curta_e_termina_com_interrogacao or contem_termos_factuais

    @staticmethod
    def _e_mensagem_complexa_ou_pessoal(texto: str) -> bool:
        """
        Verifica complexidade da mensagem usando regex pré-compiladas.

        Args:
            texto: Texto original

        Returns:
            True se for mensagem complexa ou pessoal
        """
        e_longa = len(texto) > 160
        usa_referencias_pessoais = bool(REGEX_REFERENCIAS_PESSOAIS.search(texto))
        pede_um_plano_ou_estrategia = bool(REGEX_PLANO_ESTRATEGIA.search(texto))
        tem_multiplas_frases = len(REGEX_MULTIPLAS_FRASES.findall(texto)) > 1

        return (
            e_longa
            or usa_referencias_pessoais
            or pede_um_plano_ou_estrategia
            or tem_multiplas_frases
        )
