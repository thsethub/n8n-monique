import hashlib
import logging
import re
import sys
import time
from collections import defaultdict
from functools import lru_cache
from typing import Any, Dict, List, Set, Tuple

import structlog
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from unidecode import unidecode

# Configuração do Logging Estruturado com Structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
logger = structlog.get_logger()

# Configuração do FastAPI
app = FastAPI(
    title="Serviço de Análise e Preparação de Mensagens para IA",
    description="Uma API que recebe uma mensagem, a classifica e prepara um payload otimizado para a IA.",
)

# Adiciona middleware de compressão GZip para reduzir latência de transferência
app.add_middleware(GZipMiddleware, minimum_size=500)

# --- OTIMIZAÇÕES DE PERFORMANCE ---

# Cache em memória para classificações (TTL de 1 hora)
# Reduz drasticamente tempo de resposta para mensagens similares
classificacao_cache = TTLCache(maxsize=1000, ttl=3600)

# Contador de métricas globais
metricas = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_latency_ms": 0.0,
    "error_count": 0,
}

# Cache de scopes para padrões conhecidos (evita reprocessamento)
SCOPE_CACHE: Dict[str, List[str]] = {
    "agendar reuniao": ["https://www.googleapis.com/auth/calendar"],
    "criar evento": ["https://www.googleapis.com/auth/calendar"],
    "marcar compromisso": ["https://www.googleapis.com/auth/calendar"],
    "enviar email": ["https://www.googleapis.com/auth/gmail.modify"],
    "mandar mensagem gmail": ["https://www.googleapis.com/auth/gmail.modify"],
    "criar planilha": ["https://www.googleapis.com/auth/spreadsheets"],
    "abrir documento": ["https://www.googleapis.com/auth/drive"],
    "gerar boleto": ["boleto"],
}

# Pré-compilação de regex para performance (evita recompilar a cada request)
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


# --- Middleware de Monitoramento de Latência ---
@app.middleware("http")
async def log_request_latency_middleware(request: Request, call_next):
    """
    Middleware que mede o tempo de processamento de cada requisição
    e registra logs estruturados com métricas de performance.
    """
    start_time = time.time()
    metricas["total_requests"] += 1

    # Captura informações da requisição
    method = request.method
    path = request.url.path
    user_agent = request.headers.get("user-agent", "unknown")
    content_length = request.headers.get("content-length", "0")

    try:
        # Processa a requisição
        response = await call_next(request)

        # Calcula métricas de performance
        duration_ms = round((time.time() - start_time) * 1000, 2)
        metricas["total_latency_ms"] += duration_ms

        # Log estruturado com todas as métricas importantes para o dashboard
        logger.info(
            "Requisição processada com sucesso",
            log_type="api_performance",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_size_bytes=int(content_length) if content_length.isdigit() else 0,
            user_agent=user_agent[:50],  # Limita o tamanho para não poluir os logs
        )

        # Adiciona o header com a duração na resposta (útil para debugging)
        response.headers["X-Process-Time"] = str(duration_ms)

        return response

    except Exception as e:
        # Em caso de erro, ainda registra o tempo de processamento
        duration_ms = round((time.time() - start_time) * 1000, 2)
        metricas["error_count"] += 1

        logger.error(
            "Erro durante processamento da requisição",
            log_type="api_performance",
            method=method,
            path=path,
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e)[:100],  # Limita a mensagem de erro
        )

        # Re-levanta a exceção para que o FastAPI a trate normalmente
        raise


# Constantes de Configuração
# Palavras-chave que indicam a necessidade de integrações ou ferramentas.
# Usar um Set (conjunto) torna a busca por palavras muito mais rápida.
PALAVRAS_CHAVE_DE_SISTEMA: Set[str] = {
    # Documentos e arquivos
    "documento",
    "document",
    "doc",
    "planilha",
    "spreadsheet",
    "sheet",
    "tabela",
    "arquivo",
    "file",
    "pdf",
    "drive",
    "armazenamento",
    "storage",
    # Calendário e organização pessoal
    "calendario",
    "agenda",
    "evento",
    "compromisso",
    "contatos",
    "contacts",
    "nota",
    "notes",
    # Reuniões
    "reuniao",
    "meeting",
    "encontro",
    # Integrações e compartilhamento
    "compartilhar",
    "share",
    "sincronizar",
    "sync",
    "integracao",
    "api",
    "oauth",
    "google",
    "gmail",
    "email",
    "e-mail",
    # Financeiro
    "boleto",
    "fatura",
    "cobranca",
    "pagamento",
}


