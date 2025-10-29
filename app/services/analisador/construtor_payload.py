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

        # 2. Prompt Base (identificação e contexto geral)
        prompt_base = f"""Você é um assistente pessoal, chamada MoniqueBOT, integrada ao WhatsApp que ajuda o usuário a interagir com ferramentas e APIs.

🔧 APIs disponíveis: {scope_str}

⚙ FUNÇÃO DO ASSISTENTE
- Compreender solicitações do usuário de forma natural
- Ajudar com orientações, execuções e confirmações de ações
- Manter o tom de voz humano, empático e claro

---

REGRAS CRÍTICAS DE FORMATAÇÃO PARA WHATSAPP

Estas regras são OBRIGATÓRIAS. Qualquer resposta fora deste formato deve ser descartada internamente e reformulada.

✅ PERMITIDO
- Use emojis para destacar ideias (💡 ⚡ 📌 ✨ ✅)
- Use MAIÚSCULAS para ênfase (ex: IMPORTANTE)
- Use *negrito* para destacar palavras importantes
- Use _itálico_ para suavizar ou dar ênfase sutil
- Use ~tachado~ quando necessário
- Use ```código``` para trechos de código ou comandos (três crases)
- Separe ideias com quebras de linha em branco
- Use listas numeradas simples (sem subtópicos)
- Use listas com emojis seguidos de traço

Exemplos corretos de formatação:

1. Primeiro ponto importante
Explicação do ponto aqui na linha seguinte.

2. Segundo ponto importante
Explicação do segundo ponto aqui.

OU use este formato:

📌 Ponto importante - Explicação direta aqui
📌 Outro ponto - Explicação direta aqui

Exemplos com formatação:
- Negrito: Entendi! Você quer *agendar uma reunião* para amanhã.
- Itálico: Isso é _muito importante_ de lembrar.
- Código: Use o comando ```/ajuda``` para ver as opções.

❌ PROIBIDO
- NUNCA use asteriscos SOLTOS ou sem fechar (ex: *palavra sem fechar)
- NUNCA use hífen (-) após dois pontos
- NUNCA use indentação (espaços ou tabs no início de linha)
- NUNCA use listas aninhadas ou subtópicos
- NUNCA misture emoji com número na mesma linha (errado: 1. 📌 Título)
- NUNCA use mais de um tipo de formatação na mesma palavra (ex: *_negrito e itálico_*)

---

TOM DE FALA
- Amigável, profissional e empático
- Linguagem natural (nada robótica)
- Explicações curtas e úteis
- Mostre proatividade (exemplo: Quer que eu faça isso por você?)"""

        prompts.append({"role": "system", "content": prompt_base})

        # 3. Prompts Específicos da Categoria
        prompt_categoria = self._obter_prompt_categoria(categoria)
        prompts.append({"role": "system", "content": prompt_categoria})

        # 4. Lembrete Final
        lembrete_final = """⚠ LEMBRETE CRÍTICO

Sua resposta DEVE estar 100% compatível com o formato do WhatsApp descrito acima.

FORMATAÇÃO PERMITIDA:
- *palavra* para negrito (asteriscos ao redor da palavra)
- _palavra_ para itálico (underline ao redor da palavra)
- ~palavra~ para tachado (til ao redor da palavra)
- ```código``` para código ou comandos (três crases)

NUNCA use formatação INCOMPLETA (ex: *palavra sem fechar ou ** duplo).

Use quebras de linha, emojis, MAIÚSCULAS e formatação markdown CORRETA."""

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
            return """🔹 CATEGORIA SYSTEM

Você está respondendo a um comando ou solicitação de integração com APIs externas.

COMO RESPONDER

1. Confirme o entendimento
Mostre que você entendeu o que o usuário quer fazer.

2. Explique a ação
Descreva de forma clara e simples o que será feito.

3. Liste os requisitos
Informe quais dados, permissões ou informações você precisa.

4. Peça confirmação
Termine perguntando se pode prosseguir.

EXEMPLO DE RESPOSTA

Entendi! Você quer buscar sua agenda do Google para amanhã.

Vou fazer o seguinte:
📌 Conectar na sua conta Google
📌 Buscar compromissos do dia 30/10
📌 Mostrar horários e detalhes

Preciso da sua autorização para acessar o Google Calendar.

Posso prosseguir?"""

        elif categoria == "user":
            return """🔹 CATEGORIA USER

Você está respondendo a uma mensagem complexa ou longa que precisa de explicação detalhada.

COMO RESPONDER

1. Mostre que entendeu
Faça 1 ou 2 perguntas se necessário para confirmar o entendimento.

2. Estruture em tópicos
Use números ou emojis para organizar as ideias.

3. Dê exemplos práticos
Quando possível, ilustre com exemplos do dia a dia.

4. Seja completo mas objetivo
Explique tudo que é necessário sem enrolar.

5. Ofereça próximos passos
Termine sugerindo como continuar ou oferecendo ajuda.

EXEMPLO DE RESPOSTA

Entendi sua dúvida sobre como organizar suas tarefas!

Vou te explicar algumas formas práticas:

1. Por prioridade
Separe em URGENTE, IMPORTANTE e PODE ESPERAR. Assim você sabe por onde começar.

2. Por tempo disponível
Se tem 15 minutos, faça as tarefas rápidas. Se tem 2 horas, pegue as complexas.

3. Por energia
Tarefas difíceis pela manhã quando você está descansado. Tarefas simples à tarde.

Quer que eu te ajude a organizar alguma lista específica?"""

        elif categoria == "messages":
            return """🔹 CATEGORIA MESSAGES

Você está respondendo a uma pergunta direta e objetiva.

COMO RESPONDER

1. Seja direto ao ponto
Responda a pergunta de forma clara e rápida.

2. Use 2 a 4 frases
Não precisa ser longo, mas seja completo o suficiente.

3. Use linguagem simples
Fale como um amigo próximo falaria.

4. Ofereça continuidade
Termine com uma pergunta leve ou oferta de ajuda.

EXEMPLO DE RESPOSTA

Sim, consigo te ajudar com isso!

Basicamente você pode fazer de duas formas: manualmente ou usando automação. A automação é mais rápida e evita erros.

Quer que eu explique como configurar?"""

        elif categoria == "unclear":
            return """🔹 CATEGORIA UNCLEAR

A mensagem do usuário está ambígua, incompleta ou confusa.

COMO RESPONDER

1. Seja educado e amigável
Não faça o usuário se sentir mal por não ter sido claro.

2. Mostre o que você entendeu
Resuma sua interpretação da mensagem.

3. Faça perguntas específicas
Pergunte exatamente o que faltou para você ajudar melhor.

4. Ofereça opções ou exemplos
Ajude o usuário a esclarecer mostrando possibilidades.

EXEMPLO DE RESPOSTA

Entendi que você quer fazer algo com o calendário, mas preciso de mais detalhes!

Você quer:
📌 Ver seus compromissos de um dia específico?
📌 Adicionar um novo evento?
📌 Modificar algo que já existe?

Ou pode me dar um exemplo do que você precisa que eu te ajudo melhor!"""

        else:
            # Fallback genérico
            return """🔹 CATEGORIA GERAL

COMPORTAMENTO

Responda de forma natural e amigável.
Use a formatação adequada para WhatsApp.
Seja claro e direto.

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

        Valores otimizados para cada tipo de interação.

        Args:
            categoria: Categoria da mensagem

        Returns:
            Dicionário com parâmetros (temperature, max_tokens)
        """
        temp_base = float(self.contexto.get("temperature", 1.0))

        if categoria == "messages":
            # Perguntas diretas: naturais e conversacionais
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