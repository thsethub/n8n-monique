# Arquitetura Técnica - Microsserviço de Pré-processamento

## Visão Geral da Arquitetura

O microsserviço de pré-processamento segue uma arquitetura de camadas com responsabilidades bem definidas, implementando padrões de design limpo e facilitando manutenção e escalabilidade.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Cliente (n8n)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP POST /preprocess
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  • Validação de entrada                                    │
│  • Tratamento de erros                                     │
│  • Serialização JSON                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Business Logic Layer                          │
│                (AnalisadorDeMensagem)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Extraction    │ │ Classification  │ │  Integration    ││
│  │   & Normalization│ │     Engine      │ │   Detection     ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │ Prompt Builder  │ │ Parameter Calc  │ │ Language Det.   ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Response Assembly                            │
├─────────────────────────────────────────────────────────────┤
│  • Estruturação do payload para IA                         │
│  • Metadados de classificação                              │
│  • Preservação do contexto original                        │
└─────────────────────────────────────────────────────────────┘
```

## Componentes Detalhados

### 1. API Layer (FastAPI)

**Responsabilidades:**
- Exposição de endpoints REST
- Validação de entrada
- Tratamento de exceções
- Documentação automática (OpenAPI/Swagger)

**Tecnologias:**
- FastAPI 0.116.1
- Pydantic para validação
- Uvicorn como servidor ASGI

**Endpoints:**
- `POST /preprocess`: Endpoint principal de processamento
- `GET /docs`: Documentação interativa
- `GET /redoc`: Documentação alternativa

### 2. Business Logic Layer (AnalisadorDeMensagem)

#### 2.1 Extraction & Normalization
**Função:** `_extrair_mensagem_do_payload()`, `_normalizar_texto()`

**Processo:**
1. Extração segura da mensagem do payload
2. Limpeza de espaços em branco
3. Conversão para minúsculas
4. Remoção de acentos (unidecode)

**Input:** Payload JSON bruto
**Output:** Mensagem limpa e texto normalizado

#### 2.2 Classification Engine
**Função:** `_determinar_categoria_da_mensagem()`

**Algoritmo de Classificação:**
```python
# Prioridade 1: Sistema (palavras-chave)
if encontrou_palavras_sistema:
    return "system"
    
# Prioridade 2: Pergunta direta
elif é_pergunta_objetiva:
    return "messages"
    
# Prioridade 3: Complexa/pessoal
elif é_complexa_ou_pessoal:
    return "user"
    
# Fallback: Por tamanho
else:
    return "messages" if len < 60 else "user"
```

**Buckets:**
- **system**: Integrações, APIs, ferramentas externas
- **messages**: Perguntas diretas, factuais
- **user**: Complexas, personalizadas, planejamento

#### 2.3 Integration Detection
**Função:** `_criar_prompts_de_sistema()`

**Integrações Suportadas:**
- **Google**: Drive, Calendar, Docs, Sheets
- **Apple**: iCloud, Notes
- **Financeiro**: Boletos, faturas, cobranças

**Processo:**
1. Análise de palavras-chave no texto normalizado
2. Mapeamento para integrações específicas
3. Criação de prompts contextuais

#### 2.4 Prompt Builder
**Função:** `_criar_prompts_de_sistema()`

**Estrutura de Prompts:**
```python
prompts = [
    {"role": "system", "content": prompt_idioma},
    {"role": "system", "content": prompt_categoria_especifico},
    {"role": "system", "content": prompt_instrucoes_adicionais}
]
```

**Tipos de Prompts:**
- **Idioma**: Força resposta em PT/EN
- **Categoria**: Específico para cada bucket
- **Integração**: Orienta uso de APIs
- **Instrução**: Comportamento adicional

#### 2.5 Parameter Calculator
**Função:** `_calcular_parametros_da_ia()`

**Configurações por Bucket:**

| Bucket | Temperature | Max Tokens | Objetivo |
|--------|------------|------------|----------|
| messages | ≤ 0.2 | 400 | Respostas factuais |
| system | ≤ 0.3 | 900 | Comportamento previsível |
| user | 0.3-0.6 | 900 | Criatividade moderada |

#### 2.6 Language Detection
**Função:** `_determinar_idioma()`

**Critérios:**
- Caracteres especiais: `[ãõçáéíóúàêô]`
- Palavras-chave PT: `que, como, quando, reuniao`
- Palavras-chave EN: `what, how, when, meeting`

**Fallback:** Português (PT) como padrão

### 3. Data Flow

```
Input JSON
    ↓
Extract Message
    ↓
Normalize Text
    ↓
