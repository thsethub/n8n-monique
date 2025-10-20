"""
Módulo responsável pela detecção de scopes/integrações necessárias.
"""

from typing import List
from .constantes import SCOPE_CACHE


class DetectorDeScopes:
    """Detecta scopes necessários baseado no conteúdo da mensagem."""

    @staticmethod
    def detectar_scopes(texto_normalizado: str) -> List[str]:
        """
        Detecta scopes necessários considerando o contexto principal da mensagem.
        Prioriza a ação principal para evitar scopes desnecessários.
        Usa cache de padrões conhecidos para performance máxima.

        Args:
            texto_normalizado: Texto normalizado da mensagem

        Returns:
            Lista de scopes detectados
        """
        # Verifica cache de padrões conhecidos primeiro (otimização crítica)
        for padrao, scopes in SCOPE_CACHE.items():
            if padrao in texto_normalizado:
                return scopes.copy()

        scope_detectadas = []

        # Verifica se há ações específicas de email (busca direta, sem regex)
        acoes_email = [
            "envie",
            "mande",
            "escreva",
            "responda",
            "encaminhe",
            "send",
            "reply",
            "forward",
        ]
        tem_acao_email = any(acao in texto_normalizado for acao in acoes_email)
        tem_palavra_email = any(
            palavra in texto_normalizado for palavra in ["gmail", "email", "e-mail"]
        )

        # Verifica se há ações específicas de calendário
        acoes_calendario = [
            "agende",
            "marque",
            "crie evento",
            "adicione evento",
            "schedule",
            "book",
        ]
        tem_acao_calendario = any(
            acao in texto_normalizado for acao in acoes_calendario
        )
        tem_palavra_calendario = any(
            palavra in texto_normalizado
            for palavra in [
                "calendar", "agenda", "evento", "reuniao", "meeting",
                "aula", "sala", "hoje", "amanha", "hr", ":", 
                "segunda", "terca", "quarta", "quinta", "sexta", 
                "sabado", "domingo"
            ]
        )

        # Verifica se há múltiplas intenções explícitas
        tem_multiplas_acoes = any(
            conector in texto_normalizado
            for conector in ["e depois", "tambem", "alem disso", "and then", "also"]
        )

        # Se há clara intenção de email E calendário com conectores, inclui ambos
        if (
            (tem_acao_email and tem_palavra_email)
            and (tem_acao_calendario or tem_palavra_calendario)
            and tem_multiplas_acoes
        ):
            scope_detectadas.append("https://mail.google.com/")
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
            return scope_detectadas

        # Se há clara intenção de email, prioriza apenas o scope de email
        if tem_acao_email and tem_palavra_email:
            scope_detectadas.append("https://mail.google.com/")
            return scope_detectadas

        # Se há clara intenção de calendário, prioriza apenas o scope de calendário
        if tem_acao_calendario and (
            tem_palavra_calendario or "compromisso" in texto_normalizado
        ):
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
            return scope_detectadas

        # Lógica tradicional para casos ambíguos (busca direta 'in', sem regex)
        if any(k in texto_normalizado for k in ["calendar", "agenda", "evento"]):
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
        elif "compromisso" in texto_normalizado and not tem_acao_email:
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")

        # ===== SHEETS: SEMPRE RETORNA 2 SCOPES =====
        if any(
            k in texto_normalizado
            for k in ["sheet", "planilha", "tabela", "spreadsheet"]
        ):
            scope_detectadas.append("https://www.googleapis.com/auth/spreadsheets")
            scope_detectadas.append("https://www.googleapis.com/auth/drive")
            return scope_detectadas  # Retorna imediatamente para evitar duplicatas

        # ===== DOCS: SEMPRE RETORNA 2 SCOPES =====
        if any(
            k in texto_normalizado
            for k in ["documento", "document", "doc", "arquivo", "file", "pdf"]
        ):
            scope_detectadas.append("https://www.googleapis.com/auth/drive")
            scope_detectadas.append("https://www.googleapis.com/auth/documents")
            return scope_detectadas  # Retorna imediatamente para evitar duplicatas

        # ===== GMAIL: 1 SCOPE =====
        if any(k in texto_normalizado for k in ["gmail", "email", "e-mail"]):
            scope_detectadas.append("https://mail.google.com/")

        # ===== DRIVE GENÉRICO: 1 SCOPE =====
        if "drive" in texto_normalizado:
            scope_detectadas.append("https://www.googleapis.com/auth/drive")

        # ===== BOLETO: SCOPE CUSTOMIZADO =====
        if any(k in texto_normalizado for k in ["boleto", "fatura", "cobranca"]):
            scope_detectadas.append("boleto")

        return scope_detectadas
