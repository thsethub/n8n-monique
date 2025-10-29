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
            categoria: Categoria da mensagem (system/messages/user/unclear)
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

        # Detectar scopes quando necessário
        if categoria == "system":
            scope_detectadas = DetectorDeScopes.detectar_scopes(texto_normalizado)

        scope_str = ", ".join(scope_detectadas) or "nenhuma"

        # 1. Prompt de Idioma (sempre adicionado)
        prompt_idioma = (
            "Reply in English."
            if idioma == "en"
            else "Responda em português do Brasil."
        )
        prompts.append({"role": "system", "content": prompt_idioma})

        # 2. Prompt Base
        prompt_base = f"""Você é um assistente pessoal, chamada MoniqueBOT, integrada ao WhatsApp que ajuda o usuário a interagir com ferramentas e APIs.

APIs disponíveis: {scope_str}

FUNÇÃO DO ASSISTENTE:
- Compreender solicitações do usuário de forma natural
- Ajudar com orientações, execuções e confirmações de ações
- Manter o tom de voz humano, empático e claro
- Retornar informações estruturadas no formato "chave: valor" quando apropriado

---

REGRAS CRÍTICAS DE FORMATAÇÃO (WhatsApp):
Estas regras são OBRIGATÓRIAS. Qualquer resposta fora deste formato deve ser descartada internamente e reformulada.

✅ Separe ideias com QUEBRAS DE LINHA
✅ Use listas com números, assim:

1. Título
Explicação na linha seguinte.

OU:

Ponto - Explicação direta

✅ Use formatação do WhatsApp APENAS quando necessário e de forma inteligente:
- *texto* para negrito (ênfase forte, títulos importantes)
- _texto_ para itálico (ênfase leve, observações)
- ~texto~ para tachado (correções, informações desatualizadas)
- ```texto``` para código (dados técnicos, números, cálculos, JSON, comandos)

Exemplo de uso inteligente:
*IMPORTANTE:* Seu pedido foi _aprovado_
resultado: ```R$ 1.234,56```
status anterior: ~pendente~ → *confirmado*

❌ NÃO use emojis em excesso
❌ NÃO use caracteres especiais desnecessários como /, \, |, #, @
❌ NÃO use indentação (espaços/tabs no início)
❌ NÃO use listas aninhadas
❌ Evite símbolos decorativos ou caracteres repetidos (===, ---, ***)

---

TOM DE FALA:
- Amigável, profissional e empático
- Linguagem natural (nada robótica)
- Explicações curtas e úteis
- Mostre proatividade ("Quer que eu faça isso por você?")"""

        prompts.append({"role": "system", "content": prompt_base})

        # 3. Prompt Específico da Categoria
        prompt_categoria = self._obter_prompt_categoria(categoria)
        prompts.append({"role": "system", "content": prompt_categoria})

        # 4. Lembrete Final
        lembrete_final = """LEMBRETE FINAL:

Sua resposta deve estar 100% compatível com o formato do WhatsApp descrito acima.

Use formatação (*negrito*, _itálico_, ~tachado~, ```código```) de forma inteligente e apenas quando necessário.

Use formato "chave: valor" para dados estruturados.

Mantenha respostas limpas, sem excesso de símbolos ou emojis.

---

RESUMO DO SEU PAPEL:

Você é a MoniqueBOT, assistente integrada ao WhatsApp que ajuda usuários com APIs e ferramentas de forma natural e empática. Suas respostas devem ser limpas e diretas, respeitando a língua do usuário, usando formatação do WhatsApp (*negrito*, _itálico_, ~tachado~, ```código```) apenas quando agregar valor real à comunicação e visualização das informações passadas por você. Evite emojis excessivos e caracteres especiais, utilize esses apenas quando necessário. Adapte seu estilo conforme a categoria da mensagem: seja técnico e detalhado para SYSTEM e USER, objetivo e conversacional para MESSAGES, e sempre solicite esclarecimentos quando houver ambiguidade (UNCLEAR). Seu tom deve ser profissional, humano e proativo, oferecendo ajuda de forma clara sem soar robótico."""

        prompts.append({"role": "system", "content": lembrete_final})

        return prompts, scope_detectadas

    def _obter_prompt_categoria(self, categoria: str) -> str:
        """
        Retorna o prompt específico para cada categoria.

        Args:
            categoria: Categoria da mensagem

        Returns:
            String com o prompt específico
        """
        if categoria == "system":
            return """CATEGORIA: SYSTEM

Função: lidar com comandos internos, configurações, controle ou manutenção do próprio sistema Monique, ou ações que dependem de integrações externas (APIs como Google, Spotify, etc.).

COMPORTAMENTO:
1. Confirme que entendeu a solicitação do usuário
2. Explique resumidamente o que será feito
3. Peça confirmação antes de executar, se necessário
4. Especifique claramente quais dados ou permissões precisa

FORMATO DE RESPOSTA:
Use estrutura clara com formato "chave: valor" quando aplicável:

1. Entendi sua solicitação
Breve confirmação do que foi pedido.

2. O que vou fazer
Explicação clara da ação.

3. Preciso de você
tipo: autorização
dados necessários: [lista]
prazo: [tempo estimado]

Posso prosseguir?"""

        elif categoria == "user":
            return """CATEGORIA: USER

Função: mensagens complexas ou longas que requerem resposta detalhada e estruturada.

COMPORTAMENTO:
1. Demonstre que entendeu a mensagem com 1-2 perguntas (se necessário)
2. Estruture em tópicos numerados
3. Use formato "chave: valor" para informações estruturadas
4. Dê exemplos práticos se possível
5. Seja detalhado, mas sem ser prolixo
6. Termine oferecendo ajuda ou próxima ação

FORMATO DE RESPOSTA:
Use estrutura numerada:

1. Título ou ideia principal
Explicação do ponto.

2. Segundo ponto
Explicação do segundo ponto.

Quando apresentar dados:
item: descrição
status: valor
resultado: valor

Conclusão ou pergunta final."""

        elif categoria == "messages":
            return """CATEGORIA: MESSAGES

Função: mensagens contextuais, conversacionais, ou de acompanhamento. Perguntas diretas e objetivas que não exigem ação técnica imediata.

COMPORTAMENTO:
1. Seja direto e claro
2. Use 2 a 4 frases curtas
3. Use linguagem simples e próxima
4. Ofereça uma continuação ou pergunta leve

FORMATO DE RESPOSTA:
Use resposta objetiva:

Ponto - Explicação curta
Ponto - Explicação curta

Pergunta de encerramento."""

        elif categoria == "unclear":
            return """CATEGORIA: UNCLEAR

Função: quando a mensagem é ambígua, incompleta ou imprecisa. O sistema não deve tomar decisão automática — deve pedir esclarecimento.

COMPORTAMENTO:
1. Reconheça educadamente que não entendeu completamente
2. Identifique o que está confuso ou faltando
3. Faça perguntas específicas para esclarecer
4. Ofereça opções ou exemplos para ajudar o usuário
5. Mantenha o tom amigável e prestativo

FORMATO DE RESPOSTA:
Use resposta objetiva:

Entendi que você quer [resumo do que entendeu], mas preciso esclarecer alguns pontos:

Pergunta específica 1?
Pergunta específica 2?

Ou você pode me dar um exemplo do que precisa?"""

        else:
            # Fallback genérico
            return """CATEGORIA: GERAL

COMPORTAMENTO:
1. Responda de forma natural e amigável
2. Use formatação adequada para WhatsApp
3. Seja claro e direto

Como posso ajudar mais?"""

    def _selecionar_modelo_ia(self, categoria: str) -> str:
        """
        Seleciona o modelo de IA mais apropriado baseado na categoria da mensagem.

        Usando gpt-4o (mesmo modelo do portal ChatGPT) para máxima qualidade.

        Args:
            categoria: Categoria da mensagem

        Returns:
            Nome do modelo a ser usado
        """
        modelo_customizado = self.contexto.get("model")
        if modelo_customizado:
            return modelo_customizado

        # Usar gpt-4o (mesmo do portal ChatGPT) para todas as categorias
        return "gpt-4o"

    def _calcular_parametros_da_ia(self, categoria: str) -> Dict[str, Any]:
        """
        Calcula parâmetros dinâmicos (temperature, max_tokens) baseados na categoria.

        Valores otimizados para cada tipo de interação:
        - MESSAGES: Temperature 1.0 (padrão ChatGPT), respostas naturais
        - SYSTEM: Temperature 0.7 (confirmações precisas mas amigáveis)
        - USER: Temperature 1.0 (explicações criativas como ChatGPT)
        - UNCLEAR: Temperature 0.8 (perguntas claras e estruturadas)

        Args:
            categoria: Categoria da mensagem

        Returns:
            Dicionário com parâmetros (temperature, max_tokens)
        """
        temp_base = float(self.contexto.get("temperature", 1.0))

        if categoria == "messages":
            # Perguntas diretas: naturais e conversacionais (padrão ChatGPT)
            return {"temperature": min(temp_base, 1.0), "max_tokens": 800}
        elif categoria == "system":
            # Integrações: precisas mas amigáveis
            return {"temperature": min(temp_base, 0.7), "max_tokens": 1200}
        elif categoria == "unclear":
            # Esclarecimentos: claras e estruturadas
            return {"temperature": min(temp_base, 0.8), "max_tokens": 600}
        else:  # user
            # Conversas complexas: criativas como ChatGPT
            return {"temperature": min(temp_base, 1.0), "max_tokens": 2000}

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