Classify → [system|messages|user]
    ↓
Detect Integrations → [google|apple|boleto|...]
    ↓
Build Prompts
    ↓
Calculate Parameters
    ↓
Assemble History
    ↓
Generate OpenAI Payload
    ↓
Structure Response
    ↓
JSON Output
```

### 4. Response Structure

```json
{
  "message": "string",              // Original message
  "ctx": {...},                     // Original context
  "mensagem_completa": "string",    // Extracted message
  "texto_normalizado": "string",    // Normalized text
  "openaiPayload": {                // Ready for OpenAI
    "model": "string",
    "messages": [...],
    "temperature": 0.3,
    "max_tokens": 400
  },
  "classification": {
    "bucket": "string",             // system|messages|user
    "reasons": ["string"],          // Classification reasons
    "integrations": ["string"]      // Detected integrations
  }
}
```

## Padrões de Design Utilizados

### 1. Single Responsibility Principle (SRP)
Cada método tem uma responsabilidade específica:
- `_extrair_mensagem_do_payload()`: Apenas extração
- `_normalizar_texto()`: Apenas normalização
- `_determinar_categoria_da_mensagem()`: Apenas classificação

### 2. Strategy Pattern
Diferentes estratégias de processamento baseadas no bucket:
- Prompts específicos por categoria
- Parâmetros específicos por categoria
- Comportamentos específicos por categoria

### 3. Template Method Pattern
`processar_mensagem()` define o template do algoritmo:
1. Extrair → 2. Normalizar → 3. Classificar → 4. Construir

### 4. Factory Pattern
`_criar_prompts_de_sistema()` atua como factory de prompts baseado na categoria.

## Performance e Escalabilidade

### Métricas Atuais
- **Tempo de resposta**: ~50-100ms por requisição
- **Memória**: ~20MB por instância
- **CPU**: Baixo uso (principalmente regex e string operations)

### Otimizações Implementadas
1. **Set para palavras-chave**: O(1) lookup vs O(n) em listas
2. **Regex compiladas**: Reutilização de padrões
3. **Histórico limitado**: Máximo 6 mensagens para controle de memória
4. **Normalização cacheável**: Unidecode é determinístico

### Escalabilidade Horizontal
- **Stateless**: Sem estado entre requisições
- **Container-ready**: Docker com recursos mínimos
- **Load balancer friendly**: Resposta rápida e determinística

## Segurança

### Validação de Entrada
- Payload obrigatório (400 se vazio)
- Sanitização automática via Pydantic
- Escape de regex em palavras-chave

### Logging
- Log level configurável
- Sem exposição de dados sensíveis
- Estruturado para monitoramento

## Testes e Qualidade

### Categorias de Teste
1. **Unitários**: Cada método individualmente
2. **Integração**: Fluxo completo de processamento
3. **Classificação**: Validação de buckets
4. **Performance**: Tempo de resposta

### Exemplos de Casos de Teste

```python
# Teste de classificação system
assert classificar("Agende reunião no google") == "system"

# Teste de classificação messages
assert classificar("Qual a capital do Brasil?") == "messages"

# Teste de classificação user
assert classificar("Preciso de um plano de estudos personalizado") == "user"

# Teste de detecção de integração
integracoes = detectar_integracoes("usar google drive")
assert "google" in integracoes
```

## Monitoramento e Observabilidade

### Métricas Recomendadas
- Taxa de requisições por segundo
- Distribuição de latência (p50, p95, p99)
- Taxa de erro por endpoint
- Distribuição de buckets de classificação
- Integrações mais detectadas

### Logs Estruturados
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Message processed",
  "bucket": "system",
  "integrations": ["google"],
  "processing_time_ms": 45
}
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

## Deployment

### Container Specifications
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8181"]
```

### Resource Requirements
- **CPU**: 0.1-0.2 cores por instância
- **Memory**: 128-256MB por instância
- **Storage**: Mínimo (apenas código)
- **Network**: HTTP/HTTPS padrão

### Environment Variables
```bash
LOG_LEVEL=INFO
PORT=8181
WORKERS=1
```

## Evolução e Roadmap

### Próximas Melhorias
1. **Cache de classificação**: Redis para mensagens similares
2. **Métricas avançadas**: Prometheus/Grafana
3. **Modelos ML**: Classificação baseada em embeddings
4. **Rate limiting**: Proteção contra abuso
5. **Batch processing**: Múltiplas mensagens por requisição

### Extensibilidade
- Novos buckets de classificação
- Novas integrações (Slack, Teams, etc.)
- Suporte a mais idiomas
- Classificação baseada em contexto histórico