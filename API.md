# API Documentation - Microsserviço de Pré-processamento

## Base URL
```
http://localhost:8181
```

## Authentication
Atualmente não requer autenticação. Para ambientes de produção, considere implementar API keys ou autenticação JWT.

## Headers
```
Content-Type: application/json
Accept: application/json
```

---

## Endpoints

### POST /preprocess

Processa e classifica uma mensagem para otimização de envio para modelos de IA.

#### Request

**URL:** `POST /preprocess`

**Headers:**
```http
Content-Type: application/json
```

**Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | ✅ | Mensagem do usuário a ser processada |
| `ctx` | object | ❌ | Contexto e configurações |
| `ctx.lang` | string | ❌ | Idioma forçado ("pt" ou "en"). Default: auto-detect |
| `ctx.model` | string | ❌ | Modelo da IA. Default: "gpt-4.1-mini" |
| `ctx.temperature` | number | ❌ | Temperature base. Default: 0.3 |
| `history` | array | ❌ | Histórico da conversa (máx. 6 mensagens) |
| `history[].role` | string | ❌ | Papel: "user" ou "assistant" |
| `history[].content` | string | ❌ | Conteúdo da mensagem |

#### Request Examples

##### 1. Mensagem Simples
```json
{
  "message": "Qual é a capital do Brasil?"
}
```

##### 2. Com Contexto
```json
{
  "message": "Schedule a meeting for tomorrow",
  "ctx": {
    "lang": "en",
    "model": "gpt-4-turbo",
    "temperature": 0.5
  }
}
```

##### 3. Com Histórico
```json
{
  "message": "E no Google Drive?",
  "ctx": {
    "lang": "pt"
  },
  "history": [
    {
      "role": "user",
      "content": "Como posso organizar meus documentos?"
    },
    {
      "role": "assistant", 
      "content": "Você pode criar pastas por categorias..."
    }
  ]
}
```

#### Response

**Status Code:** `200 OK`

**Response Body:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Mensagem original do request |
| `ctx` | object | Contexto original do request |
| `mensagem_completa` | string | Mensagem extraída e limpa |
| `texto_normalizado` | string | Texto normalizado (sem acentos, minúsculas) |
| `openaiPayload` | object | Payload otimizado para OpenAI |
| `openaiPayload.model` | string | Modelo da IA configurado |
| `openaiPayload.messages` | array | Array de mensagens formatadas |
| `openaiPayload.temperature` | number | Temperature calculada |
| `openaiPayload.max_tokens` | number | Limite de tokens |
| `classification` | object | Resultado da classificação |
| `classification.bucket` | string | Categoria: "system", "messages", ou "user" |
| `classification.reasons` | array | Motivos da classificação |
| `classification.integrations` | array | Integrações detectadas |

#### Response Examples

##### 1. Pergunta Direta (Bucket: messages)
```json
{
  "message": "Qual é a capital do Brasil?",
  "ctx": {},
  "mensagem_completa": "Qual é a capital do Brasil?",
  "texto_normalizado": "qual e a capital do brasil?",
  "openaiPayload": {
    "model": "gpt-4.1-mini",
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
        "content": "Qual é a capital do Brasil?"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 400
  },
  "classification": {
    "bucket": "messages",
    "reasons": ["Pergunta direta/fechada detectada."],
    "integrations": []
  }
}
```

##### 2. Integração de Sistema (Bucket: system)
```json
{
  "message": "Preciso organizar uma reunião no meu google calendar para a próxima semana",
  "ctx": {
    "lang": "pt"
  },
  "mensagem_completa": "Preciso organizar uma reunião no meu google calendar para a próxima semana",
  "texto_normalizado": "preciso organizar uma reuniao no meu google calendar para a proxima semana",
  "openaiPayload": {
    "model": "gpt-4.1-mini",
    "messages": [
      {
        "role": "system",
        "content": "Responda em português do Brasil."
      },
      {
        "role": "system",
        "content": "MODO INTEGRAÇÃO ATIVO. A intenção do usuário parece ser usar ferramentas como calendário, documentos ou pagamentos. Antes de agir, sempre confirme os detalhes necessários. Informe que usaria as APIs (google) e peça confirmação."
      },
      {
        "role": "user",
        "content": "Preciso organizar uma reunião no meu google calendar para a próxima semana"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 900
  },
  "classification": {
    "bucket": "system",
    "reasons": ["Palavras-chave de sistemas/APIs: google, reuniao"],
    "integrations": ["google"]
  }
}
```

