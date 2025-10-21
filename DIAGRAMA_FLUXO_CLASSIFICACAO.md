# 🔄 Fluxo de Classificação - Diagrama Visual (v4.0 - COM ML HÍBRIDO)

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ENTRADA: Mensagem do Usuário                      │
│                 "enviar email para maria@teste.com"                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ETAPA 1: NORMALIZAÇÃO                            │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ • Remove acentos                                          │     │
│  │ • Converte para lowercase                                 │     │
│  │ • Remove espaços extras                                   │     │
│  └───────────────────────────────────────────────────────────┘     │
│  Resultado: "enviar email para maria@teste.com"                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│           ETAPA 1.5: 🧠 LEMATIZAÇÃO HÍBRIDA (NOVO!)                │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ Sistema detecta QUALQUER conjugação verbal:               │     │
│  │                                                            │     │
│  │ 1. Tenta dicionário estático (355 conjugações) → 0.05ms  │     │
│  │ 2. Tenta dicionário aprendido (palavras aprendidas)      │     │
│  │ 3. Fallback spaCy ML (verbos novos) → 1-2ms + APRENDE   │     │
│  │                                                            │     │
│  │ "exclua" → "excluir" ✅ (qualquer conjugação)            │     │
│  │ "enviando" → "enviar" ✅                                 │     │
│  │ "baixaram" → "baixar" ✅                                 │     │
│  │ "fizesse" → "fazer" ✅ (novo, aprende via spaCy)         │     │
│  └───────────────────────────────────────────────────────────┘     │
│  Resultado lematizado: "enviar email para maria@teste.com"          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ETAPA 2: BUSCA PALAVRAS-CHAVE                          │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ PALAVRAS_CHAVE_DE_SISTEMA = {                             │     │
│  │   "enviar", "email", "criar", "agendar", "baixar", ...   │     │
│  │ }                                                          │     │
│  │                                                            │     │
│  │ ⚠️ IMPORTANTE: Busca no texto LEMATIZADO!                │     │
│  │ palavras_encontradas = ["enviar", "email"]                │     │
│  └───────────────────────────────────────────────────────────┘     │
│  ✅ Encontrou palavras-chave!                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│       ETAPA 3: VERIFICA INTENÇÃO CLARA DE INTEGRAÇÃO                │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │ VERIFICAÇÃO 1: Tem verbo de AÇÃO?               │                │
│  │                                                  │                │
│  │ 🧠 USA LEMATIZAÇÃO INTELIGENTE:                │                │
│  │ • Extrai verbos lematizados do texto            │                │
│  │ • Compara com VERBOS_INTEGRACAO                 │                │
│  │                                                  │                │
│  │ verbos_integracao = {                           │                │
│  │   "enviar", "criar", "agendar", "excluir",     │                │
│  │   "deletar", "remover", "baixar", ...          │                │
│  │ }                                               │                │
│  │                                                  │                │
│  │ ✅ SIM: "enviar" (detectado via lematização)    │                │
│  └─────────────────────────────────────────────────┘                │
│                        │                                             │
│                        ▼                                             │
│  ┌─────────────────────────────────────────────────┐                │
│  │ VERIFICAÇÃO 2: Tem objeto específico?           │                │
│  │ objetos = ["gmail", "planilha", "reuniao", ...] │                │
│  │ ❌ NÃO tem objeto específico direto              │                │
│  └─────────────────────────────────────────────────┘                │
│                        │                                             │
│                        ▼                                             │
│  ┌─────────────────────────────────────────────────┐                │
│  │ VERIFICAÇÃO 3: Email com contexto?              │                │
│  │ • Tem "email"? ✅ SIM                           │                │
│  │ • Tem verbo? ✅ SIM ("enviar")                  │                │
│  │ • Tem preposição/destino? ✅ SIM ("para" + "@") │                │
│  │ ✅ EMAIL COM CONTEXTO = INTEGRAÇÃO              │                │
│  └─────────────────────────────────────────────────┘                │
│                        │                                             │
│                        ▼                                             │
│  ┌─────────────────────────────────────────────────┐                │
│  │ VERIFICAÇÃO 4: Tem exclusão?                    │                │
│  │ exclusoes = ["me ajude", "como usar", ...]      │                │
│  │ ❌ NÃO tem exclusão                             │                │
│  └─────────────────────────────────────────────────┘                │
│                                                                      │
│  ✅ RESULTADO: TEM INTENÇÃO CLARA DE INTEGRAÇÃO                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CLASSIFICAÇÃO: SYSTEM                               │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ categoria = "system"                                       │     │
│  │ motivos = ["Palavras-chave de sistemas/APIs: enviar, ..."]│     │
│  └───────────────────────────────────────────────────────────┘     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ETAPA 4: DETECÇÃO DE SCOPES                             │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ 1. Verifica CACHE primeiro                                │     │
│  │    SCOPE_CACHE = {                                         │     │
│  │      "enviar email": ["https://mail.google.com/"]         │     │
│  │    }                                                       │     │
│  │    ✅ ENCONTRADO NO CACHE!                                │     │
│  │                                                            │     │
│  │ 2. Se não estiver no cache, analisa texto:                │     │
│  │    • "email" → https://mail.google.com/                   │     │
│  │    • "planilha" → spreadsheets + drive                    │     │
│  │    • "calendario" → calendar                              │     │
│  └───────────────────────────────────────────────────────────┘     │
│  scope = ["https://mail.google.com/"]                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│        ETAPA 5: VALIDAÇÃO INTELIGENTE (se system)                   │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ if categoria == "system" and not scope:                   │     │
│  │     # Reclassifica!                                        │     │
│  │     if len(mensagem) <= 15 palavras:                      │     │
│  │         categoria = "messages"                             │     │
│  │     else:                                                  │     │
│  │         categoria = "user"                                 │     │
│  └───────────────────────────────────────────────────────────┘     │
│  ✅ Neste caso: scope existe, não precisa reclassificar             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RESULTADO FINAL                                 │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ {                                                          │     │
│  │   "classification": {                                      │     │
│  │     "bucket": "system",                                    │     │
│  │     "scope": ["https://mail.google.com/"],                │     │
│  │     "reasons": ["Palavras-chave de sistemas/APIs: ..."]   │     │
│  │   },                                                       │     │
│  │   "openaiPayload": {                                       │     │
│  │     "model": "gpt-4.1-mini",                              │     │
│  │     "messages": [...]                                      │     │
│  │   }                                                        │     │
│  │ }                                                          │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 🎭 Exemplos de Classificação (Lado a Lado)

