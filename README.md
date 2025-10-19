# 🤖 Microserviço de Análise e Preparo de Mensagens para IA

Este microserviço utiliza **FastAPI** para classificar e preparar mensagens inteligentemente antes de enviá-las para modelos de IA (OpenAI GPT), otimizando custos, performance e qualidade das respostas.

## 🎯 Funcionalidades Principais

- **Classificação Inteligente**: Analisa mensagens e as categoriza em `system`, `user` ou `messages`
- **Detecção de Integrações**: Identifica automaticamente quando APIs externas são necessárias (Google Calendar, Gmail, Drive, etc.)
- **Cache Inteligente**: Sistema de cache TTL que reduz drasticamente o tempo de resposta para mensagens similares
- **Logging Estruturado**: Logs em JSON para fácil integração com ferramentas de observabilidade
- **Métricas em Tempo Real**: Exposição de métricas de performance via endpoint `/metrics`

---

## 📋 Endpoint Principal: `/preprocess`

### **POST** `/preprocess`

Este é o endpoint mais importante do microserviço. Ele recebe uma mensagem do usuário, a classifica e prepara um payload otimizado para envio à API do OpenAI.

### 🔹 Payload de Entrada

```json
{
  "message": "Preciso agendar uma reunião com o time amanhã às 14h",
  "ctx": {
    "lang": "pt",
    "temperature": 0.3,
    "model": "gpt-4o-mini"
  },
  "history": [
    {
      "role": "user",
      "content": "Oi"
    },
    {
      "role": "assistant",
      "content": "Olá! Como posso ajudar?"
    }
  ]
}
```

#### Campos do Payload:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `message` | `string` | ✅ Sim | A mensagem do usuário a ser analisada |
| `ctx.lang` | `string` | ❌ Não | Idioma (`pt` ou `en`). Se omitido, é detectado automaticamente |
| `ctx.temperature` | `float` | ❌ Não | Temperatura base para o modelo (padrão: `0.3`) |
| `ctx.model` | `string` | ❌ Não | Modelo OpenAI a usar. Se omitido, é selecionado automaticamente |
| `history` | `array` | ❌ Não | Histórico da conversa (últimas 3 mensagens são usadas) |

---

### 🔸 Resposta (Exemplo 1: Integração de Sistema)

```json
{
  "message": "Preciso agendar uma reunião com o time amanhã às 14h",
  "ctx": {
    "lang": "pt",
    "temperature": 0.3
  },
  "history": [],
  "mensagem_completa": "Preciso agendar uma reunião com o time amanhã às 14h",
  "texto_normalizado": "preciso agendar uma reuniao com o time amanha as 14h",
  "openaiPayload": {
    "model": "gpt-4.1-mini",
    "messages": [
      {
        "role": "system",
        "content": "Responda em português do Brasil."
      },
      {
        "role": "system",
        "content": "MODO INTEGRAÇÃO ATIVO. A intenção do usuário parece ser usar ferramentas como calendário, documentos ou pagamentos. Antes de agir, sempre confirme os detalhes necessários. Informe que usaria as APIs (https://www.googleapis.com/auth/calendar) e peça confirmação."
      },
      {
        "role": "user",
        "content": "Preciso agendar uma reunião com o time amanhã às 14h"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 900
  },
  "classification": {
    "bucket": "system",
    "reasons": [
      "Palavras-chave de sistemas/APIs: reuniao, agendar"
    ],
    "scope": [
      "https://www.googleapis.com/auth/calendar"
    ]
  },
  "performance": {
    "extracao_ms": 0.05,
    "cache_lookup_ms": 0.12,
    "normalizacao_ms": 0.08,
    "classificacao_ms": 0.15,
    "construcao_payload_ms": 0.22,
    "total_ms": 0.62
  }
}
```

---

### 🔸 Resposta (Exemplo 2: Pergunta Direta)

```json
{
  "message": "Que dia é hoje?",
  "mensagem_completa": "Que dia é hoje?",
  "texto_normalizado": "que dia e hoje?",
  "openaiPayload": {
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "Responda em português do Brasil."
      },
      {
        "role": "system",
        "content": "Você é um assistente no WhatsApp, amigável e direto. Evite jargões. Se não souber algo, admita e sugira como verificar."
      },
      {
        "role": "system",
        "content": "INSTRUÇÃO ADICIONAL: A mensagem é uma pergunta direta. Responda de forma objetiva em 1 a 3 frases."
      },
      {
        "role": "user",
        "content": "Que dia é hoje?"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 400
  },
  "classification": {
    "bucket": "messages",
    "reasons": [
      "Pergunta direta/fechada detectada."
    ],
    "scope": []
  },
  "performance": {
    "extracao_ms": 0.03,
    "cache_lookup_ms": 0.08,
    "normalizacao_ms": 0.05,
    "classificacao_ms": 0.11,
    "construcao_payload_ms": 0.18,
    "total_ms": 0.45
  }
}
```

---

### ⚡ Performance e Tempo de Resposta

| Cenário | Tempo Médio | Observação |
|---------|-------------|------------|
| **Cache Hit** | **~0.15ms** | Quando a mensagem já foi processada anteriormente |
| **Cache Miss (primeira vez)** | **0.4ms - 0.8ms** | Processamento completo da mensagem |
| **Mensagem complexa** | **0.6ms - 1.2ms** | Mensagens longas ou com múltiplas intenções |
| **Com histórico (3 msgs)** | **+0.1ms - 0.2ms** | Overhead adicional para processar histórico |