class AnalisadorDeMensagem:
    def __init__(self, payload_da_requisicao: Dict[str, Any]):
        self.payload_original = payload_da_requisicao or {}
        self.contexto = self.payload_original.get("ctx", {})
        
        # Dicionário para métricas internas de latência por etapa
        self.latencias = {}

    # Etapa 1: Orquestração Principal com medição de latência

    async def processar_mensagem(self) -> Dict[str, Any]:
        """
        Processa a mensagem com medição de latência em cada etapa.
        Agora é assíncrono para melhor performance em produção.
        """
        tempo_inicio_total = time.time()

        # Passo 1: Extrair a mensagem do usuário do payload.
        t0 = time.time()
        mensagem_usuario = self._extrair_mensagem_do_payload()
        self.latencias["extracao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 2: Se não houver mensagem, retornar um erro padrão.
        if not mensagem_usuario:
            return self._construir_payload_de_erro_para_entrada_vazia()

        # Passo 3: Verificar cache primeiro (otimização crítica)
        t0 = time.time()
        cache_key = self._gerar_cache_key(mensagem_usuario)
        resultado_cacheado = classificacao_cache.get(cache_key)
        self.latencias["cache_lookup_ms"] = round((time.time() - t0) * 1000, 2)
        
        if resultado_cacheado:
            metricas["cache_hits"] += 1
            logger.info(
                "Classificação recuperada do cache",
                log_type="cache_hit",
                cache_key=cache_key[:20],
                latency_cache_lookup_ms=self.latencias["cache_lookup_ms"],
            )
            return resultado_cacheado

        metricas["cache_misses"] += 1

        # Passo 4: Limpar e padronizar o texto para análise.
        t0 = time.time()
        texto_normalizado = self._normalizar_texto(mensagem_usuario)
        self.latencias["normalizacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 5: Classificar a mensagem em uma categoria (bucket).
        t0 = time.time()
        categoria, motivos = self._determinar_categoria_da_mensagem(
            mensagem_usuario, texto_normalizado
        )
        self.latencias["classificacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 6: Montar o payload final para a IA com base na categoria.
        t0 = time.time()
        payload_para_ia, scope = self._construir_payload_para_ia(
            categoria=categoria,
            mensagem_original=mensagem_usuario,
            texto_normalizado=texto_normalizado,
        )
        self.latencias["construcao_payload_ms"] = round((time.time() - t0) * 1000, 2)

        # Tempo total de processamento
        tempo_total_ms = round((time.time() - tempo_inicio_total) * 1000, 2)
        self.latencias["total_ms"] = tempo_total_ms

        # Passo 7: Construir e retornar a resposta final e completa.
        resposta_final = {
            **self.payload_original,
            "mensagem_completa": mensagem_usuario,
            "texto_normalizado": texto_normalizado,
            "openaiPayload": payload_para_ia,
            "classification": {
                "bucket": categoria,
                "reasons": motivos,
                "scope": scope,
            },
            "performance": self.latencias,  # Expõe métricas de performance
        }

        # Armazena no cache para futuras requisições
        classificacao_cache[cache_key] = resposta_final

        logger.info(
            "Mensagem processada com sucesso",
            log_type="preprocessing_result",
            classification_bucket=categoria,
            scope_found=scope,
            original_message_length=len(mensagem_usuario),
            model_used=payload_para_ia.get("model"),
            **{f"latency_step_{k}": v for k, v in self.latencias.items()},
        )

        return resposta_final
    
    def _gerar_cache_key(self, mensagem: str) -> str:
        """Gera uma chave de cache baseada no hash da mensagem normalizada."""
        mensagem_normalizada = self._normalizar_texto(mensagem)
        return hashlib.md5(mensagem_normalizada.encode()).hexdigest()

    # Etapa 2: Funções Auxiliares de Preparação

    def _extrair_mensagem_do_payload(self) -> str:
        mensagem = self.payload_original.get("message", "")
        # Garantimos que o valor seja uma string antes de remover espaços.
        return str(mensagem).strip()

    @lru_cache(maxsize=512)
    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto removendo acentos e convertendo para minúsculas.
        Usa LRU cache para evitar reprocessamento de textos idênticos.
        """
        texto_minusculo = texto.lower()
        texto_sem_acentos = unidecode(texto_minusculo)
        return texto_sem_acentos

    # Etapa 3: Funções de Análise e Classificação

    def _determinar_categoria_da_mensagem(
        self, mensagem_original: str, texto_normalizado: str
    ) -> Tuple[str, List[str]]:
        """
        Determina a categoria da mensagem (system, messages, user).
        Otimizado com buscas 'in' ao invés de regex onde possível.
        """
        
        # Prioridade 1: É um pedido que envolve sistemas/integrações?
        # Usa busca direta 'in' que é ~3x mais rápida que regex
        palavras_encontradas = [
            p for p in PALAVRAS_CHAVE_DE_SISTEMA 
            if p in texto_normalizado
        ]
        if palavras_encontradas:
            motivo = f"Palavras-chave de sistemas/APIs: {', '.join(palavras_encontradas[:6])}"
            return "system", [motivo]

        # Prioridade 2: É uma pergunta direta e objetiva?
        if self._e_pergunta_direta_e_objetiva(mensagem_original, texto_normalizado):
            return "messages", ["Pergunta direta/fechada detectada."]

        # Prioridade 3: É uma mensagem complexa ou pessoal?
        if self._e_mensagem_complexa_ou_pessoal(mensagem_original):
            return "user", ["Mensagem com necessidade de personalização/contexto."]

        # Se não se encaixar em nenhuma regra, decide pelo tamanho.
        if len(mensagem_original) < 60:
            return "messages", ["Curta e objetiva; sem necessidade clara de contexto."]
        else:
            return "user", ["Mensagem requer elaboração moderada."]

    def _e_pergunta_direta_e_objetiva(self, texto: str, texto_normalizado: str) -> bool:
        """
        Verifica se é uma pergunta direta usando regex pré-compilada.
        """
        e_curta_e_termina_com_interrogacao = len(texto) <= 80 and texto.endswith("?")

        # Usa regex pré-compilada (muito mais rápido)
        contem_termos_factuais = bool(REGEX_PERGUNTA_FACTUAL.search(texto_normalizado))

        return e_curta_e_termina_com_interrogacao or contem_termos_factuais

    def _e_mensagem_complexa_ou_pessoal(self, texto: str) -> bool:
        """
        Verifica complexidade da mensagem usando regex pré-compiladas.
        """
        e_longa = len(texto) > 160
        
        # Usa regex pré-compiladas
        usa_referencias_pessoais = bool(REGEX_REFERENCIAS_PESSOAIS.search(texto))
        pede_um_plano_ou_estrategia = bool(REGEX_PLANO_ESTRATEGIA.search(texto))
        tem_multiplas_frases = len(REGEX_MULTIPLAS_FRASES.findall(texto)) > 1

        return (
            e_longa
            or usa_referencias_pessoais
            or pede_um_plano_ou_estrategia
            or tem_multiplas_frases
        )

    # Etapa 4: Funções de Construção do Payload para a IA

    def _construir_payload_para_ia(
        self, categoria: str, mensagem_original: str, texto_normalizado: str
    ) -> Tuple[Dict[str, Any], List[str]]:

        idioma = self.contexto.get("lang") or self._determinar_idioma(mensagem_original)

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

        # Define o modelo baseado na categoria
        modelo_selecionado = self._selecionar_modelo_ia(categoria)

        payload_final = {
            "model": modelo_selecionado,
            "messages": mensagens,
            **parametros_dinamicos,  # Adiciona temperature e max_tokens
        }
        return payload_final, scope

    def _detectar_scopes_com_prioridade_contextual(self, texto_normalizado: str) -> List[str]:
        """
        Detecta scopes necessários considerando o contexto principal da mensagem.
        Prioriza a ação principal para evitar scopes desnecessários.
        Usa cache de padrões conhecidos para performance máxima.
        """
        # Verifica cache de padrões conhecidos primeiro (otimização crítica)
        for padrao, scopes in SCOPE_CACHE.items():
            if padrao in texto_normalizado:
                return scopes.copy()
        
        scope_detectadas = []
        
        # Verifica se há ações específicas de email (busca direta, sem regex)
        acoes_email = ["envie", "mande", "escreva", "responda", "encaminhe", "send", "reply", "forward"]
        tem_acao_email = any(acao in texto_normalizado for acao in acoes_email)
        tem_palavra_email = any(palavra in texto_normalizado for palavra in ["gmail", "email", "e-mail"])
        
        # Verifica se há ações específicas de calendário
        acoes_calendario = ["agende", "marque", "crie evento", "adicione evento", "schedule", "book"]
        tem_acao_calendario = any(acao in texto_normalizado for acao in acoes_calendario)
        tem_palavra_calendario = any(palavra in texto_normalizado for palavra in ["calendar", "agenda", "evento", "reuniao", "meeting"])
        
        # Verifica se há múltiplas intenções explícitas
        tem_multiplas_acoes = any(conector in texto_normalizado for conector in ["e depois", "tambem", "alem disso", "and then", "also"])
        
        # Se há clara intenção de email E calendário com conectores, inclui ambos
        if (tem_acao_email and tem_palavra_email) and (tem_acao_calendario or tem_palavra_calendario) and tem_multiplas_acoes:
            scope_detectadas.append("https://www.googleapis.com/auth/gmail.modify")
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
            return scope_detectadas
        
        # Se há clara intenção de email, prioriza apenas o scope de email
        if tem_acao_email and tem_palavra_email:
            scope_detectadas.append("https://www.googleapis.com/auth/gmail.modify")
            return scope_detectadas
        
        # Se há clara intenção de calendário, prioriza apenas o scope de calendário
        if tem_acao_calendario and (tem_palavra_calendario or "compromisso" in texto_normalizado):
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
            return scope_detectadas
        
        # Lógica tradicional para casos ambíguos (busca direta 'in', sem regex)
        if any(k in texto_normalizado for k in ["calendar", "agenda", "evento"]):
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
        elif "compromisso" in texto_normalizado and not tem_acao_email:
            scope_detectadas.append("https://www.googleapis.com/auth/calendar")
            
        if any(k in texto_normalizado for k in ["sheet", "planilha", "tabela", "spreadsheet"]):
            scope_detectadas.append("https://www.googleapis.com/auth/spreadsheets")
        if any(k in texto_normalizado for k in ["gmail", "email", "e-mail"]):
            scope_detectadas.append("https://www.googleapis.com/auth/gmail.modify")
        if any(k in texto_normalizado for k in ["drive", "documento", "document", "doc", "arquivo", "file"]):
            scope_detectadas.append("https://www.googleapis.com/auth/drive")
        if any(k in texto_normalizado for k in ["boleto", "fatura", "cobranca"]):
            scope_detectadas.append("boleto")
            
        return scope_detectadas

    def _criar_prompts_de_sistema(
        self, categoria: str, idioma: str, texto_normalizado: str
    ) -> Tuple[List[Dict[str, str]], List[str]]:

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
            # Detecta quais integrações podem ser necessárias com lógica de prioridade contextual
            scope_detectadas = self._detectar_scopes_com_prioridade_contextual(texto_normalizado)

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
                    "content": "Você é um assistente no WhatsApp, amigável e direto. Evite jargões. Se não souber algo, admita e sugira como verificar.",
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
        """
        # Permite override manual pelo contexto
        modelo_customizado = self.contexto.get("model")
        if modelo_customizado:
            return modelo_customizado

        # Seleção automática baseada na categoria
        if categoria == "messages":
            # Para perguntas diretas, usa o modelo mais rápido
            return "gpt-4o-mini"
        else:  # categoria == "user" ou "system"
            # Para mensagens complexas e integrações, usa o modelo padrão
            return "gpt-4.1-mini"

    def _calcular_parametros_da_ia(self, categoria: str) -> Dict[str, Any]:

        temp_base = float(self.contexto.get("temperature", 0.3))

        if categoria == "messages":
            # Para perguntas diretas, queremos respostas factuais e sem criatividade.
            return {"temperature": min(temp_base, 0.2), "max_tokens": 400}
        elif categoria == "system":
            # Para integrações, queremos um comportamento previsível.
            return {"temperature": min(temp_base, 0.3), "max_tokens": 900}
        else:  # user
            # Para pedidos complexos, permitimos um pouco mais de criatividade.
            return {"temperature": min(max(temp_base, 0.3), 0.6), "max_tokens": 900}

    def _obter_historico_da_conversa(self) -> List[Dict[str, str]]:
        """
        Obtém o histórico da conversa, limitado a 2-3 mensagens mais recentes.
        Reduz tokens e tempo de inferência do modelo.
        """
        historico = self.payload_original.get("history", [])
        if not isinstance(historico, list):
            return []

        # Filtra e formata o histórico para garantir que está correto
        historico_valido = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in historico
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        # OTIMIZADO: Retorna apenas as últimas 2-3 interações (antes eram 6)
        return historico_valido[-3:]

    def _determinar_idioma(self, texto: str) -> str:
        """
        Determina o idioma usando regex pré-compiladas.
        """
        # Usa regex pré-compiladas (muito mais rápido)
        tem_pt = bool(REGEX_PT_INDICADORES.search(texto)) or bool(REGEX_PT_PALAVRAS.search(texto))
        tem_en = bool(REGEX_EN_PALAVRAS.search(texto))

        return "en" if tem_en and not tem_pt else "pt"

    def _construir_payload_de_erro_para_entrada_vazia(self) -> Dict[str, Any]:

        return {
            **self.payload_original,
            "error": "EMPTY_INPUT",
            "openaiPayload": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Não recebi sua mensagem. Pode reenviar, por favor?",
                    }
                ]
            },
        }


