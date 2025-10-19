# 📐 Arquitetura do Módulo Analisador (Refatorado)

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Layer (routes.py)                            │
│                                                                         │
│  POST /preprocess  ──┐                                                 │
│  POST /webhook     ──┼──> AnalisadorDeMensagem                        │
│                      │                                                 │
└──────────────────────┼─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              AnalisadorPrincipal (Orquestrador)                        │
│                                                                         │
│  async def processar_mensagem():                                       │
│    1. Extrair mensagem                                                 │
│    2. Validar entrada                                                  │
│    3. ──> GerenciadorDeCache.obter_do_cache()                        │
│    4. ──> normalizar_texto()                                          │
│    5. ──> Classificador.determinar_categoria()                        │
│    6. ──> ConstrutorDePayload.construir_payload()                     │
│    7. ──> GerenciadorDeCache.salvar_no_cache()                        │
│    8. Retornar resposta completa                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Normalizador │ │ Gerenciador  │ │Classificador │ │  Construtor  │
│              │ │   de Cache   │ │              │ │  de Payload  │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│              │ │              │ │              │ │              │
│ normalizar_  │ │ gerar_cache_ │ │ determinar_  │ │ construir_   │
│ texto()      │ │ key()        │ │ categoria()  │ │ payload()    │
│              │ │              │ │              │ │              │
│ @lru_cache   │ │ obter_do_    │ │ _e_pergunta_ │ │ _criar_      │
│ (512 items)  │ │ cache()      │ │ direta()     │ │ prompts()    │
│              │ │              │ │              │ │              │
│ unidecode()  │ │ salvar_no_   │ │ _e_mensagem_ │ │ _selecionar_ │
│              │ │ cache()      │ │ complexa()   │ │ modelo_ia()  │
│              │ │              │ │              │ │              │
│              │ │ MD5 hashing  │ │ Priority:    │ │ _calcular_   │
│              │ │              │ │ 1. system    │ │ parametros() │
│              │ │ TTLCache     │ │ 2. messages  │ │              │
│              │ │ (1h, 1000)   │ │ 3. user      │ │ _obter_      │
│              │ │              │ │              │ │ historico()  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                           │              │
                                           ▼              ▼
                                  ┌──────────────┐ ┌──────────────┐
                                  │  Detector    │ │  Detector    │
                                  │  de Scopes   │ │  de Idioma   │
                                  ├──────────────┤ ├──────────────┤
                                  │              │ │              │
                                  │ detectar_    │ │ determinar_  │
                                  │ scopes()     │ │ idioma()     │
                                  │              │ │              │
                                  │ SCOPE_CACHE  │ │ Regex:       │
                                  │ (8 padrões)  │ │ - PT detect  │
                                  │              │ │ - EN detect  │
                                  │ Scopes:      │ │              │
                                  │ - gmail      │ │ Returns:     │
                                  │ - calendar   │ │ - "pt"       │
                                  │ - drive      │ │ - "en"       │
                                  │ - sheets     │ │              │
                                  │ - boleto     │ │              │
                                  └──────────────┘ └──────────────┘
                                           │
                                           ▼
                                  ┌──────────────┐
                                  │  Constantes  │
                                  ├──────────────┤
                                  │              │
                                  │ PALAVRAS_    │
                                  │ CHAVE_DE_    │
                                  │ SISTEMA      │
                                  │ (44 words)   │
                                  │              │
                                  │ SCOPE_CACHE  │
                                  │ (8 patterns) │
                                  │              │
                                  └──────────────┘
```

## 🔄 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                       REQUEST FLOW                              │
└─────────────────────────────────────────────────────────────────┘

1. HTTP Request (POST /preprocess)
   │
   ├─> payload: {
   │     "message": "enviar email para joão",
   │     "ctx": {"lang": "pt"},
   │     "history": []
   │   }
   │
   ▼
2. AnalisadorPrincipal.__init__(payload)
   │
   ├─> self.payload_original = payload
   ├─> self.contexto = payload.get("ctx", {})
   ├─> self.latencias = {}
   │
   ▼
3. processar_mensagem() [ASYNC]
   │
   ├─> [STEP 1] Extrair mensagem
   │   └─> mensagem_usuario = "enviar email para joão"
   │       Latência: ~0.0ms
   │
   ├─> [STEP 2] Verificar cache
   │   ├─> cache_key = MD5(normalize(mensagem))
   │   └─> resultado = GerenciadorDeCache.obter_do_cache(cache_key)
   │       Latência: ~0.03-4ms
   │       └─> Se HIT: retorna resultado cacheado (FIM)
   │
   ├─> [STEP 3] Normalizar texto
   │   ├─> texto_normalizado = normalizar_texto(mensagem)
   │   └─> "enviar email para joao" (sem acento, minúsculas)
   │       Latência: ~0.0ms (LRU cached)
   │
   ├─> [STEP 4] Classificar mensagem
   │   ├─> Classificador.determinar_categoria(mensagem, texto_norm)
   │   ├─> Verifica PALAVRAS_CHAVE_DE_SISTEMA
   │   └─> categoria = "system", motivos = ["email detectado"]
   │       Latência: ~0.01ms
   │
   ├─> [STEP 5] Construir payload
   │   ├─> ConstrutorDePayload.construir_payload(...)
   │   ├──> DetectorDeIdioma.determinar_idioma(mensagem)
   │   │    └─> idioma = "pt"
   │   ├──> DetectorDeScopes.detectar_scopes(texto_norm)
   │   │    ├─> Busca em SCOPE_CACHE
   │   │    └─> scopes = ["https://mail.google.com/"]
   │   ├──> _criar_prompts_de_sistema(categoria, idioma, scopes)
   │   ├──> _selecionar_modelo_ia(categoria)
   │   │    └─> modelo = "gpt-4.1-mini"
   │   ├──> _calcular_parametros_da_ia(categoria)
   │   │    └─> {temperature: 0.3, max_tokens: 900}
   │   └──> payload_openai = {model, messages, temperature, max_tokens}
   │       Latência: ~0.01ms
   │
   ├─> [STEP 6] Salvar no cache
   │   └─> GerenciadorDeCache.salvar_no_cache(cache_key, resposta)
   │
   ▼
4. Retornar resposta completa
   │
   └─> {
         "mensagem_completa": "enviar email para joão",
         "texto_normalizado": "enviar email para joao",
         "openaiPayload": {...},
         "classification": {
           "bucket": "system",
           "reasons": [...],
           "scope": ["https://mail.google.com/"]
         },
         "performance": {
           "extracao_ms": 0.0,
           "cache_lookup_ms": 0.03,
           "normalizacao_ms": 0.0,
           "classificacao_ms": 0.01,
           "construcao_payload_ms": 0.01,
           "total_ms": 0.06
         }
       }
```