**Taxa de Cache Hit esperada:** 40-60% em produção (depende do padrão de uso)

**Observação:** Os tempos acima **NÃO incluem** a latência de rede ou o tempo de resposta da API do OpenAI. São apenas os tempos de pré-processamento.

---

### 📊 Campos da Resposta

#### `classification.bucket`
Indica a categoria da mensagem:
- **`system`**: Requer integração com APIs externas (Google, pagamentos, etc.)
- **`messages`**: Pergunta direta e objetiva
- **`user`**: Mensagem complexa que requer contexto e personalização

#### `classification.scope`
Array com os escopos OAuth necessários para executar a ação (apenas para `bucket: "system"`):
- `https://www.googleapis.com/auth/calendar` - Google Calendar
- `https://mail.google.com/` - Gmail
- `https://www.googleapis.com/auth/drive` - Google Drive
- `https://www.googleapis.com/auth/spreadsheets` - Google Sheets
- `boleto` - Sistema de geração de boletos

#### `openaiPayload`
Payload pronto para ser enviado diretamente à API do OpenAI, contendo:
- **Prompts de sistema otimizados** baseados na classificação
- **Modelo selecionado automaticamente** (ou o especificado no `ctx.model`)
- **Parâmetros ajustados** (`temperature`, `max_tokens`)

#### `performance`
Métricas detalhadas de latência por etapa do processamento (em milissegundos)

---

## 🚀 Como Rodar Localmente

### 1. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Execute a API:
```bash
uvicorn app.main:app --reload --port 8181
```

### 3. Acesse a documentação interativa:
- Swagger UI: http://localhost:8181/docs
- ReDoc: http://localhost:8181/redoc

### 4. Teste o endpoint:
```bash
curl -X POST http://localhost:8181/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Preciso criar uma planilha com os dados de vendas",
    "ctx": {"lang": "pt"}
  }'
```

---

## 🐳 Docker

### Build da imagem:
```bash
docker build -t preproc-api:latest .
```

### Executar container:
```bash
docker run -p 8181:8181 preproc-api:latest
```

---

## 📁 Estrutura do Projeto

```
n8n-monique/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # Endpoints da API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuração do logging estruturado
│   │   ├── metrics.py         # Métricas e cache global
│   │   └── middleware.py      # Middleware de logging de latência
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Schemas Pydantic (futuro)
│   ├── services/
│   │   ├── __init__.py
│   │   └── analisador/         # 📦 MÓDULO MODULAR (8 componentes)
│   │       ├── __init__.py
│   │       ├── analisador_principal.py    # Orquestração
│   │       ├── classificador.py           # Classificação
│   │       ├── construtor_payload.py      # Payload OpenAI
│   │       ├── detector_scopes.py         # Detecção de scopes
│   │       ├── detector_idioma.py         # Detecção de idioma
│   │       ├── gerenciador_cache.py       # Operações de cache
│   │       ├── normalizador.py            # Normalização de texto
│   │       ├── constantes.py              # Constantes
│   │       └── README.md                  # Documentação do módulo
│   ├── utils/
│   │   ├── __init__.py
│   │   └── regex.py           # Regex pré-compiladas
│   ├── __init__.py
│   └── main.py                # Ponto de entrada FastAPI
├── tests/
│   ├── conftest.py
│   ├── pytest.ini
│   └── test_main.py
├── docs/
├── main.py                    # Importa app de app.main
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 📈 Outros Endpoints

### **GET** `/health`
Verifica o status do serviço.

**Resposta:**
```json
{
  "status": "healthy",
  "service": "preproc-api",
  "version": "2.0.0",
  "timestamp": 1697654321.123
}
```

---

### **GET** `/metrics`
Retorna métricas de performance em tempo real.

**Resposta:**
```json
{
  "total_requests": 1523,
  "cache_hits": 687,
  "cache_misses": 836,
  "cache_hit_rate_percent": 45.11,
  "cache_size": 234,
  "avg_latency_ms": 0.58,
  "error_count": 3,
  "error_rate_percent": 0.20,
  "timestamp": 1697654321.456
}
```

---

### **POST** `/webhook`
Endpoint simplificado para receber mensagens via webhook (ex: ngrok, Evolution API).

**Request:**
```json
{
  "from": "5511999999999",
  "message": "agendar reunião amanhã"
}
```

---

## 🧪 Testes

Execute os testes com pytest:

```bash
pytest tests/ -v --cov=app --cov-report=html
```

**Cobertura esperada:** >85%

---

## 🔧 Variáveis de Ambiente (Futuro)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CACHE_TTL` | `3600` | Tempo de vida do cache em segundos |
| `CACHE_MAX_SIZE` | `1000` | Tamanho máximo do cache |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |

---

## 📝 Roadmap

- [ ] Adicionar Pydantic models para validação de entrada
- [ ] Implementar rate limiting
- [ ] Adicionar suporte a múltiplos idiomas (ES, FR)
- [ ] Integração com Redis para cache distribuído
- [ ] Implementar circuit breaker para APIs externas
- [ ] Adicionar testes de integração
- [ ] Documentação de arquitetura (diagramas)

---

## 📄 Licença

MIT License - Sinta-se livre para usar e modificar.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
