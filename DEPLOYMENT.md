# Guia de Deployment - Microsserviço de Pré-processamento

## Opções de Deployment

### 1. Docker (Recomendado)

#### Build Local
```bash
# Clone o repositório
git clone https://github.com/thsethub/n8n-monique.git
cd n8n-monique

# Build da imagem
docker build -t preproc-api:latest .

# Execute o container
docker run -d \
  --name preproc-api \
  -p 8181:8181 \
  --restart unless-stopped \
  preproc-api:latest
```

#### Docker Compose
```bash
# Execute com docker-compose
docker-compose up -d

# Verificar logs
docker-compose logs -f preproc-api

# Parar serviços
docker-compose down
```

### 2. Deploy Local (Desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar servidor
uvicorn main:app --host 0.0.0.0 --port 8181

# Ou com auto-reload para desenvolvimento
uvicorn main:app --host 0.0.0.0 --port 8181 --reload
```

### 3. Deploy em Cloud

#### Google Cloud Run
```bash
# Build e push para Container Registry
gcloud builds submit --tag gcr.io/[PROJECT-ID]/preproc-api

# Deploy no Cloud Run
gcloud run deploy preproc-api \
  --image gcr.io/[PROJECT-ID]/preproc-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8181 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

#### AWS ECS
```yaml
# task-definition.json
{
  "family": "preproc-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "preproc-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/preproc-api:latest",
      "portMappings": [
        {
          "containerPort": 8181,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/preproc-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Azure Container Instances
```bash
# Create resource group
az group create --name preproc-rg --location eastus

# Deploy container
az container create \
  --resource-group preproc-rg \
  --name preproc-api \
  --image your-registry/preproc-api:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8181 \
  --dns-name-label preproc-api-unique \
  --restart-policy Always
```

### 4. Kubernetes

#### Deployment YAML
```yaml
# k8s-deployment.yaml
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
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8181
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /docs
            port: 8181
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: preproc-api-service
spec:
  selector:
    app: preproc-api
  ports:
  - port: 80
    targetPort: 8181
  type: LoadBalancer
```

#### Deploy no Kubernetes
```bash
# Aplicar configuração
kubectl apply -f k8s-deployment.yaml

# Verificar status
kubectl get pods -l app=preproc-api
kubectl get services

# Ver logs
kubectl logs -l app=preproc-api

# Escalar
kubectl scale deployment preproc-api --replicas=5
```

## Configurações de Produção

### 1. Variáveis de Ambiente

```bash
# .env (opcional)
LOG_LEVEL=INFO
PORT=8181
WORKERS=1
HOST=0.0.0.0
```

### 2. Configuração do Uvicorn para Produção

```bash
# Múltiplos workers (recomendado para produção)
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8181 \
  --workers 4 \
  --log-level info \
  --access-log

# Ou com Gunicorn + Uvicorn workers
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8181 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
```

### 3. Nginx como Reverse Proxy

```nginx
# /etc/nginx/sites-available/preproc-api
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8181;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 4. SSL/TLS (Certbot)
```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d your-domain.com

# Auto-renovação
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoramento

### 1. Health Check Endpoint
```python
# Adicionar ao main.py se necessário
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }
```

### 2. Prometheus Metrics (Opcional)
```bash
# Instalar prometheus-fastapi-instrumentator
pip install prometheus-fastapi-instrumentator

# Adicionar ao main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 3. Logging Estruturado
```python
# Configuração avançada de logging
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_entry)

# Configurar logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

## Backup e Versionamento

### 1. Container Registry
```bash
# Tag com versão
docker tag preproc-api:latest preproc-api:v1.0.0

# Push para registry
docker push your-registry/preproc-api:v1.0.0
docker push your-registry/preproc-api:latest
```

### 2. Deploy com Zero Downtime
```bash
# Rolling update no Kubernetes
kubectl set image deployment/preproc-api preproc-api=your-registry/preproc-api:v1.1.0

# Verificar rollout
kubectl rollout status deployment/preproc-api

