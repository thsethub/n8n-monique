# Microsserviço de Pré-processamento para IA

## Visão Geral

Este microsserviço é responsável por analisar, classificar e preparar mensagens de usuários antes de enviá-las para modelos de IA (como GPT). Ele faz parte de um pipeline de processamento inteligente que otimiza as interações entre usuários e assistentes virtuais no WhatsApp.

### Funcionalidades Principais

- **Classificação Inteligente**: Categoriza mensagens em buckets (system, messages, user)
- **Detecção de Integrações**: Identifica necessidades de integração com APIs externas
- **Otimização de Prompts**: Ajusta prompts baseado no tipo de mensagem
- **Normalização de Texto**: Processa e limpa texto para análise
- **Configuração Dinâmica**: Ajusta parâmetros da IA baseado no contexto

## Arquitetura

### Componentes Principais

1. **API FastAPI**: Interface REST para recebimento de mensagens
2. **AnalisadorDeMensagem**: Classe principal para processamento
3. **Sistema de Classificação**: Lógica de categorização em buckets
4. **Detector de Integrações**: Identifica necessidades de APIs externas
5. **Gerador de Prompts**: Cria prompts otimizados para cada categoria

### Fluxo de Processamento

```
Mensagem de Entrada
       ↓
Extração do Payload
       ↓
Normalização do Texto
       ↓
Classificação (system/messages/user)
       ↓
Detecção de Integrações
       ↓
Geração de Prompts
       ↓
Configuração de Parâmetros da IA
       ↓
Resposta Estruturada
```

## Buckets de Classificação

### 1. **system** - Integrações e Ferramentas
**Critério**: Presença de palavras-chave relacionadas a sistemas externos

**Palavras-chave**:
- Documentos: documento, planilha, pdf, drive, icloud
- Calendário: calendario, agenda, evento, compromisso
- Reuniões: reuniao, meeting, encontro
- Integrações: api, oauth, google, apple, sync
- Financeiro: boleto, fatura, cobranca, pagamento

**Comportamento**:
- Temperature: ≤ 0.3 (respostas previsíveis)
- Max tokens: 900
- Modo integração ativo
- Solicita confirmação antes de usar APIs

**Exemplo**:
```json
{
  "message": "Preciso organizar uma reunião no google calendar",
  "classification": {
    "bucket": "system",
    "reasons": ["Palavras-chave de sistemas/APIs: google, reuniao"],
    "integrations": ["google"]
  }
}
```

### 2. **messages** - Perguntas Diretas
**Critérios**:
- Mensagens curtas (≤ 80 chars) terminadas com "?"
- Contém termos factuais: "que dia e hoje", "capital de", "quanto e"
- Perguntas objetivas que requerem respostas factuais

**Comportamento**:
- Temperature: ≤ 0.2 (máxima precisão)
- Max tokens: 400
- Respostas objetivas em 1-3 frases

**Exemplo**:
```json
{
  "message": "Qual é a capital do Brasil?",
  "classification": {
    "bucket": "messages",
    "reasons": ["Pergunta direta/fechada detectada."]
  }
}
```

### 3. **user** - Mensagens Complexas/Pessoais
**Critérios**:
- Mensagens longas (> 160 chars)
- Referências pessoais: "meu", "minha", "eu", "para mim"
- Pedidos de planejamento: "plano", "estratégia", "roteiro"
- Múltiplas frases (> 1 pontuação)

**Comportamento**:
- Temperature: 0.3-0.6 (permite criatividade)
- Max tokens: 900
- Até 2 perguntas para esclarecimento
- Respostas estruturadas em tópicos

**Exemplo**:
```json
{
  "message": "Preciso de um plano de estudos para aprender Python",
  "classification": {
    "bucket": "user",
    "reasons": ["Mensagem com necessidade de personalização/contexto."]
  }
}
```

## API Reference

### POST /preprocess

Processa e prepara uma mensagem para envio à IA.

#### Request Body

```json
{
  "message": "string",           // Mensagem do usuário (obrigatório)
  "ctx": {                       // Contexto opcional
    "lang": "pt|en",            // Idioma (default: auto-detect)
    "model": "string",          // Modelo da IA (default: gpt-4.1-mini)
    "temperature": 0.3          // Temperature base (default: 0.3)
  },
  "history": [                   // Histórico da conversa (opcional)
    {
      "role": "user|assistant",
      "content": "string"
    }
  ]
}
```

#### Response

```json
{
  "message": "string",                    // Mensagem original
  "ctx": {...},                          // Contexto original
  "mensagem_completa": "string",         // Mensagem extraída
  "texto_normalizado": "string",         // Texto normalizado para análise
  "openaiPayload": {                     // Payload pronto para OpenAI
    "model": "string",
    "messages": [...],
    "temperature": 0.3,
    "max_tokens": 400
  },
  "classification": {
    "bucket": "system|messages|user",   // Categoria identificada
    "reasons": ["string"],              // Motivos da classificação
    "integrations": ["string"]          // Integrações detectadas
  }
}
```