##### 3. Mensagem Complexa (Bucket: user)
```json
{
  "message": "Preciso criar um plano de estudos personalizado para aprender Python, considerando que trabalho 8 horas por dia e tenho apenas 2 horas livres à noite",
  "ctx": {
    "lang": "pt"
  },
  "mensagem_completa": "Preciso criar um plano de estudos personalizado para aprender Python, considerando que trabalho 8 horas por dia e tenho apenas 2 horas livres à noite",
  "texto_normalizado": "preciso criar um plano de estudos personalizado para aprender python, considerando que trabalho 8 horas por dia e tenho apenas 2 horas livres a noite",
  "openaiPayload": {
    "model": "gpt-4.1-mini",
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
        "content": "INSTRUÇÃO ADICIONAL: A mensagem do usuário é complexa. Faça até 2 perguntas para entender melhor e estruture a resposta final em tópicos, se aplicável."
      },
      {
        "role": "user",
        "content": "Preciso criar um plano de estudos personalizado para aprender Python, considerando que trabalho 8 horas por dia e tenho apenas 2 horas livres à noite"
      }
    ],
    "temperature": 0.4,
    "max_tokens": 900
  },
  "classification": {
    "bucket": "user",
    "reasons": ["Mensagem com necessidade de personalização/contexto."],
    "integrations": []
  }
}
```

#### Error Responses

##### 400 Bad Request - Payload Vazio
```json
{
  "detail": "O payload não pode ser vazio."
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Interactive Documentation

### Swagger UI
Acesse `http://localhost:8181/docs` para documentação interativa com possibilidade de testar os endpoints.

### ReDoc
Acesse `http://localhost:8181/redoc` para documentação alternativa em formato mais limpo.

---

## Classification Logic

### Buckets Detalhados

#### 1. "system" - Integrações e Ferramentas

**Critério Principal:** Presença de palavras-chave relacionadas a sistemas externos

**Palavras-chave detectadas:**
- **Documentos:** documento, document, doc, planilha, spreadsheet, sheet, tabela, arquivo, file, pdf
- **Armazenamento:** drive, icloud, armazenamento, storage
- **Calendário:** calendario, agenda, evento, compromisso, contatos, contacts
- **Notas:** nota, notes
- **Reuniões:** reuniao, meeting, encontro
- **Integrações:** compartilhar, share, sincronizar, sync, integracao, api, oauth
- **Plataformas:** google, apple
- **Financeiro:** boleto, fatura, cobranca, pagamento

**Comportamento:**
- Temperature: ≤ 0.3 (respostas previsíveis)
- Max tokens: 900
- Prompt: Modo integração ativo, solicita confirmação

**Integrações detectadas baseadas em contexto:**
- `google`: Para google, drive, docs, sheet, planilha, calendar, agenda
- `apple`: Para apple, icloud, notes
- `boleto`: Para boleto, fatura, cobranca

#### 2. "messages" - Perguntas Diretas

**Critérios:**
1. Mensagem curta (≤ 80 caracteres) terminada com "?"
2. Contém termos factuais: "que dia e hoje", "data de hoje", "quem descobriu", "capital de", "definicao de", "quanto e", "resultado de"

**Comportamento:**
- Temperature: ≤ 0.2 (máxima precisão)
- Max tokens: 400
- Prompt: Resposta objetiva em 1-3 frases

#### 3. "user" - Mensagens Complexas/Pessoais

**Critérios:**
1. Mensagem longa (> 160 caracteres)
2. Referências pessoais: "meu", "minha", "minhas", "meus", "eu", "para mim", "no meu caso"
3. Pedidos de planejamento: "plano", "passo a passo", "organizar", "estratégia", "roteiro", "currículo", "proposta", "estudo"
4. Múltiplas frases (> 1 pontuação: . ? ! ;)

**Comportamento:**
- Temperature: 0.3-0.6 (permite criatividade)
- Max tokens: 900
- Prompt: Até 2 perguntas de esclarecimento, respostas estruturadas