# Rollback se necessário
kubectl rollout undo deployment/preproc-api
```

## Performance Tuning

### 1. Recursos Recomendados

| Ambiente | CPU | Memória | Réplicas | RPS Suportado |
|----------|-----|---------|----------|---------------|
| Dev | 0.1 core | 128MB | 1 | ~50 |
| Staging | 0.2 core | 256MB | 2 | ~100 |
| Produção | 0.5 core | 512MB | 3-5 | ~300-500 |
| Alta Carga | 1 core | 1GB | 5-10 | ~1000+ |

### 2. Otimizações

#### Cache (Redis)
```python
# Implementar cache para classificações
import redis
import pickle

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_classification(text_hash):
    cached = redis_client.get(f"classification:{text_hash}")
    return pickle.loads(cached) if cached else None

def cache_classification(text_hash, result):
    redis_client.setex(f"classification:{text_hash}", 3600, pickle.dumps(result))
```

#### Connection Pooling
```python
# Para integrações externas futuras
import httpx

http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=httpx.Timeout(10.0)
)
```

## Testes de Carga

### 1. Teste Simples com curl
```bash
# Teste de carga básico
for i in {1..100}; do
  curl -s -X POST "http://localhost:8181/preprocess" \
    -H "Content-Type: application/json" \
    -d '{"message": "Teste de carga '$i'"}' &
done
wait
```

### 2. Teste com Apache Bench
```bash
# Instalar apache2-utils
sudo apt install apache2-utils

# Teste com ab
ab -n 1000 -c 10 -p test-payload.json -T "application/json" http://localhost:8181/preprocess
```

### 3. Teste com k6
```javascript
// test-load.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function() {
  let payload = JSON.stringify({
    message: "Teste de carga com k6"
  });

  let params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  let response = http.post('http://localhost:8181/preprocess', payload, params);
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

```bash
# Executar teste
k6 run test-load.js
```

## Troubleshooting

### 1. Problemas Comuns

#### Container não inicia
```bash
# Verificar logs
docker logs preproc-api

# Verificar se a porta está ocupada
netstat -tulpn | grep 8181

# Testar localmente
docker run -it --rm preproc-api:latest /bin/bash
```

#### Resposta lenta
```bash
# Verificar uso de recursos
docker stats preproc-api

# Verificar logs de erro
kubectl logs -l app=preproc-api --previous
```

#### Erro 500
```bash
# Logs detalhados
export LOG_LEVEL=DEBUG
uvicorn main:app --log-level debug

# Testar classificação específica
curl -X POST "http://localhost:8181/preprocess" \
  -H "Content-Type: application/json" \
  -d '{"message": "Mensagem que causa erro"}'
```

### 2. Monitoramento de Saúde

#### Script de Monitoramento
```bash
#!/bin/bash
# health-check.sh

URL="http://localhost:8181/docs"
TIMEOUT=5

if curl -f -s --max-time $TIMEOUT $URL > /dev/null; then
    echo "$(date): Service is healthy"
    exit 0
else
    echo "$(date): Service is down"
    exit 1
fi
```

#### Cronjob para Monitoramento
```bash
# Adicionar ao crontab
*/5 * * * * /path/to/health-check.sh >> /var/log/preproc-health.log 2>&1
```

## Segurança

### 1. Container Security
```dockerfile
# Dockerfile com usuário não-root
FROM python:3.11-slim

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# ... instalar dependências ...

USER appuser
```

### 2. Network Security
```bash
# Restringir acesso por IP (nginx)
location / {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://127.0.0.1:8181;
}
```

### 3. Rate Limiting
```python
# Implementar rate limiting básico
from collections import defaultdict
from time import time

request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time()
    
    # Limpar requests antigos (mais de 1 minuto)
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < 60
    ]
    
    # Verificar limite (100 requests por minuto)
    if len(request_counts[client_ip]) >= 100:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    request_counts[client_ip].append(now)
    response = await call_next(request)
    return response
```

---

## Checklist de Deploy

### Pré-deploy
- [ ] Código testado localmente
- [ ] Testes automatizados passando
- [ ] Dockerfile funcional
- [ ] Variáveis de ambiente configuradas
- [ ] Recursos de infraestrutura provisionados

### Deploy
- [ ] Build da imagem realizado
- [ ] Imagem enviada para registry
- [ ] Deploy executado
- [ ] Health check funcionando
- [ ] Logs sendo coletados

### Pós-deploy
- [ ] Teste de fumaça realizado
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Documentação atualizada
- [ ] Equipe notificada

### Rollback Plan
- [ ] Versão anterior identificada
- [ ] Processo de rollback testado
- [ ] Dados de backup disponíveis
- [ ] Checklist de rollback documentado