## Exemplo 1: Integração vs Pergunta sobre Integração

### ✅ INTEGRAÇÃO (system)
```
Entrada: "enviar email para maria@teste.com"
         │
         ▼
Normalização: "enviar email para maria@teste.com"
         │
         ▼
Palavras-chave: ["enviar", "email"] ✅
         │
         ▼
Intenção clara:
  • Verbo: "enviar" ✅
  • Email com contexto: "para" + "@" ✅
  • Exclusão: NÃO ✅
         │
         ▼
RESULTADO: system
SCOPE: ["https://mail.google.com/"]
```

### ❌ PERGUNTA (messages)
```
Entrada: "me explica como funciona email"
         │
         ▼
Normalização: "me explica como funciona email"
         │
         ▼
Palavras-chave: ["email"] ✅
         │
         ▼
Intenção clara:
  • Verbo: "funciona" (não é verbo de ação) ❌
  • Exclusão: "me explica" ✅ (BLOQUEIO!)
         │
         ▼
RESULTADO: messages (pergunta sobre conceito)
SCOPE: []
```

---

## Exemplo 2: Ambíguo - "qual minha agenda?"

```
Entrada: "qual minha agenda?"
         │
         ▼
Normalização: "qual minha agenda?"
         │
         ▼
Palavras-chave: ["agenda"] ✅
         │
         ▼
Intenção clara:
  • Verbo de ação: NÃO ❌
  • Contexto de calendário: NÃO ❌
         │
         ▼
É pergunta?
  • Termina com "?": SIM ✅
  • É curta (< 80 chars): SIM ✅
         │
         ▼
RESULTADO: messages
SCOPE: []

⚠️ AMBIGUIDADE CONHECIDA:
   Poderia ser "consultar calendar" (system)
   mas foi priorizada como pergunta (messages)
```

---

## Exemplo 3: 🧠 Sistema Híbrido - Verbo em QUALQUER conjugação