#### Fallback por Tamanho
Se não se encaixar em nenhuma regra específica:
- Mensagem < 60 caracteres → "messages"
- Mensagem ≥ 60 caracteres → "user"

---

## Language Detection

### Critérios de Detecção

#### Português (pt)
- **Caracteres especiais:** ã, õ, ç, á, é, í, ó, ú, à, ê, ô
- **Palavras-chave:** que, como, quando, onde, reuniao, calendario

#### Inglês (en)
- **Palavras-chave:** what, how, when, where, meeting, calendar

#### Lógica
```
if (tem_palavras_en AND NOT tem_palavras_pt):
    return "en"
else:
    return "pt"  // Default
```

---

## Parameter Calculation

### Temperature e Max Tokens por Bucket

| Bucket | Temperature Logic | Max Tokens | Justificativa |
|--------|------------------|------------|---------------|
| messages | `min(base_temp, 0.2)` | 400 | Respostas factuais, sem criatividade |
| system | `min(base_temp, 0.3)` | 900 | Comportamento previsível para APIs |
| user | `min(max(base_temp, 0.3), 0.6)` | 900 | Criatividade moderada permitida |

**Base Temperature:** Valor do `ctx.temperature` ou 0.3 como padrão.

---

## Rate Limiting (Recomendado para Produção)

Embora não implementado atualmente, recomenda-se para produção:

```
- 100 requests/minute por IP
- 1000 requests/hour por usuário
- Burst de até 10 requests simultâneas
```

---

## HTTP Status Codes

| Code | Description | Quando ocorre |
|------|-------------|---------------|
| 200 | OK | Processamento bem-sucedido |
| 400 | Bad Request | Payload vazio ou malformado |
| 422 | Unprocessable Entity | Dados inválidos (Pydantic) |
| 500 | Internal Server Error | Erro interno do servidor |

---

## Examples for Different Use Cases

### 1. Chat Bot Integration
```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como fazer backup dos meus arquivos?",
    "ctx": {"lang": "pt"}
  }'
```

### 2. Task Automation
```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a new spreadsheet in Google Drive",
    "ctx": {"lang": "en", "model": "gpt-4-turbo"}
  }'
```

### 3. Learning Assistant
```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique como funciona machine learning de forma simples",
    "ctx": {"temperature": 0.6}
  }'
```

### 4. With Conversation History
```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "E como fazer isso no Python?",
    "history": [
      {"role": "user", "content": "Como ordenar uma lista?"},
      {"role": "assistant", "content": "Você pode usar o método .sort() ou a função sorted()..."}
    ]
  }'
```

---

## SDKs and Client Libraries

### Python Client Example
```python
import requests

def preprocess_message(message, ctx=None, history=None):
    url = "http://localhost:8181/preprocess"
    payload = {"message": message}
    
    if ctx:
        payload["ctx"] = ctx
    if history:
        payload["history"] = history
    
    response = requests.post(url, json=payload)
    return response.json()

# Usage
result = preprocess_message(
    "Agende uma reunião no google calendar",
    ctx={"lang": "pt"}
)
print(result["classification"]["bucket"])  # "system"
```

### JavaScript/Node.js Client Example
```javascript
const axios = require('axios');

async function preprocessMessage(message, ctx = null, history = null) {
    const url = 'http://localhost:8181/preprocess';
    const payload = { message };
    
    if (ctx) payload.ctx = ctx;
    if (history) payload.history = history;
    
    const response = await axios.post(url, payload);
    return response.data;
}

// Usage
const result = await preprocessMessage(
    "Schedule a meeting in google calendar",
    { lang: "en" }
);
console.log(result.classification.bucket); // "system"
```

---

## Testing Checklist

### Manual Testing
- [ ] Pergunta simples → bucket "messages"
- [ ] Pergunta com integração → bucket "system" + detecção
- [ ] Mensagem complexa → bucket "user"
- [ ] Detecção de idioma PT/EN
- [ ] Histórico preservado
- [ ] Payload vazio → erro 400
- [ ] Contexto customizado aplicado

### Automated Testing
```bash
# Test simple question
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it?"}' | jq '.classification.bucket'
# Expected: "messages"

# Test system integration
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a document in Google Drive"}' | jq '.classification'
# Expected: bucket="system", integrations=["google"]
```