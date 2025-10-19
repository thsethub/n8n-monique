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
        texto_normalizado = normalizar_texto(mensagem_usuario)
        self.latencias["normalizacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 5: Classificar mensagem
        t0 = time.time()
        categoria, motivos = Classificador.determinar_categoria(
            mensagem_usuario, texto_normalizado
        )
        self.latencias["classificacao_ms"] = round((time.time() - t0) * 1000, 2)

        # Passo 6: Construir payload para IA
        t0 = time.time()
        construtor = ConstrutorDePayload(self.contexto, self.payload_original)
        payload_para_ia, scope = construtor.construir_payload(
            categoria=categoria,
            mensagem_original=mensagem_usuario,
            texto_normalizado=texto_normalizado,
        )
        self.latencias["construcao_payload_ms"] = round((time.time() - t0) * 1000, 2)

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