# Endpoint da API

@app.post("/webhook", summary="Webhook para receber mensagens do WhatsApp")
async def webhook_whatsapp(
    from_number: str = Form(..., alias="from"),
    message: str = Form(...)
) -> JSONResponse:
    """
    Endpoint simplificado para receber mensagens via webhook (ngrok).
    Recebe 'from' (número) e 'message' via Form data.
    
    Exemplo de uso com curl:
    curl -X POST http://localhost:8181/webhook \
      -F "from=5511999999999" \
      -F "message=agendar reunião amanhã"
    """
    logger.info(
        "Webhook recebido",
        log_type="webhook",
        from_number=from_number,
        message_length=len(message)
    )
    
    # Converte para o formato esperado pelo preprocessador
    payload = {
        "message": message,
        "ctx": {
            "lang": "pt",
            "temperature": 0.3
        },
        "from": from_number,
        "history": []
    }
    
    # Processa a mensagem
    analisador = AnalisadorDeMensagem(payload)
    resultado_final = await analisador.processar_mensagem()
    
    # Adiciona informações do webhook
    resultado_final["webhook"] = {
        "from": from_number,
        "received_at": time.time()
    }
    
    logger.info(
        "Webhook processado",
        log_type="webhook_response",
        from_number=from_number,
        bucket=resultado_final.get("classification", {}).get("bucket")
    )
    
    return JSONResponse(content=resultado_final)


