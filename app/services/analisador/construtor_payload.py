"""
Módulo responsável pela construção do payload para a API do OpenAI.
"""

from typing import Any, Dict, List, Tuple
from .detector_scopes import DetectorDeScopes
from .detector_idioma import DetectorDeIdioma


class ConstrutorDePayload:
    """Constrói payloads otimizados para envio à API do OpenAI."""

    def __init__(self, contexto: Dict[str, Any], payload_original: Dict[str, Any]):
        """
        Inicializa o construtor de payload.

        Args:
            contexto: Contexto da requisição (ctx)
            payload_original: Payload original da requisição
        """
        self.contexto = contexto
        self.payload_original = payload_original

    def construir_payload(
        self, categoria: str, mensagem_original: str, texto_normalizado: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Constrói o payload otimizado para envio à API do OpenAI.

        Args:
            categoria: Categoria da mensagem (system/messages/user)
            mensagem_original: Mensagem original do usuário
            texto_normalizado: Texto normalizado

        Returns:
            Tupla com (payload completo, lista de scopes)
        """
        idioma = self.contexto.get("lang") or DetectorDeIdioma.determinar_idioma(
            mensagem_original
        )

        prompts_de_sistema, scope = self._criar_prompts_de_sistema(
            categoria, idioma, texto_normalizado
        )
        historico_da_conversa = self._obter_historico_da_conversa()

        mensagens = (
            prompts_de_sistema
            + historico_da_conversa
            + [{"role": "user", "content": mensagem_original}]
        )

        parametros_dinamicos = self._calcular_parametros_da_ia(categoria)
        modelo_selecionado = self._selecionar_modelo_ia(categoria)

        payload_final = {
            "model": modelo_selecionado,
            "messages": mensagens,
            **parametros_dinamicos,
        }
        return payload_final, scope

    def _criar_prompts_de_sistema(
        self, categoria: str, idioma: str, texto_normalizado: str
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Cria os prompts de sistema apropriados baseados na categoria e idioma.

        Args:
            categoria: Categoria da mensagem
            idioma: Idioma detectado
            texto_normalizado: Texto normalizado

        Returns:
            Tupla com (lista de prompts, lista de scopes)
        """
        prompts = []
        scope_detectadas = []

        # 1. Prompt de Idioma (sempre adicionado)
        prompt_idioma = (
            "Reply in English."
            if idioma == "en"
            else "Responda em português do Brasil."
        )
        prompts.append({"role": "system", "content": prompt_idioma})

        # 2. Prompts Específicos da Categoria
        if categoria == "system":
            scope_detectadas = DetectorDeScopes.detectar_scopes(texto_normalizado)
            scope_str = ", ".join(scope_detectadas) or "nenhuma"
            prompts.append(
                {
                    "role": "system",
                    "content": f"MODO INTEGRAÇÃO ATIVO. A intenção do usuário parece ser usar ferramentas como calendário, documentos ou pagamentos. Antes de agir, sempre confirme os detalhes necessários. Informe que usaria as APIs ({scope_str}) e peça confirmação.",
                }
            )
        else:  # Categoria 'user' ou 'messages'
            prompts.append(
                {
                    "role": "system",
                    "content": """Você é um assistente no WhatsApp, amigável e direto. Evite jargões. Se não souber algo, admita e sugira como verificar.

FORMATAÇÃO WHATSAPP (OBRIGATÓRIO):
- Negrito: *texto* (UM asterisco antes e depois)
- Itálico: _texto_ (UM underscore antes e depois)
- Riscado: ~texto~ (UM til antes e depois)

NUNCA USE:
❌ **texto** (dois asteriscos)
❌ __texto__ (dois underscores)
❌ Markdown tradicional

EXEMPLOS CORRETOS:
✅ *Defina seu objetivo* (negrito)
✅ _Saiba exatamente_ (itálico)
✅ Use *métodos ativos de estudo* (negrito no meio da frase)

Sempre use formatação WhatsApp nativa, não Markdown!""",
                }
            )
            if categoria == "user":
                prompts.append(
                    {
                        "role": "system",
                        "content": "INSTRUÇÃO ADICIONAL: A mensagem do usuário é complexa. Faça até 2 perguntas para entender melhor e estruture a resposta final em tópicos, se aplicável.",
                    }
                )
            elif categoria == "messages":
                prompts.append(
                    {
                        "role": "system",
                        "content": "INSTRUÇÃO ADICIONAL: A mensagem é uma pergunta direta. Responda de forma objetiva em 1 a 3 frases.",
                    }
                )

        return prompts, scope_detectadas

    def _selecionar_modelo_ia(self, categoria: str) -> str:
        """
        Seleciona o modelo de IA mais apropriado baseado na categoria da mensagem.

        Args:
            categoria: Categoria da mensagem

        Returns:
            Nome do modelo a ser usado
        """
        modelo_customizado = self.contexto.get("model")
        if modelo_customizado:
            return modelo_customizado

        if categoria == "messages":
            return "gpt-4o-mini"
        else:
            return "gpt-4.1-mini"

    def _calcular_parametros_da_ia(self, categoria: str) -> Dict[str, Any]:
        """
        Calcula parâmetros dinâmicos (temperature, max_tokens) baseados na categoria.

        Args:
            categoria: Categoria da mensagem

        Returns:
            Dicionário com parâmetros (temperature, max_tokens)
        """
        temp_base = float(self.contexto.get("temperature", 0.3))

        if categoria == "messages":
            return {"temperature": min(temp_base, 0.2), "max_tokens": 400}
        elif categoria == "system":
            return {"temperature": min(temp_base, 0.3), "max_tokens": 900}
        else:  # user
            return {"temperature": min(max(temp_base, 0.3), 0.6), "max_tokens": 900}

    def _obter_historico_da_conversa(self) -> List[Dict[str, str]]:
        """
        Obtém o histórico da conversa, limitado a 2-3 mensagens mais recentes.

        Returns:
            Lista com histórico formatado
        """
        historico = self.payload_original.get("history", [])
        if not isinstance(historico, list):
            return []

        historico_valido = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in historico
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        return historico_valido[-3:]