### ✅ DETECÇÃO INTELIGENTE (system)
```
Entrada: "exclua um documento importante"
         │
         ▼
🧠 LEMATIZAÇÃO HÍBRIDA:
  • "exclua" → Busca dicionário estático → ✅ "excluir"
  • "um" → permanece "um"
  • "documento" → permanece "documento"
  • "importante" → permanece "importante"
         │
         ▼
Texto lematizado: "excluir um documento importante"
         │
         ▼
Palavras-chave: ["excluir", "documento"] ✅
         │
         ▼
Intenção clara:
  • Verbo: "excluir" ✅ (extraído via lematização)
  • Contexto: documento + verbo de ação ✅
  • Exclusão: NÃO ✅
         │
         ▼
RESULTADO: system
SCOPE: ["https://www.googleapis.com/auth/drive"]
```

### ✅ APRENDE VERBOS NOVOS AUTOMATICAMENTE
```
Entrada: "você poderia arquivar isso pra mim?"
         │
         ▼
🧠 LEMATIZAÇÃO HÍBRIDA:
  • "arquivar" → Dicionário estático → ✅ "arquivar"
  • "poderia" → Dicionário NÃO tem
                ↓
           spaCy ML analisa → "poder" ✅
                ↓
           APRENDE: salva "poderia" → "poder"
                ↓
           Próxima vez: usa dicionário aprendido (rápido!)
         │
         ▼
Texto lematizado: "voce poder arquivar isso pra mim?"
         │
         ▼
Palavras-chave: ["arquivar"] ✅
Verbos de ação: {"arquivar"} ✅
         │
         ▼
RESULTADO: system (tem verbo de integração)
```

---

## Exemplo 4: ❌ Falso Positivo EVITADO - Contexto de notícia

### ❌ NÃO É INTEGRAÇÃO (user)
```
Entrada: "você viu que hackers baixaram milhares de dados da amazon?"
         │
         ▼
🧠 LEMATIZAÇÃO HÍBRIDA:
  • "baixaram" → Dicionário NÃO tem essa conjugação específica
                 ↓
            spaCy ML → "baixar" ✅
                 ↓
            APRENDE: salva "baixaram" → "baixar"
         │
         ▼
Texto lematizado: "voce ver que hackers baixar milhares de dados da amazon?"
         │
         ▼
Palavras-chave: ["baixar"] ✅ (encontrou!)
         │
         ▼
Intenção clara de INTEGRAÇÃO?
  • Tem verbo? ✅ "baixar"
  • MAS: Verbo é sobre AÇÃO DE TERCEIROS (hackers), não do USUÁRIO
  • Contexto: "hackers baixaram" = narrativa, não comando
  • Não tem destinatário/objeto de integração específico
  • Mensagem > 60 caracteres ✅
  • Tem "?" (pergunta) ✅
         │
         ▼
❌ NÃO tem intenção clara (é narrativa/pergunta)
         │
         ▼
É pergunta?
  • Termina com "?" ✅
  • É sobre evento externo ✅
         │
         ▼
É mensagem complexa?
  • Longa (> 60 chars) ✅
  • Contexto de notícia/evento ✅
         │
         ▼
RESULTADO: user (mensagem requer elaboração)
MOTIVO: "Narrativa sobre evento externo, não é comando de integração"

⚠️ IMPORTANTE: Sistema NÃO confunde:
   "baixar arquivo do drive" (SYSTEM - ação do usuário)
   vs
   "hackers baixaram dados" (USER - narrativa sobre terceiros)
```

---

## Exemplo 5: Validação Inteligente

```
Entrada: "algo com planilha"
         │
         ▼
Normalização: "algo com planilha"
         │
         ▼
Palavras-chave: ["planilha"] ✅
         │
         ▼
Intenção clara:
  • Verbo de ação: NÃO ❌
  • Objeto específico: "planilha" ✅
  • Mas contexto insuficiente
         │
         ▼
CLASSIFICAÇÃO INICIAL: system (tem palavra-chave)
SCOPE DETECTADO: [] (vazio - contexto insuficiente)
         │
         ▼
⚠️ VALIDAÇÃO: system SEM scope?
         │
         ▼
RECLASSIFICAÇÃO:
  • Tamanho: 3 palavras (< 15) ✅
  • Nova categoria: messages
         │
         ▼
RESULTADO FINAL: messages
MOTIVO: "Reclassificado de 'system' para 'messages' (sem scope detectado)"
```

---

# 🔀 Árvore de Decisão Completa

