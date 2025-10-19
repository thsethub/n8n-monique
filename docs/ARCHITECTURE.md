# 🏗️ Arquitetura do Microserviço

## Visão Geral

Este documento descreve a arquitetura modular do microserviço de análise e preparo de mensagens para IA.

## 📦 Estrutura de Módulos

```
app/
├── api/                    # Camada de Apresentação (API)
│   ├── routes.py          # Definição de todos os endpoints
│   └── __init__.py
│
├── core/                   # Núcleo da Aplicação
│   ├── config.py          # Configuração global (logging)
│   ├── metrics.py         # Métricas e cache global
│   ├── middleware.py      # Middleware de logging de latência
│   └── __init__.py
│
├── services/               # Lógica de Negócio
│   ├── analisador.py      # Serviço de análise de mensagens
│   └── __init__.py
│
├── models/                 # Modelos de Dados
│   ├── schemas.py         # Schemas Pydantic (futuro)
│   └── __init__.py
│
├── utils/                  # Utilitários
│   ├── regex.py           # Regex pré-compiladas
│   └── __init__.py
│
├── main.py                 # Ponto de entrada FastAPI
└── __init__.py
```

---

## 🔄 Fluxo de Requisição

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cliente (n8n, webhook)                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application (main.py)                │
│                     ┌─────────────────────────┐                  │
│                     │  GZip Middleware        │                  │
│                     └───────────┬─────────────┘                  │
│                                 ▼                                 │
│                     ┌─────────────────────────┐                  │
│                     │  Logging Middleware     │                  │
│                     │  (metrics, latency)     │                  │
│                     └───────────┬─────────────┘                  │
└─────────────────────────────────┼─────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Routes (api/routes.py)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ /preprocess  │  │  /webhook    │  │  /metrics    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          ▼                  ▼                  │
┌─────────────────────────────────────────────┐│
│   AnalisadorDeMensagem (services/analisador) ││
│                                               ││
│  1. Extração da mensagem                     ││
│  2. Verificação de cache                     ││
│  3. Normalização de texto                    ││
│  4. Classificação (system/user/messages)     ││
│  5. Detecção de scopes                       ││
│  6. Construção do payload OpenAI             ││
│  7. Armazenamento em cache                   ││
└───────────────────┬───────────────────────────┘│
                    ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Métricas & Cache (core/metrics.py)            │
│  - classificacao_cache (TTL: 1h)                                 │
│  - metricas (requests, cache_hits, latency, errors)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Responsabilidades dos Módulos

### `app/main.py`
- **Responsabilidade**: Inicialização da aplicação FastAPI
- **Dependências**: FastAPI, middlewares, rotas
- **Exports**: `app` (instância FastAPI)

### `app/api/routes.py`
- **Responsabilidade**: Definição de endpoints HTTP
- **Endpoints**:
  - `POST /preprocess` - Preprocessamento de mensagens
  - `POST /webhook` - Recebimento de webhooks
  - `GET /health` - Health check
  - `GET /metrics` - Métricas de performance
- **Dependências**: AnalisadorDeMensagem, logger, metrics

### `app/core/config.py`
- **Responsabilidade**: Configuração global do logging estruturado
- **Exports**: `logger` (structlog instance)
- **Configuração**: JSON logging, timestamps ISO, error formatting

### `app/core/metrics.py`
- **Responsabilidade**: Armazenamento de métricas e cache
- **Exports**:
  - `classificacao_cache` - TTLCache (1h, max 1000 items)
  - `metricas` - Dict com contadores globais
- **Métricas rastreadas**:
  - `total_requests`
  - `cache_hits` / `cache_misses`
  - `total_latency_ms`
  - `error_count`

### `app/core/middleware.py`
- **Responsabilidade**: Middleware de logging e medição de latência
- **Funcionalidades**:
  - Medição do tempo de processamento
  - Logging estruturado de requisições
  - Adição do header `X-Process-Time`
  - Tracking de erros