#### Status Codes

- **200**: Processamento bem-sucedido
- **400**: Payload vazio ou inválido

## Instalação e Configuração

### Requisitos

- Python 3.11+
- Docker (opcional)

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/thsethub/n8n-monique.git
cd n8n-monique

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor
uvicorn main:app --host 0.0.0.0 --port 8181
```

### Docker

```bash
# Build da imagem
docker build -t preproc-api .

# Execute o container
docker run -p 8181:8181 preproc-api
```

### Docker Compose

```bash
docker-compose up -d
```

## Configuração

### Variáveis de Ambiente

O serviço pode ser configurado através do payload de entrada. Não requer variáveis de ambiente externas.

### Configurações do Contexto

```json
{
  "ctx": {
    "lang": "pt",              // Força idioma português
    "model": "gpt-4-turbo",    // Modelo específico da OpenAI
    "temperature": 0.5         // Temperature customizada
  }
}
```

## Exemplos de Uso

### 1. Pergunta Simples

```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Que horas são?",
    "ctx": {"lang": "pt"}
  }'
```

### 2. Solicitação de Integração

```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crie um documento no Google Drive com o relatório mensal",
    "ctx": {"lang": "pt"}
  }'
```

### 3. Mensagem Complexa com Histórico

```bash
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Baseado na nossa conversa anterior, me ajude a criar um cronograma de estudos personalizado",
    "ctx": {"lang": "pt"},
    "history": [
      {"role": "user", "content": "Quero aprender programação"},
      {"role": "assistant", "content": "Que linguagem te interessa?"},
      {"role": "user", "content": "Python para análise de dados"}
    ]
  }'
```

## Testes

### Testes Manuais

Execute os exemplos acima para validar o funcionamento básico.

### Teste de Classificação

```python
# Teste de mensagem system
payload = {"message": "Agende uma reunião no meu calendario google"}
# Resultado esperado: bucket = "system", integrations = ["google"]

# Teste de mensagem messages  
payload = {"message": "Qual a capital da França?"}
# Resultado esperado: bucket = "messages"

# Teste de mensagem user
payload = {"message": "Preciso de um plano detalhado para reorganizar minha rotina de trabalho e estudos"}
# Resultado esperado: bucket = "user"
```

## Monitoramento e Logs

### Logs da Aplicação

O serviço utiliza o módulo `logging` padrão do Python:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Métricas

- Tempo de processamento por requisição
- Distribuição de buckets de classificação
- Integrações mais solicitadas

## Deployment

### Produção

1. **Container Registry**: Push da imagem para registry
2. **Orquestração**: Deploy via Docker Swarm, Kubernetes, ou similar
3. **Load Balancer**: Configure balanceamento de carga
4. **Monitoring**: Configure monitoramento de saúde

### Exemplo Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: preproc-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: preproc-api
  template:
    metadata:
      labels:
        app: preproc-api
    spec:
      containers:
      - name: preproc-api
        image: thsethub/preproc-api:latest
        ports:
        - containerPort: 8181
---
apiVersion: v1
kind: Service
metadata:
  name: preproc-api-service
spec:
  selector:
    app: preproc-api
  ports:
  - port: 8181
    targetPort: 8181
  type: ClusterIP
```

## Troubleshooting

### Problemas Comuns

1. **Erro 400 - Payload vazio**
   - Verifique se o JSON está bem formatado
   - Certifique-se que o campo "message" existe

2. **Classificação incorreta**
   - Verifique as palavras-chave em `PALAVRAS_CHAVE_DE_SISTEMA`
   - Analise os logs para entender o motivo da classificação

3. **Integrações não detectadas**
   - Confirme se as palavras-chave estão na lista de detecção
   - Verifique a normalização do texto

### Debug

Para debug detalhado, ajuste o nível de log:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contribuição

### Estrutura do Código

- `main.py`: Código principal da aplicação
- `AnalisadorDeMensagem`: Classe principal de processamento
- `PALAVRAS_CHAVE_DE_SISTEMA`: Constantes para detecção de integrações

### Adicionando Novas Integrações

1. Adicione palavras-chave em `PALAVRAS_CHAVE_DE_SISTEMA`
2. Atualize a lógica em `_criar_prompts_de_sistema()`
3. Teste a detecção com mensagens de exemplo

### Modificando Critérios de Classificação

1. Ajuste os métodos `_e_pergunta_direta_e_objetiva()` e `_e_mensagem_complexa_ou_pessoal()`
2. Teste com diversos tipos de mensagem
3. Valide se a distribuição de buckets faz sentido

## License

[Inserir informações de licença apropriadas]

## Contato

Para dúvidas técnicas ou suporte, contate a equipe de desenvolvimento.