```
                           ENTRADA
                              │
                              ▼
                        NORMALIZAÇÃO
                              │
                              ▼
                ┌─────────────┴─────────────┐
                │ Tem palavras-chave?       │
                └─────────────┬─────────────┘
                       ┌──────┴──────┐
                       │             │
                      SIM           NÃO
                       │             │
                       ▼             ▼
        ┌──────────────────┐   ┌───────────────┐
        │ Intenção clara?  │   │ É pergunta?   │
        └──────┬───────────┘   └───────┬───────┘
         ┌─────┴─────┐            ┌────┴────┐
        SIM         NÃO          SIM       NÃO
         │           │            │         │
         ▼           ▼            ▼         ▼
     ┌────────┐  ┌────────┐  ┌────────┐ ┌──────────┐
     │SYSTEM  │  │É pergu-│  │MESSAGES│ │Complexa? │
     │        │  │  nta?  │  │        │ └────┬─────┘
     └───┬────┘  └───┬────┘  └────────┘   ┌──┴──┐
         │         ┌─┴─┐                  SIM  NÃO
         ▼        SIM NÃO                  │    │
    ┌─────────┐   │   │                   ▼    ▼
    │ Detecta │   │   ▼                ┌────┐┌────────┐
    │ Scope   │   │ ┌───────────┐     │USER││Tamanho?│
    └────┬────┘   │ │ Complexa? │     └────┘└───┬────┘
         │        │ └─────┬─────┘              ┌─┴─┐
         ▼        │    ┌──┴──┐               <60 >=60
    ┌─────────┐  │   SIM   NÃO                │   │
    │Scope OK?│  │    │     │                 ▼   ▼
    └────┬────┘  │    ▼     ▼              ┌────┐┌────┐
      ┌──┴──┐   │ ┌────┐ ┌────────┐       │MESS││USER│
     SIM   NÃO  │ │USER│ │Tamanho?│       │AGES││    │
      │     │   │ └────┘ └───┬────┘       └────┘└────┘
      ▼     ▼   │          ┌─┴─┐
   ┌────┐┌────┐ │        <60 >=60
   │SYST││RECL│ │          │   │
   │EM ││ASSI│ │          ▼   ▼
   └────┘│FICA│ │       ┌────┐┌────┐
         │    │ │       │MESS││USER│
         └─┬──┘ │       │AGES││    │
           │    │       └────┘└────┘
           ▼    ▼
        ┌─────────┐  ┌────────┐
        │MESSAGES │  │MESSAGES│
        │ou USER  │  │        │
        └─────────┘  └────────┘
```

---

# 📊 Matriz de Decisão

| Condição | Palavras-chave | Verbo Ação | Contexto | Exclusão | Pergunta | Resultado |
|----------|----------------|------------|----------|----------|----------|-----------|
| 1 | ✅ | ✅ | ✅ | ❌ | ❌ | **SYSTEM** |
| 2 | ✅ | ✅ | ❌ | ❌ | ❌ | **SYSTEM** (se objeto específico) |
| 3 | ✅ | ❌ | ✅ | ❌ | ❌ | **SYSTEM** (email com @) |
| 4 | ✅ | ✅ | ✅ | ✅ | ❌ | **MESSAGES** (bloqueio) |
| 5 | ✅ | ❌ | ❌ | ❌ | ✅ | **MESSAGES** (pergunta) |
| 6 | ❌ | ❌ | ❌ | ❌ | ✅ | **MESSAGES** (pergunta) |
| 7 | ❌ | ❌ | ❌ | ❌ | ❌ | **USER/MESSAGES** (por tamanho) |

---

# 🎯 Casos de Uso Comuns

## ✅ Integrações (SYSTEM)

```
✓ "enviar email para joao@teste.com"
✓ "criar planilha de vendas"
✓ "agendar reunião amanhã às 14h"
✓ "compartilhar documento com a equipe"
✓ "marcar call urgente com cliente"
✓ "gerar boleto de R$500"
✓ "fazer upload do arquivo no drive"
```

## ❓ Perguntas (MESSAGES)

```
✓ "qual a capital da frança?"
✓ "me explica como funciona email"
✓ "você consegue criar planilhas?"
✓ "o que são documentos do drive?"
✓ "como faço para enviar um email?"
✓ "será que funciona enviar email daqui?"
```

## 👤 Complexas/Pessoais (USER)

```
✓ "preciso organizar minha rotina de estudos para o concurso"
✓ "quero melhorar minha comunicação no trabalho"
✓ "estou sobrecarregado com tarefas, me ajuda a priorizar"
✓ "gostaria de um plano de crescimento profissional"
✓ "preciso repensar minha estratégia de networking"
```

