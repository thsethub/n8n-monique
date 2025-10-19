"""
Regex pré-compiladas para análise de mensagens.
"""

import re

REGEX_PT_INDICADORES = re.compile(r"[ãõçáéíóúàêô]", re.IGNORECASE)
REGEX_PT_PALAVRAS = re.compile(
    r"\b(que|como|quando|onde|reuniao|calendario)\b", re.IGNORECASE
)
REGEX_EN_PALAVRAS = re.compile(
    r"\b(what|how|when|where|meeting|calendar)\b", re.IGNORECASE
)
REGEX_PERGUNTA_FACTUAL = re.compile(
    r"\b(que dia e hoje|data de hoje|quem descobriu|capital de|definicao de|quanto e|resultado de)\b",
    re.IGNORECASE,
)
REGEX_REFERENCIAS_PESSOAIS = re.compile(
    r"\b(meu|minha|minhas|meus|eu|para mim|no meu caso)\b", re.IGNORECASE
)
REGEX_PLANO_ESTRATEGIA = re.compile(
    r"\b(plano|passo a passo|organizar|estratégia|roteiro|currículo|proposta|estudo)\b",
    re.IGNORECASE,
)
REGEX_MULTIPLAS_FRASES = re.compile(r"[.?!;]")
