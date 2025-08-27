# Changelog - Microsserviço de Pré-processamento

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-08-27

### Adicionado
- **Documentação técnica completa do microsserviço**
  - README.md com visão geral e guia de uso
  - ARCHITECTURE.md com detalhes técnicos da arquitetura
  - API.md com documentação completa da API
  - DEPLOYMENT.md com guias de implantação
  - CHANGELOG.md para controle de versões

- **Melhorias na documentação do código**
  - Docstrings detalhadas em todas as classes e métodos
  - Comentários explicativos sobre a lógica de classificação
  - Exemplos de uso em docstrings
  - Documentação dos parâmetros e retornos

- **Testes básicos de funcionalidade**
  - test_basic.py com testes abrangentes
  - Validação de classificação de mensagens
  - Testes de detecção de integrações
  - Verificação de cálculo de parâmetros
  - Testes de detecção de idioma

- **Configurações de desenvolvimento**
  - .gitignore para ignorar arquivos temporários
  - Configurações aprimoradas do FastAPI
  - Versionamento da API

### Funcionalidades Existentes Documentadas

#### Sistema de Classificação de Mensagens
- **Bucket "system"**: Para mensagens que requerem integrações
  - Detecção por palavras-chave: documento, planilha, calendário, reunião, etc.
  - Parâmetros: temperature ≤ 0.3, max_tokens = 900
  - Prompts específicos para modo integração

- **Bucket "messages"**: Para perguntas diretas e objetivas
  - Critérios: mensagens curtas com "?" ou termos factuais
  - Parâmetros: temperature ≤ 0.2, max_tokens = 400
  - Prompts para respostas objetivas

- **Bucket "user"**: Para mensagens complexas e personalizadas
  - Critérios: mensagens longas, referências pessoais, pedidos de planejamento
  - Parâmetros: temperature 0.3-0.6, max_tokens = 900
  - Prompts para respostas estruturadas

#### Detecção de Integrações
- **Google**: Drive, Calendar, Docs, Sheets
- **Apple**: iCloud, Notes
- **Financeiro**: Boletos, faturas, cobranças

#### Funcionalidades de Processamento
- **Normalização de texto**: Remoção de acentos e conversão para minúsculas
- **Detecção de idioma**: Português e inglês baseado em padrões
- **Histórico de conversa**: Suporte a contexto histórico (últimas 6 mensagens)
- **Configuração dinâmica**: Parâmetros ajustáveis via contexto

### Melhorias Técnicas

#### Arquitetura
- Padrões de design implementados: SRP, Strategy, Template Method, Factory
- Separação clara de responsabilidades
- Código modular e extensível

#### Performance
- Uso de Set para lookup O(1) de palavras-chave
- Regex otimizadas
- Controle de memória com histórico limitado

#### Documentação
- OpenAPI/Swagger automático
- Documentação interativa em /docs e /redoc
- Exemplos práticos de uso
- Guias de deployment para múltiplas plataformas

### Estrutura de Arquivos
```
/
├── main.py                 # Código principal da aplicação
├── requirements.txt        # Dependências Python
├── Dockerfile             # Configuração Docker
├── docker-compose.yml     # Orquestração Docker
├── .gitignore            # Arquivos ignorados pelo Git
├── test_basic.py         # Testes básicos de funcionalidade
├── README.md             # Documentação principal
├── ARCHITECTURE.md       # Documentação técnica da arquitetura
├── API.md               # Documentação da API
├── DEPLOYMENT.md        # Guias de implantação
└── CHANGELOG.md         # Histórico de mudanças
```

### Endpoints da API
- `POST /preprocess`: Processamento principal de mensagens
- `GET /docs`: Documentação interativa (Swagger)
- `GET /redoc`: Documentação alternativa (ReDoc)

### Dependências Principais
- **FastAPI 0.116.1**: Framework web moderno
- **Uvicorn 0.35.0**: Servidor ASGI
- **Unidecode 1.4.0**: Normalização de texto
- **httpx 0.28.1**: Cliente HTTP assíncrono
- **Pydantic 2.11.7**: Validação de dados

### Métricas de Qualidade
- ✅ 100% dos endpoints documentados
- ✅ Docstrings em todas as funções públicas
- ✅ Testes cobrindo cenários principais
- ✅ Exemplos práticos de uso
- ✅ Guias de deployment

### Compatibilidade
- **Python**: 3.11+
- **Docker**: Compatível com images slim
- **Plataformas**: Linux, macOS, Windows
- **Cloud**: AWS, GCP, Azure compatível
- **Kubernetes**: Manifests incluídos

---

## Versões Futuras (Roadmap)

### [1.1.0] - Planejado
- Cache Redis para classificações frequentes
- Métricas Prometheus/Grafana
- Rate limiting implementado
- Testes de integração automatizados

### [1.2.0] - Planejado
- Suporte a mais idiomas (ES, FR)
- Classificação baseada em ML/embeddings
- Batch processing para múltiplas mensagens
- API de configuração dinâmica

### [2.0.0] - Futuro
- Refatoração para microserviços
- Suporte a plugins de integração
- Dashboard de administração
- Análise de sentimento

---

## Convenções de Versionamento

### Formato: MAJOR.MINOR.PATCH

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Funcionalidades adicionadas de forma compatível
- **PATCH**: Correções de bugs compatíveis

### Tipos de Mudanças

- **Adicionado**: Para novas funcionalidades
- **Alterado**: Para mudanças em funcionalidades existentes
- **Depreciado**: Para funcionalidades que serão removidas
- **Removido**: Para funcionalidades removidas
- **Corrigido**: Para correção de bugs
- **Segurança**: Para vulnerabilidades

---

## Como Contribuir

### Para desenvolvedores:
1. Faça fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Para documentação:
1. Atualize README.md, API.md ou ARCHITECTURE.md conforme necessário
2. Adicione exemplos práticos quando possível
3. Mantenha a consistência no formato
4. Teste os exemplos fornecidos

### Para reports de bugs:
1. Verifique se o bug já foi reportado
2. Inclua passos para reproduzir o problema
3. Adicione logs relevantes
4. Especifique versão e ambiente

---

## Licença

[Especificar licença do projeto]

## Autores

- **thsethub** - Desenvolvimento inicial e documentação

## Agradecimentos

- Comunidade FastAPI pela excelente documentação
- Contribuidores do projeto n8n pela inspiração
- Equipe de desenvolvimento pela revisão