## 🧩 Dependências Entre Módulos

```
AnalisadorPrincipal
    ├── usa → Normalizador
    │   └── depende de: unidecode, functools.lru_cache
    │
    ├── usa → GerenciadorDeCache
    │   └── depende de: hashlib, app.core.metrics, app.core.config
    │
    ├── usa → Classificador
    │   ├── depende de: app.utils.regex (7 patterns)
    │   └── depende de: Constantes (PALAVRAS_CHAVE_DE_SISTEMA)
    │
    └── usa → ConstrutorDePayload
        ├── usa → DetectorDeIdioma
        │   └── depende de: app.utils.regex (3 patterns)
        │
        ├── usa → DetectorDeScopes
        │   └── depende de: Constantes (SCOPE_CACHE)
        │
        └── depende de: contexto, payload_original

Constantes
    └── independente (apenas dados estáticos)

Normalizador
    └── independente (apenas unidecode)
```

## 📊 Matriz de Responsabilidades

| Módulo                | Responsabilidade Principal | LOC | Dependências |
|-----------------------|---------------------------|-----|--------------|
| **analisador_principal** | Orquestração do fluxo | 124 | 5 módulos |
| **classificador**     | Categorização de mensagens | 89 | 2 módulos |
| **construtor_payload** | Montagem payload OpenAI | 149 | 3 módulos |
| **detector_scopes**   | Detecção de integrações | 101 | 1 módulo |
| **detector_idioma**   | Detecção de idioma | 22 | 1 módulo |
| **gerenciador_cache** | Operações de cache | 58 | 3 módulos |
| **normalizador**      | Normalização de texto | 24 | 1 pacote |
| **constantes**        | Dados estáticos | 54 | 0 |
| **TOTAL**             | - | **621** | - |

## 🎯 Padrões de Design Aplicados

### 1. **Single Responsibility Principle (SRP)**
Cada módulo tem uma responsabilidade única e bem definida.

### 2. **Dependency Injection**
`ConstrutorDePayload` recebe contexto e payload via construtor.

### 3. **Strategy Pattern**
Seleção de modelo e parâmetros baseada na categoria.

### 4. **Facade Pattern**
`AnalisadorPrincipal` é a fachada que orquestra todos os componentes.

### 5. **Cache Pattern**
- LRU cache para normalização (hot path)
- TTL cache para resultados completos

### 6. **Factory Pattern**
`ConstrutorDePayload` cria diferentes payloads baseado em categoria.

## 🚀 Pontos de Extensão

### Adicionar Nova Categoria
```python
# Em classificador.py
def determinar_categoria(...):
    # ... lógica existente ...
    
    # NOVA CATEGORIA
    if self._e_mensagem_tecnica(texto_normalizado):
        return "technical", ["Mensagem técnica detectada"]
```

### Adicionar Novo Scope
```python
# Em constantes.py
SCOPE_CACHE: Dict[str, List[str]] = {
    # ... scopes existentes ...
    
    # NOVO SCOPE
    "criar tarefa": ["https://www.googleapis.com/auth/tasks"],
}
```

### Adicionar Novo Detector
```python
# Criar detector_sentimento.py
class DetectorDeSentimento:
    @staticmethod
    def detectar_sentimento(texto: str) -> str:
        # ... lógica de detecção ...
        return "positivo"  # ou "negativo", "neutro"

# Importar em construtor_payload.py
from .detector_sentimento import DetectorDeSentimento
```

## 📈 Métricas de Qualidade

### Complexidade Ciclomática (por módulo)
- **analisador_principal**: 6 (Baixa)
- **classificador**: 8 (Média)
- **construtor_payload**: 10 (Média)
- **detector_scopes**: 12 (Média-Alta)
- **detector_idioma**: 3 (Muito Baixa)
- **gerenciador_cache**: 4 (Baixa)
- **normalizador**: 2 (Muito Baixa)
- **constantes**: 1 (Muito Baixa)

### Coesão
✅ **Alta**: Cada módulo tem métodos relacionados a uma única responsabilidade

### Acoplamento
✅ **Baixo**: Módulos dependem de interfaces, não de implementações concretas

---

**Legenda do Diagrama**:
- `──>` : Fluxo de dados
- `└──>` : Dependência/chamada de método
- `[STEP N]` : Etapa numerada do processamento
- `~Xms` : Latência média em milissegundos
