"""
Módulo principal que orquestra todo o processo de análise de mensagens.
"""

import time
from typing import Any, Dict
from app.core.config import logger
from .normalizador import normalizar_texto
from .gerenciador_cache import GerenciadorDeCache
from .classificador import Classificador
from .construtor_payload import ConstrutorDePayload


class AnalisadorDeMensagem:
    """
    Classe responsável por analisar, classificar e preparar mensagens para a IA.

    Esta classe orquestra todos os componentes para:
    - Extrair e normalizar mensagens
    - Classificar mensagens em categorias (system, user, messages)
    - Detectar necessidade de integrações (scopes)
    - Construir payloads otimizados para OpenAI
    - Gerenciar cache e métricas de performance
    """

    def __init__(self, payload_da_requisicao: Dict[str, Any]):
        """
        Inicializa o analisador com o payload da requisição.

        Args:
            payload_da_requisicao: Payload completo da requisição HTTP
        """
        self.payload_original = payload_da_requisicao or {}
        self.contexto = self.payload_original.get("ctx", {})
        self.latencias = {}

    async def processar_mensagem(self) -> Dict[str, Any]:
        """
        Processa a mensagem com medição de latência em cada etapa.
        Orquestra todos os componentes do analisador.

        Returns:
            Dicionário com resultado completo do processamento
        """
        tempo_inicio_total = time.time()

        # Passo 1: Extrair a mensagem do usuário
        t0 = time.time()
        mensagem_usuario = self._extrair_mensagem_do_payload()
        self.latencias["extracao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 2: Validar entrada
        if not mensagem_usuario:
            return self._construir_payload_de_erro_para_entrada_vazia()

        # Passo 3: Verificar cache
        t0 = time.time()
        cache_key = GerenciadorDeCache.gerar_cache_key(mensagem_usuario)
        resultado_cacheado = GerenciadorDeCache.obter_do_cache(cache_key)
        self.latencias["cache_lookup_ms"] = round((time.time() - t0) * 1000, 2)

        if resultado_cacheado:
            logger.info(
                "Classificação recuperada do cache",
                log_type="cache_hit",
                cache_key=cache_key[:20],
                latency_cache_lookup_ms=self.latencias["cache_lookup_ms"],
            )
            return resultado_cacheado

        # Passo 4: Normalizar texto
        t0 = time.time()
        try:
            texto_normalizado = normalizar_texto(mensagem_usuario)
            if not texto_normalizado:
                logger.error(
                    "Falha na normalização: texto normalizado está vazio",
                    log_type="normalization_error",
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "NORMALIZATION_FAILED",
                    "Erro ao normalizar a mensagem. Tente novamente.",
                    mensagem_usuario,
                )
        except Exception as e:
            logger.error(
                "Exceção durante normalização",
                log_type="normalization_exception",
                error=str(e),
                original_message=mensagem_usuario[:100],
            )
            return self._construir_payload_de_erro_classificacao(
                "NORMALIZATION_EXCEPTION",
                f"Erro ao processar a mensagem: {str(e)}",
                mensagem_usuario,
            )
        
        self.latencias["normalizacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 5: Classificar mensagem
        t0 = time.time()
        try:
            resultado_classificacao = Classificador.determinar_categoria(
                mensagem_usuario, texto_normalizado
            )
            
            if not resultado_classificacao or len(resultado_classificacao) != 2:
                logger.error(
                    "Classificação retornou valor inválido",
                    log_type="classification_invalid_return",
                    resultado=resultado_classificacao,
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "CLASSIFICATION_INVALID_RETURN",
                    "Erro ao classificar a mensagem. Tente reformular sua pergunta.",
                    mensagem_usuario,
                )
            
            categoria, motivos = resultado_classificacao
            
            categorias_validas = ["system", "messages", "user", "unclear"]
            if not categoria or categoria not in categorias_validas:
                logger.error(
                    "Categoria retornada é inválida",
                    log_type="classification_invalid_category",
                    categoria=categoria,
                    categorias_validas=categorias_validas,
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "CLASSIFICATION_INVALID_CATEGORY",
                    f"Erro na classificação: categoria '{categoria}' inválida. Tente reformular sua pergunta.",
                    mensagem_usuario,
                )
            
            if not isinstance(motivos, list):
                logger.error(
                    "Motivos retornados não é uma lista",
                    log_type="classification_invalid_reasons",
                    motivos=motivos,
                    tipo_motivos=type(motivos),
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "CLASSIFICATION_INVALID_REASONS",
                    "Erro ao processar a classificação. Tente novamente.",
                    mensagem_usuario,
                )
                
        except Exception as e:
            logger.error(
                "Exceção durante classificação",
                log_type="classification_exception",
                error=str(e),
                error_type=type(e).__name__,
                original_message=mensagem_usuario[:100],
            )
            return self._construir_payload_de_erro_classificacao(
                "CLASSIFICATION_EXCEPTION",
                f"Erro ao classificar a mensagem: {str(e)}",
                mensagem_usuario,
            )
        
        self.latencias["classificacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 6: Construir payload para IA
        t0 = time.time()
        try:
            construtor = ConstrutorDePayload(self.contexto, self.payload_original)
            resultado_payload = construtor.construir_payload(
                categoria=categoria,
                mensagem_original=mensagem_usuario,
                texto_normalizado=texto_normalizado,
            )
            
            if not resultado_payload or len(resultado_payload) != 2:
                logger.error(
                    "Construtor de payload retornou valor inválido",
                    log_type="payload_construction_invalid_return",
                    resultado=resultado_payload,
                    categoria=categoria,
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "PAYLOAD_CONSTRUCTION_INVALID_RETURN",
                    "Erro ao construir payload para a IA. Tente novamente.",
                    mensagem_usuario,
                )
            
            payload_para_ia, scope = resultado_payload
            
            if not isinstance(payload_para_ia, dict) or not payload_para_ia:
                logger.error(
                    "Payload para IA é inválido ou vazio",
                    log_type="payload_construction_invalid_payload",
                    payload_tipo=type(payload_para_ia),
                    payload_vazio=not payload_para_ia,
                    categoria=categoria,
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "PAYLOAD_CONSTRUCTION_INVALID_PAYLOAD",
                    "Erro ao preparar resposta da IA. Tente novamente.",
                    mensagem_usuario,
                )
            
            if not isinstance(scope, list):
                logger.error(
                    "Scope retornado não é uma lista",
                    log_type="payload_construction_invalid_scope",
                    scope_tipo=type(scope),
                    categoria=categoria,
                    original_message=mensagem_usuario[:100],
                )
                return self._construir_payload_de_erro_classificacao(
                    "PAYLOAD_CONSTRUCTION_INVALID_SCOPE",
                    "Erro ao detectar integrações necessárias. Tente novamente.",
                    mensagem_usuario,
                )
                
        except Exception as e:
            logger.error(
                "Exceção durante construção de payload",
                log_type="payload_construction_exception",
                error=str(e),
                error_type=type(e).__name__,
                categoria=categoria,
                original_message=mensagem_usuario[:100],
            )
            return self._construir_payload_de_erro_classificacao(
                "PAYLOAD_CONSTRUCTION_EXCEPTION",
                f"Erro ao preparar resposta: {str(e)}",
                mensagem_usuario,
            )
        
        self.latencias["construcao_payload_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 6.1: Validação inteligente - Reclassificar se SYSTEM sem SCOPE
        if categoria == "system" and not scope:
            logger.info(
                "Reclassificando mensagem: detectada como SYSTEM mas sem scope detectado",
                log_type="reclassification",
                original_category="system",
                message_length=len(mensagem_usuario),
            )

            # Reclassificar baseado no tamanho da mensagem
            if len(mensagem_usuario.split()) <= 15:
                categoria = "messages"
            else:
                categoria = "user"

            # Reconstruir payload com a nova categoria
            payload_para_ia, scope = construtor.construir_payload(
                categoria=categoria,
                mensagem_original=mensagem_usuario,
                texto_normalizado=texto_normalizado,
            )

            motivos.append(
                f"Reclassificado de 'system' para '{categoria}' (sem scope detectado)"
            )

        # Tempo total
        tempo_total_ms = round((time.time() - tempo_inicio_total) * 1000, 2)
        self.latencias["total_ms"] = tempo_total_ms

        # Passo 7: Construir resposta final
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
            "performance": self.latencias,
        }

        # Salvar no cache
        GerenciadorDeCache.salvar_no_cache(cache_key, resposta_final)

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

    def _extrair_mensagem_do_payload(self) -> str:
        """
        Extrai e limpa a mensagem do payload.

        Returns:
            Mensagem extraída e limpa
        """
        mensagem = self.payload_original.get("message", "")
        return str(mensagem).strip()

    def _construir_payload_de_erro_para_entrada_vazia(self) -> Dict[str, Any]:
        """
        Constrói um payload de erro para quando a mensagem está vazia.

        Returns:
            Dicionário com mensagem de erro
        """
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

    def _construir_payload_de_erro_classificacao(
        self, codigo_erro: str, mensagem_erro: str, mensagem_original: str
    ) -> Dict[str, Any]:
        """
        Constrói um payload de erro estruturado quando há falha na classificação
        ou processamento da mensagem.

        Args:
            codigo_erro: Código do erro (ex: "CLASSIFICATION_EXCEPTION")
            mensagem_erro: Mensagem de erro amigável para o usuário
            mensagem_original: Mensagem original do usuário

        Returns:
            Dicionário com payload de erro estruturado
        """
        tempo_total_ms = round(
            sum(self.latencias.values()) * 1000, 2
        ) if self.latencias else 0

        payload_erro = {
            **self.payload_original,
            "error": codigo_erro,
            "mensagem_completa": mensagem_original,
            "texto_normalizado": mensagem_original.lower() if mensagem_original else "",
            "openaiPayload": {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um assistente prestativo. O usuário encontrou um erro ao processar sua mensagem.",
                    },
                    {
                        "role": "user",
                        "content": mensagem_original or "Mensagem não fornecida",
                    },
                    {
                        "role": "assistant",
                        "content": f"Desculpe, encontrei um problema ao processar sua mensagem: {mensagem_erro}",
                    },
                ],
                "temperature": 0.7,
                "max_tokens": 400,
            },
            "classification": {
                "bucket": "unclear",
                "reasons": [f"Erro durante classificação: {codigo_erro}"],
                "scope": [],
            },
            "performance": {
                **self.latencias,
                "total_ms": tempo_total_ms,
            },
        }

        logger.error(
            "Payload de erro construído",
            log_type="error_payload_created",
            codigo_erro=codigo_erro,
            mensagem_original_length=len(mensagem_original) if mensagem_original else 0,
        )

        return payload_erro
