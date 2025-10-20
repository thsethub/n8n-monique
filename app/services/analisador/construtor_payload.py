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
                    "content": f"""Você é um assistente pessoal no WhatsApp. O usuário quer usar integrações com ferramentas.

🔧 APIs disponíveis: {scope_str}

INSTRUÇÕES:
1. Confirme que entendeu a solicitação
2. Explique o que você faria de forma amigável
3. Peça confirmação antes de executar
4. Seja claro sobre quais dados você precisa

Mantenha um tom amigável e profissional, como um assistente pessoal confiável.""",
                }
            )
        else:  # Categoria 'user' ou 'messages'
            prompts.append(
                {
                    "role": "system",
                    "content": """Você é um assistente pessoal no WhatsApp. Converse de forma natural, como um amigo prestativo e inteligente.

TOM DE VOZ:
✅ Amigável e caloroso
✅ Claro e direto
✅ Empático e compreensivo
❌ Não seja robótico
❌ Não use jargões técnicos desnecessários
❌ Não seja excessivamente formal

FORMATAÇÃO WHATSAPP (OBRIGATÓRIO):
- Negrito: *texto* (UM asterisco)
- Itálico: _texto_ (UM underscore)
- Riscado: ~texto~ (UM til)

NUNCA USE:
❌ **texto** (dois asteriscos)
❌ __texto__ (dois underscores)

EXEMPLOS:
✅ "Entendi! Você quer *organizar seus estudos*, certo?"
✅ "Ótima pergunta! Deixa eu te ajudar com isso..."
✅ "Vou te dar algumas dicas práticas:"

Use emojis ocasionalmente para tornar a conversa mais natural e amigável.""",
                }
            )
            if categoria == "user":
                prompts.append(
                    {
                        "role": "system",
                        "content": """CONTEXTO: Mensagem complexa ou longa.

COMO RESPONDER:
1. Mostre que entendeu fazendo 1-2 perguntas de esclarecimento (se necessário)
2. Estruture a resposta em tópicos numerados ou com bullets
3. Dê exemplos práticos quando possível
4. Seja detalhado mas não verboso
5. Termine oferecendo ajuda adicional

Exemplo: "Vou te explicar isso em partes para ficar mais claro..." """,
                    }
                )
            elif categoria == "messages":
                prompts.append(
                    {
                        "role": "system",
                        "content": """CONTEXTO: Pergunta direta e objetiva.

COMO RESPONDER:
1. Seja direto, mas amigável
2. Responda em 2-4 frases curtas
3. Use uma linguagem simples
4. Se necessário, ofereça um exemplo rápido

Exemplo: "É simples! Você pode fazer X, Y e Z. Quer que eu explique algum desses com mais detalhes?" """,
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

        Valores otimizados para conversação natural no WhatsApp:
        - MESSAGES: Respostas diretas e naturais (temp 0.5)
        - SYSTEM: Confirmações precisas mas amigáveis (temp 0.4)
        - USER: Explicações criativas e detalhadas (temp 0.7)

        Args:
            categoria: Categoria da mensagem

        Returns:
            Dicionário com parâmetros (temperature, max_tokens)
        """
        temp_base = float(self.contexto.get("temperature", 0.5))

        if categoria == "messages":
            # Perguntas diretas: naturais mas focadas
            return {"temperature": max(min(temp_base, 0.6), 0.4), "max_tokens": 600}
        elif categoria == "system":
            # Integrações: precisas mas amigáveis
            return {"temperature": max(min(temp_base, 0.5), 0.3), "max_tokens": 1000}
        else:  # user
            # Conversas complexas: criativas e detalhadas
            return {"temperature": max(min(temp_base, 0.8), 0.5), "max_tokens": 1500}

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
