"""
Microsserviço de Pré-processamento para IA

Este módulo implementa um serviço de análise e preparação de mensagens para modelos de IA.
Ele classifica mensagens em categorias (buckets), detecta necessidades de integração com 
APIs externas e otimiza prompts baseado no contexto da mensagem.

Autor: thsethub
Data: 2024
"""

import os
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
from unidecode import unidecode

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração do FastAPI ---
app = FastAPI(
    title="Serviço de Análise e Preparação de Mensagens para IA",
    description="Uma API que recebe uma mensagem, a classifica e prepara um payload otimizado para a IA.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Constantes de Configuração ---
# Palavras-chave que indicam a necessidade de integrações ou ferramentas.
# Usar um Set (conjunto) torna a busca por palavras muito mais rápida.
PALAVRAS_CHAVE_DE_SISTEMA: Set[str] = {
    # Documentos e arquivos
    "documento", "document", "doc", "planilha", "spreadsheet", "sheet", "tabela",
    "arquivo", "file", "pdf", "drive", "icloud", "armazenamento", "storage",
    # Calendário e organização pessoal
    "calendario", "agenda", "evento", "compromisso", "contatos", "contacts", "nota", "notes",
    # Reuniões
    "reuniao", "meeting", "encontro",
    # Integrações e compartilhamento
    "compartilhar", "share", "sincronizar", "sync", "integracao", "api", "oauth", "google", "apple",
    # Financeiro
    "boleto", "fatura", "cobranca", "pagamento"
}


class AnalisadorDeMensagem:
    """
    Classe principal responsável pela análise e processamento de mensagens.
    
    Esta classe implementa a lógica de classificação de mensagens em buckets
    (system, messages, user), detecta necessidades de integrações e prepara
    payloads otimizados para modelos de IA.
    
    Attributes:
        payload_original (Dict[str, Any]): Payload completo recebido na requisição
        contexto (Dict[str, Any]): Contexto extraído do payload para configurações
    """

    def __init__(self, payload_da_requisicao: Dict[str, Any]):
        """
        Inicializa o analisador com o payload da requisição.
        
        Args:
            payload_da_requisicao: Dicionário contendo a mensagem e contexto
        """
        self.payload_original = payload_da_requisicao or {}
        self.contexto = self.payload_original.get("ctx", {})

    # --- Etapa 1: Orquestração Principal ---

    def processar_mensagem(self) -> Dict[str, Any]:
        """
        Método principal que orquestra todo o processamento da mensagem.
        
        Executa o fluxo completo de análise:
        1. Extrai mensagem do payload
        2. Normaliza o texto
        3. Classifica em bucket (system/messages/user)
        4. Detecta integrações necessárias
        5. Constrói payload otimizado para IA
        
        Returns:
            Dict contendo a mensagem processada, classificação e payload para IA
            
        Example:
            >>> analisador = AnalisadorDeMensagem({"message": "Qual a capital do Brasil?"})
            >>> resultado = analisador.processar_mensagem()
            >>> print(resultado["classification"]["bucket"])
            "messages"
        """

        # Passo 1: Extrair a mensagem do usuário do payload.
        mensagem_usuario = self._extrair_mensagem_do_payload()

        # Passo 2: Se não houver mensagem, retornar um erro padrão.
        if not mensagem_usuario:
            return self._construir_payload_de_erro_para_entrada_vazia()

        # Passo 3: Limpar e padronizar o texto para análise.
        texto_normalizado = self._normalizar_texto(mensagem_usuario)
        
        # Passo 4: Classificar a mensagem em uma categoria (bucket).
        categoria, motivos = self._determinar_categoria_da_mensagem(mensagem_usuario, texto_normalizado)

        # Passo 5: Montar o payload final para a IA com base na categoria.
        payload_para_ia, integrações = self._construir_payload_para_ia(
            categoria=categoria,
            mensagem_original=mensagem_usuario,
            texto_normalizado=texto_normalizado
        )

        # Passo 6: Construir e retornar a resposta final e completa.
        return {
            **self.payload_original,
            "mensagem_completa": mensagem_usuario,
            "texto_normalizado": texto_normalizado,
            "openaiPayload": payload_para_ia,
            "classification": {
                "bucket": categoria,
                "reasons": motivos,
                "integrations": integrações,
            },
        }

    # --- Etapa 2: Funções Auxiliares de Preparação ---

    def _extrair_mensagem_do_payload(self) -> str:
        """
        Extrai e limpa a mensagem do payload original.
        
        Returns:
            string: Mensagem do usuário limpa e sem espaços extras
        """
 
        mensagem = self.payload_original.get("message", "")
        
        # Garantimos que o valor seja uma string antes de remover espaços.
        return str(mensagem).strip()

    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto para análise removendo acentos e convertendo para minúsculas.
        
        Args:
            texto: Texto a ser normalizado
            
        Returns:
            string: Texto normalizado sem acentos e em minúsculas
            
        Example:
            >>> self._normalizar_texto("Reunião às 15h")
            "reuniao as 15h"
        """

        texto_minusculo = texto.lower()
        texto_sem_acentos = unidecode(texto_minusculo)
        return texto_sem_acentos

    # --- Etapa 3: Funções de Análise e Classificação ---

    def _determinar_categoria_da_mensagem(self, mensagem_original: str, texto_normalizado: str) -> Tuple[str, List[str]]:
        """
        Classifica a mensagem em um dos três buckets baseado no conteúdo.
        
        Buckets:
        - "system": Mensagens que requerem integrações/APIs externas
        - "messages": Perguntas diretas e objetivas
        - "user": Mensagens complexas que precisam de personalização
        
        Args:
            mensagem_original: Texto original da mensagem
            texto_normalizado: Texto normalizado para análise
            
        Returns:
            Tuple[str, List[str]]: (bucket, lista de motivos da classificação)
            
        Example:
            >>> self._determinar_categoria_da_mensagem("Agende reunião no google", "agende reuniao no google")
            ("system", ["Palavras-chave de sistemas/APIs: google, reuniao"])
        """

        # Prioridade 1: É um pedido que envolve sistemas/integrações?
        palavras_encontradas = [
            p for p in PALAVRAS_CHAVE_DE_SISTEMA 
            if re.search(r'\b' + re.escape(p) + r'\b', texto_normalizado)
        ]
        if palavras_encontradas:
            motivo = f"Palavras-chave de sistemas/APIs: {', '.join(palavras_encontradas[:6])}"
            return "system", [motivo]

        # Prioridade 2: É uma pergunta direta e objetiva?
        if self._e_pergunta_direta_e_objetiva(mensagem_original):
            return "messages", ["Pergunta direta/fechada detectada."]

        # Prioridade 3: É uma mensagem complexa ou pessoal?
        if self._e_mensagem_complexa_ou_pessoal(mensagem_original):
            return "user", ["Mensagem com necessidade de personalização/contexto."]

        # Se não se encaixar em nenhuma regra, decide pelo tamanho.
        if len(mensagem_original) < 60:
            return "messages", ["Curta e objetiva; sem necessidade clara de contexto."]
        else:
            return "user", ["Mensagem requer elaboração moderada."]

    def _e_pergunta_direta_e_objetiva(self, texto: str) -> bool:
        """
        Identifica se uma mensagem é uma pergunta direta que requer resposta factual.
        
        Critérios:
        - Mensagem curta (≤ 80 chars) terminada com "?"
        - Contém termos factuais como "que dia e hoje", "capital de", etc.
        
        Args:
            texto: Texto da mensagem a ser analisada
            
        Returns:
            bool: True se for pergunta direta, False caso contrário
            
        Example:
            >>> self._e_pergunta_direta_e_objetiva("Qual a capital do Brasil?")
            True
        """

        e_curta_e_termina_com_interrogacao = len(texto) <= 80 and texto.endswith("?")
        
        texto_sem_acentos = self._normalizar_texto(texto)
        contem_termos_factuais = bool(re.search(
            r"\b(que dia e hoje|data de hoje|quem descobriu|capital de|definicao de|quanto e|resultado de)\b",
            texto_sem_acentos,
            re.IGNORECASE
        ))
        
        return e_curta_e_termina_com_interrogacao or contem_termos_factuais

    def _e_mensagem_complexa_ou_pessoal(self, texto: str) -> bool:
        """
        Identifica mensagens que requerem personalização ou contexto específico.
        
        Critérios:
        - Mensagem longa (> 160 chars)
        - Referências pessoais ("meu", "minha", "eu")
        - Pedidos de planejamento ("plano", "estratégia")
        - Múltiplas frases
        
        Args:
            texto: Texto da mensagem a ser analisada
            
        Returns:
            bool: True se for mensagem complexa/pessoal, False caso contrário
            
        Example:
            >>> self._e_mensagem_complexa_ou_pessoal("Preciso de um plano para organizar minha rotina")
            True
        """

        e_longa = len(texto) > 160
        usa_referencias_pessoais = bool(re.search(r"\b(meu|minha|minhas|meus|eu|para mim|no meu caso)\b", texto, re.IGNORECASE))
        pede_um_plano_ou_estrategia = bool(re.search(r"\b(plano|passo a passo|organizar|estratégia|roteiro|currículo|proposta|estudo)\b", texto, re.IGNORECASE))
        tem_multiplas_frases = len(re.findall(r"[.?!;]", texto)) > 1
        
        return e_longa or usa_referencias_pessoais or pede_um_plano_ou_estrategia or tem_multiplas_frases

    # --- Etapa 4: Funções de Construção do Payload para a IA ---

    def _construir_payload_para_ia(self, categoria: str, mensagem_original: str, texto_normalizado: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Constrói o payload otimizado para envio ao modelo de IA.
        
        Monta as mensagens de sistema, histórico e parâmetros dinâmicos
        baseado na categoria identificada.
        
        Args:
            categoria: Bucket da mensagem (system/messages/user)
            mensagem_original: Texto original da mensagem
            texto_normalizado: Texto normalizado para detecção
            
        Returns:
            Tuple[Dict, List]: (payload_para_ia, lista_de_integrações)
            
        Example:
            >>> payload, integracoes = self._construir_payload_para_ia("system", "Agende reunião", "agende reuniao")
            >>> print(payload["temperature"])
            0.3
        """

        idioma = self.contexto.get("lang") or self._determinar_idioma(mensagem_original)
        
        prompts_de_sistema, integrações = self._criar_prompts_de_sistema(categoria, idioma, texto_normalizado)
        historico_da_conversa = self._obter_historico_da_conversa()
        
        mensagens = prompts_de_sistema + historico_da_conversa + [{"role": "user", "content": mensagem_original}]
        
        parametros_dinamicos = self._calcular_parametros_da_ia(categoria)

        payload_final = {
            "model": self.contexto.get("model", "gpt-4.1-mini"),
            "messages": mensagens,
            **parametros_dinamicos, # Adiciona temperature e max_tokens
        }
        return payload_final, integrações
    
    def _criar_prompts_de_sistema(self, categoria: str, idioma: str, texto_normalizado: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Cria prompts de sistema personalizados baseado na categoria e idioma.
        
        Para cada categoria, gera prompts específicos que orientam o comportamento
        da IA e detecta integrações necessárias baseado em palavras-chave.
        
        Args:
            categoria: Bucket da mensagem (system/messages/user)
            idioma: Idioma identificado ("pt" ou "en")
            texto_normalizado: Texto para detecção de integrações
            
        Returns:
            Tuple[List[Dict], List[str]]: (lista_de_prompts, integrações_detectadas)
            
        Example:
            >>> prompts, integracoes = self._criar_prompts_de_sistema("system", "pt", "google calendar")
            >>> print(integracoes)
            ["google"]
        """

        prompts = []
        integracoes_detectadas = []

        # 1. Prompt de Idioma (sempre adicionado)
        prompt_idioma = "Reply in English." if idioma == "en" else "Responda em português do Brasil."
        prompts.append({"role": "system", "content": prompt_idioma})

        # 2. Prompts Específicos da Categoria
        if categoria == "system":
            # Detecta quais integrações podem ser necessárias
            if any(k in texto_normalizado for k in ["google", "drive", "docs", "sheet", "planilha", "calendar", "agenda"]): integracoes_detectadas.append("google")
            if any(k in texto_normalizado for k in ["apple", "icloud", "notes"]): integracoes_detectadas.append("apple")
            if any(k in texto_normalizado for k in ["boleto", "fatura", "cobranca"]): integracoes_detectadas.append("boleto")
            
            integracoes_str = ", ".join(integracoes_detectadas) or "nenhuma"
            prompts.append({
                "role": "system",
                "content": f"MODO INTEGRAÇÃO ATIVO. A intenção do usuário parece ser usar ferramentas como calendário, documentos ou pagamentos. Antes de agir, sempre confirme os detalhes necessários. Informe que usaria as APIs ({integracoes_str}) e peça confirmação."
            })
        else: # Categoria 'user' ou 'messages'
            prompts.append({
                "role": "system",
                "content": "Você é um assistente no WhatsApp, amigável e direto. Evite jargões. Se não souber algo, admita e sugira como verificar."
            })
            if categoria == "user":
                prompts.append({
                    "role": "system",
                    "content": "INSTRUÇÃO ADICIONAL: A mensagem do usuário é complexa. Faça até 2 perguntas para entender melhor e estruture a resposta final em tópicos, se aplicável."
                })
            elif categoria == "messages":
                prompts.append({
                    "role": "system",
                    "content": "INSTRUÇÃO ADICIONAL: A mensagem é uma pergunta direta. Responda de forma objetiva em 1 a 3 frases."
                })
        
        return prompts, integracoes_detectadas

    def _calcular_parametros_da_ia(self, categoria: str) -> Dict[str, Any]:
        """
        Calcula parâmetros dinâmicos da IA baseado na categoria da mensagem.
        
        Ajusta temperature e max_tokens para otimizar o comportamento da IA:
        - messages: Baixa criatividade, respostas factuais
        - system: Comportamento previsível para integrações
        - user: Permite criatividade moderada
        
        Args:
            categoria: Bucket da mensagem (system/messages/user)
            
        Returns:
            Dict[str, Any]: Dicionário com temperature e max_tokens
            
        Example:
            >>> params = self._calcular_parametros_da_ia("messages")
            >>> print(params["temperature"])
            0.2
        """

        temp_base = float(self.contexto.get("temperature", 0.3))

        if categoria == "messages":
            # Para perguntas diretas, queremos respostas factuais e sem criatividade.
            return {"temperature": min(temp_base, 0.2), "max_tokens": 400}
        elif categoria == "system":
            # Para integrações, queremos um comportamento previsível.
            return {"temperature": min(temp_base, 0.3), "max_tokens": 900}
        else: # user
            # Para pedidos complexos, permitimos um pouco mais de criatividade.
            return {"temperature": min(max(temp_base, 0.3), 0.6), "max_tokens": 900}

    def _obter_historico_da_conversa(self) -> List[Dict[str, str]]:
        """
        Extrai e valida o histórico da conversa do payload.
        
        Filtra mensagens inválidas e retorna apenas as últimas 6 interações
        para manter o contexto sem sobrecarregar o modelo.
        
        Returns:
            List[Dict[str, str]]: Lista de mensagens válidas do histórico
            
        Example:
            >>> historico = self._obter_historico_da_conversa()
            >>> print(len(historico))  # máximo 6
            3
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
        return historico_valido[-6:] # Retorna apenas as últimas 6 interações

    def _determinar_idioma(self, texto: str) -> str:
        """
        Detecta automaticamente o idioma da mensagem.
        
        Analisa caracteres especiais e palavras-chave para identificar
        se a mensagem está em português ou inglês.
        
        Args:
            texto: Texto para análise de idioma
            
        Returns:
            str: "pt" para português, "en" para inglês
            
        Example:
            >>> self._determinar_idioma("Como está o tempo hoje?")
            "pt"
        """

        tem_pt = (re.search(r"[ãõçáéíóúàêô]", texto, re.IGNORECASE) or
                  re.search(r"\b(que|como|quando|onde|reuniao|calendario)\b", texto, re.IGNORECASE))
        tem_en = re.search(r"\b(what|how|when|where|meeting|calendar)\b", texto, re.IGNORECASE)
        
        return "en" if tem_en and not tem_pt else "pt"

    def _construir_payload_de_erro_para_entrada_vazia(self) -> Dict[str, Any]:
        """
        Constrói resposta padrão para casos de entrada vazia.
        
        Returns:
            Dict[str, Any]: Payload com erro formatado para entrada vazia
        """

        return {
            **self.payload_original,
            "error": "EMPTY_INPUT",
            "openaiPayload": {
                "messages": [
                    {"role": "assistant", "content": "Não recebi sua mensagem. Pode reenviar, por favor?"}
                ]
            }
        }


# --- Endpoint da API ---

@app.post("/preprocess", summary="Processa e prepara uma mensagem para a IA")
async def rota_de_preprocessamento(payload: Dict[str, Any]) -> JSONResponse:
    """
    Endpoint principal para processamento de mensagens.
    
    Recebe uma mensagem do usuário, classifica em buckets, detecta integrações
    necessárias e retorna um payload otimizado para modelos de IA.
    
    Args:
        payload: Dicionário contendo:
            - message (str): Mensagem do usuário (obrigatório)
            - ctx (dict, opcional): Contexto com configurações
            - history (list, opcional): Histórico da conversa
    
    Returns:
        JSONResponse: Resposta estruturada com classificação e payload para IA
        
    Raises:
        HTTPException: 400 se o payload estiver vazio
        
    Example:
        Request:
        ```json
        {
            "message": "Agende uma reunião no google calendar",
            "ctx": {"lang": "pt"}
        }
        ```
        
        Response:
        ```json
        {
            "classification": {
                "bucket": "system",
                "reasons": ["Palavras-chave de sistemas/APIs: google, reuniao"],
                "integrations": ["google"]
            },
            "openaiPayload": {...}
        }
        ```
    """

    if not payload:
        raise HTTPException(status_code=400, detail="O payload não pode ser vazio.")
        
    # 1. Cria o Analisador (O "Gerente") para cuidar do pedido.
    analisador = AnalisadorDeMensagem(payload)
    
    # 2. Pede para o Analisador processar a mensagem e preparar o resultado.
    resultado_final = analisador.processar_mensagem()
    
    # 3. Retorna o resultado completo para o n8n.
    return JSONResponse(content=resultado_final)