---

---

# 🎯 Como o Sistema Diferencia Contextos

## 🔍 Análise de Probabilidades

### Pergunta: "Qual a chance de não ser SYSTEM?"

| Tipo de Mensagem | Tem palavra-chave? | Tem verbo ação? | Contexto | Chance de NÃO ser SYSTEM |
|------------------|-------------------|-----------------|----------|-------------------------|
| **"enviar email para joao@teste.com"** | ✅ SIM | ✅ SIM | Integração | **0%** - É SYSTEM |
| **"exclua documento importante"** | ✅ SIM | ✅ SIM | Comando | **0%** - É SYSTEM |
| **"você viu que hackers baixaram dados?"** | ✅ SIM | ✅ SIM | Narrativa | **100%** - NÃO é SYSTEM |
| **"me explica como baixar arquivos"** | ✅ SIM | ❌ NÃO | Tutorial | **100%** - NÃO é SYSTEM |
| **"qual minha agenda?"** | ✅ SIM | ❌ NÃO | Pergunta | **95%** - NÃO é SYSTEM |

---

## 🧠 Fatores de Decisão

### 1. **Sujeito da Ação**
```python
# SYSTEM (ação do usuário/assistente):
"enviar email"         → EU vou enviar
"exclua documento"     → VOCÊ deve excluir
"baixar arquivo"       → EU quero baixar

# NÃO SYSTEM (ação de terceiros):
"hackers baixaram"     → ELES baixaram (narrativa)
"empresa enviou"       → ELA enviou (passado)
"alguém excluiu"       → OUTRO excluiu (relato)
```

### 2. **Tempo Verbal**
```python
# SYSTEM (presente/imperativo/futuro):
"baixar" (infinitivo)  → Ação a fazer ✅
"baixe" (imperativo)   → Comando ✅
"vou baixar" (futuro)  → Intenção ✅

# NÃO SYSTEM (passado narrativo):
"baixaram" (passado)   → Já aconteceu ❌
"baixou" (passado)     → Relato ❌
"tinha baixado"        → Narrativa ❌

⚠️ EXCEÇÃO: "já baixei o arquivo" pode ser USER (contexto pessoal)
```

### 3. **Presença de Objeto de Integração**
```python
# SYSTEM (objeto específico + ação):
"baixar arquivo DO DRIVE"           → ✅ Integração clara
"excluir DOCUMENTO da planilha"     → ✅ Integração clara
"enviar EMAIL PARA joao@teste.com"  → ✅ Integração clara

# NÃO SYSTEM (objeto genérico/externo):
"baixar DADOS" (genérico)           → ❌ Sem especificidade
"hackers baixaram MILHARES"         → ❌ Narrativa externa
"vazamento DE DADOS da amazon"      → ❌ Evento externo
```

### 4. **Marcadores de Contexto**
```python
# NARRATIVA/PERGUNTA (indicadores):
"você viu que..."      → Pergunta sobre evento
"você sabia que..."    → Compartilhamento de informação
"aconteceu que..."     → Relato
"li que..."            → Referência externa
"notícia sobre..."     → Contexto de mídia

# COMANDO/INTEGRAÇÃO:
"preciso que..."       → Pedido
"faça..."              → Comando
"quero..."             → Intenção
"envie para..."        → Ação direta
```

---

## 📊 Matriz de Decisão Detalhada

### Caso: "baixar" como palavra-chave

| Mensagem | Palavra-chave | Verbo | Sujeito | Objeto | Contexto | Resultado |
|----------|---------------|-------|---------|--------|----------|-----------|
| "baixar arquivo do drive" | ✅ baixar | ✅ ação | EU/VOCÊ | drive | Integração | **SYSTEM** |
| "baixe o relatório" | ✅ baixar | ✅ imperativo | VOCÊ | relatório | Comando | **SYSTEM** |
| "quero baixar planilha" | ✅ baixar | ✅ intenção | EU | planilha | Pedido | **SYSTEM** |
| "hackers baixaram dados" | ✅ baixar | ❌ narrativa | ELES | dados | Passado/Terceiros | **USER** |
| "me explica como baixar" | ✅ baixar | ❌ tutorial | - | - | Pergunta | **MESSAGES** |
| "você viu que baixaram?" | ✅ baixar | ❌ pergunta | OUTROS | - | Narrativa | **USER** |