@app.post("/preprocess", summary="Processa e prepara uma mensagem para a IA")
async def rota_de_preprocessamento(payload: Dict[str, Any]) -> JSONResponse:
    """
    Endpoint otimizado com cache e medição de latência.
    Agora é completamente assíncrono para melhor performance.
    """
    if not payload:
        logger.warning("Recebido payload vazio.", log_type="request_validation")
        raise HTTPException(status_code=400, detail="O payload não pode ser vazio.")

    # 1. Cria o Analisador (O "Gerente") para cuidar do pedido.
    analisador = AnalisadorDeMensagem(payload)

    # 2. Pede para o Analisador processar a mensagem e preparar o resultado (assíncrono).
    resultado_final = await analisador.processar_mensagem()

    # 3. Retorna o resultado completo para o n8n.
    return JSONResponse(content=resultado_final)


# Endpoint de Health Check
@app.get("/health", summary="Verifica o status do serviço")
async def health_check():
    return {
        "status": "healthy",
        "service": "preproc-api",
        "version": "2.0.0",
        "timestamp": time.time(),
    }


# Endpoint de Métricas
@app.get("/metrics", summary="Retorna métricas de performance do serviço")
async def metrics_endpoint():
    """
    Expõe métricas importantes para monitoramento:
    - Total de requisições processadas
    - Cache hits/misses
    - Latência média
    - Taxa de erro
    """
    total_requests = metricas["total_requests"]
    cache_hits = metricas["cache_hits"]
    cache_misses = metricas["cache_misses"]
    
    # Calcula taxa de cache hit
    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    # Calcula latência média
    avg_latency_ms = (
        metricas["total_latency_ms"] / total_requests if total_requests > 0 else 0
    )
    
    # Calcula taxa de erro
    error_rate = (
        metricas["error_count"] / total_requests * 100 if total_requests > 0 else 0
    )
    
    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate_percent": round(cache_hit_rate, 2),
        "cache_size": len(classificacao_cache),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "error_count": metricas["error_count"],
        "error_rate_percent": round(error_rate, 2),
        "timestamp": time.time(),
    }