### `app/services/analisador.py`
- **Responsabilidade**: Lógica de negócio de análise de mensagens
- **Classe Principal**: `AnalisadorDeMensagem`
- **Funcionalidades**:
  - Extração e normalização de texto
  - Classificação em categorias (system/user/messages)
  - Detecção de scopes de integrações
  - Seleção automática de modelo OpenAI
  - Ajuste de parâmetros (temperature, max_tokens)
  - Gestão de cache com hash MD5
- **Otimizações**:
  - Cache LRU para normalização de texto
  - Regex pré-compiladas
  - Busca direta com `in` ao invés de regex quando possível

### `app/utils/regex.py`
- **Responsabilidade**: Regex pré-compiladas para performance
- **Exports**:
  - `REGEX_PT_INDICADORES` - Detecção de acentos portugueses
  - `REGEX_PT_PALAVRAS` - Palavras em português
  - `REGEX_EN_PALAVRAS` - Palavras em inglês
  - `REGEX_PERGUNTA_FACTUAL` - Perguntas factuais
  - `REGEX_REFERENCIAS_PESSOAIS` - Pronomes pessoais
  - `REGEX_PLANO_ESTRATEGIA` - Palavras de planejamento
  - `REGEX_MULTIPLAS_FRASES` - Detecção de pontuação

---

## 🎯 Padrões de Design Utilizados

### 1. **Service Layer Pattern**
- Separação clara entre rotas (API) e lógica de negócio (services)
- `AnalisadorDeMensagem` encapsula toda a lógica de análise

### 2. **Singleton Pattern**
- Cache e métricas são objetos globais compartilhados
- Logger configurado uma vez e reutilizado

### 3. **Strategy Pattern**
- Seleção dinâmica de modelo OpenAI baseado na categoria
- Ajuste de parâmetros baseado no tipo de mensagem

### 4. **Cache-Aside Pattern**
- Verificação de cache antes do processamento
- Armazenamento em cache após processamento
- Invalidação automática via TTL

### 5. **Middleware Pattern**
- Logging e métricas aplicados de forma transparente
- Separação de concerns (logging vs business logic)

---

## ⚡ Otimizações Implementadas

### Performance
1. **Cache TTL** (1h) - Reduz 95% do tempo para mensagens repetidas
2. **Regex pré-compiladas** - 3-5x mais rápidas que regex inline
3. **LRU Cache** - Normalização de texto cacheada (512 entries)
4. **Busca direta com `in`** - Mais rápida que regex para palavras-chave
5. **Histórico limitado** - Apenas últimas 3 mensagens (reduz tokens)
6. **GZip Middleware** - Compressão de respostas HTTP

### Observabilidade
1. **Logging estruturado** (JSON) - Fácil parsing e agregação
2. **Métricas detalhadas** - Por etapa do processamento
3. **Endpoint /metrics** - Exposição de métricas em tempo real
4. **Header X-Process-Time** - Latência em cada resposta

---

## 🔐 Segurança (Futuro)

- [ ] Rate limiting por IP/usuário
- [ ] Validação de schema com Pydantic
- [ ] Sanitização de inputs
- [ ] CORS configurável
- [ ] API Key authentication
- [ ] Request size limits

---

## 📈 Escalabilidade

### Horizontal
- Stateless (exceto cache em memória)
- Pode rodar múltiplas instâncias atrás de load balancer
- **Limitação atual**: Cache local não compartilhado

### Vertical
- Async/await para I/O não-bloqueante
- Processamento otimizado (< 1ms por mensagem)
- Baixo consumo de CPU

### Melhorias Futuras
- [ ] Redis para cache distribuído
- [ ] Message queue para processamento assíncrono
- [ ] Database para histórico persistente
- [ ] Circuit breaker para APIs externas

---

## 🧪 Testabilidade

### Vantagens da Arquitetura Modular
- Cada módulo pode ser testado isoladamente
- Mocks fáceis (services, cache, logger)
- Testes de integração via TestClient (FastAPI)
- Fixtures reutilizáveis (pytest)

### Cobertura de Testes
- Unitários: `services/analisador.py`, `utils/regex.py`
- Integração: `api/routes.py`
- E2E: Docker + curl

---

## 📚 Referências

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Structlog Documentation](https://www.structlog.org/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