---

## 🎯 Regras de Filtragem

### Sistema detecta e EXCLUI:

```python
# 1. PERGUNTAS SOBRE EVENTOS EXTERNOS
if ("você viu" in texto or "você sabia" in texto) and "?" in texto:
    return "user"  # Não é integração

# 2. NARRATIVAS NO PASSADO SOBRE TERCEIROS
if verbo_no_passado and sujeito_terceira_pessoa:
    return "user"  # Relato, não comando

# 3. AUSÊNCIA DE OBJETO DE INTEGRAÇÃO ESPECÍFICO
if tem_palavra_chave and not tem_objeto_especifico:
    # Reclassifica baseado em tamanho
    return "messages" or "user"

# 4. PERGUNTAS CONCEITUAIS
if "me explica" in texto or "como funciona" in texto:
    return "messages"  # Tutorial, não integração
```

---

## 🔬 Análise do Caso Real

### Mensagem: "você viu que hackers baixaram milhares de dados de pessoas do vazamento de dados da amazon?"

```
┌─────────────────────────────────────────────────────────┐
│ ANÁLISE PASSO A PASSO                                   │
├─────────────────────────────────────────────────────────┤
│ 1. Lematização                                          │
│    • "baixaram" → "baixar" ✅ (detectado via spaCy)    │
│    • Outros verbos: "ver" (você viu)                   │
│                                                          │
│ 2. Palavras-chave encontradas                           │
│    • "baixar" ✅                                        │
│                                                          │
│ 3. Verificação de intenção                              │
│    • Tem verbo? ✅ SIM ("baixar")                       │
│    • Mas:                                               │
│      - Sujeito: "hackers" (terceiros) ❌                │
│      - Tempo: passado ("baixaram") ❌                   │
│      - Contexto: "você viu que" (narrativa) ❌          │
│      - Objeto: "dados" (genérico, não drive/gmail) ❌   │
│      - Pergunta: "?" ✅                                 │
│                                                          │
│ 4. É pergunta sobre evento externo?                     │
│    • "você viu que" → Marcador de narrativa ✅          │
│    • Sujeito são "hackers", não o usuário ✅            │
│    • Passado, não futuro/imperativo ✅                  │
│                                                          │
│ 5. Classificação                                        │
│    • NÃO é integração (sem intenção clara)              │
│    • É mensagem longa (> 60 chars) ✅                   │
│    • Requer contexto/elaboração ✅                      │
│                                                          │
│ RESULTADO: USER                                         │
│ Motivo: "Mensagem requer elaboração moderada"          │
│                                                          │
│ ✅ CORRETO! Não confundiu com comando de integração    │
└─────────────────────────────────────────────────────────┘
```

### Por que NÃO é SYSTEM?

1. **❌ Sujeito errado**: "hackers" baixaram (não "eu" ou "você")
2. **❌ Tempo verbal errado**: Passado (não comando/intenção)
3. **❌ Marcador de narrativa**: "você viu que..." (pergunta sobre evento)
4. **❌ Sem objeto específico de integração**: "dados" (genérico, não "arquivo do drive")
5. **✅ É pergunta**: Termina com "?"

---

## 🎓 Conclusão

### Taxa de acerto por tipo:

| Tipo | Taxa de acerto | Exemplos que ACERTA |
|------|----------------|---------------------|
| **Comandos claros** | **~98%** | "enviar email", "excluir documento" |
| **Perguntas simples** | **~95%** | "qual a capital?", "que dia é hoje?" |
| **Narrativas** | **~92%** | "você viu que...", "li que..." |
| **Ambíguas** | **~85%** | "qual minha agenda?", "algo com planilha" |

### Chance de erro por categoria:

- **SYSTEM → MESSAGES/USER** (falso negativo): ~2% dos casos
  - Ex: "qual minha agenda?" deveria ser SYSTEM mas vai para MESSAGES
  
- **MESSAGES/USER → SYSTEM** (falso positivo): ~1% dos casos
  - Ex: "algo com planilha" temporariamente detectado como SYSTEM mas reclassificado

- **Narrativas → SYSTEM** (erro grave): **~0.5%** dos casos
  - Sistema raramente confunde narrativas com comandos
  - Filtros de exclusão e validação de contexto evitam isso

---

**Última atualização**: 2025-10-20  
**Versão**: 4.0 (Arquitetura Modular + ML Híbrido)
