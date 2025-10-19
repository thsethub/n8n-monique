# Módulo Analisador de Mensagens

Este módulo é responsável por toda a lógica de análise, classificação e preparação de mensagens para a API do OpenAI.

## Estrutura Modular

```
analisador/
├── __init__.py                  # Exporta AnalisadorDeMensagem
├── analisador_principal.py      # Orquestração principal
├── classificador.py             # Classificação de mensagens
├── construtor_payload.py        # Construção de payloads OpenAI
├── detector_scopes.py           # Detecção de integrações
├── detector_idioma.py           # Detecção de idioma
├── gerenciador_cache.py         # Operações de cache
├── normalizador.py              # Normalização de texto
├── constantes.py                # Constantes e configurações
└── README.md                    # Esta documentação
```

## Componentes

### 1. AnalisadorPrincipal (`analisador_principal.py`)
**Responsabilidade**: Orquestração de todo o processo de análise.

**Principais métodos**:
- `processar_mensagem()` - Método principal assíncrono que coordena todas as etapas
- `_extrair_mensagem_do_payload()` - Extração e limpeza da mensagem
- `_construir_payload_de_erro_para_entrada_vazia()` - Tratamento de erros

**Fluxo de execução**:
1. Extrai mensagem do payload
2. Valida entrada
3. Consulta cache
4. Normaliza texto
5. Classifica mensagem
6. Constrói payload para IA
7. Salva no cache
8. Retorna resposta completa

### 2. Classificador (`classificador.py`)
**Responsabilidade**: Classificar mensagens em categorias.

**Categorias**:
- `system` - Mensagens que requerem integrações (calendário, email, documentos)
- `messages` - Perguntas diretas e objetivas
- `user` - Mensagens complexas ou pessoais

**Métodos principais**:
- `determinar_categoria()` - Classifica a mensagem
- `_e_pergunta_direta_e_objetiva()` - Detecta perguntas factuais
- `_e_mensagem_complexa_ou_pessoal()` - Detecta complexidade

### 3. DetectorDeScopes (`detector_scopes.py`)
**Responsabilidade**: Detectar quais integrações (scopes) são necessárias.

**Scopes suportados**:
- `https://mail.google.com/` - Email
- `https://www.googleapis.com/auth/calendar` - Calendário
- `https://www.googleapis.com/auth/spreadsheets` - Planilhas
- `https://www.googleapis.com/auth/drive` - Drive/Documentos
- `boleto` - Sistema de boletos

**Otimizações**:
- Cache de padrões conhecidos para performance máxima
- Priorização contextual (evita scopes desnecessários)
- Detecção de múltiplas intenções explícitas

### 4. ConstrutorDePayload (`construtor_payload.py`)
**Responsabilidade**: Construir payloads otimizados para OpenAI.

**Funcionalidades**:
- Seleção automática de modelo (gpt-4o-mini ou gpt-4.1-mini)
- Ajuste dinâmico de temperature
- Limitação de tokens por categoria
- Gerenciamento de histórico de conversa (últimas 3 mensagens)
- Criação de prompts de sistema contextualizados

### 5. DetectorDeIdioma (`detector_idioma.py`)
**Responsabilidade**: Detectar o idioma da mensagem.

**Idiomas suportados**:
- Português (pt)
- Inglês (en)

**Método**: Usa regex pré-compiladas para performance.

### 6. GerenciadorDeCache (`gerenciador_cache.py`)
**Responsabilidade**: Gerenciar cache de classificações.

**Características**:
- TTLCache com 1 hora de validade
- Capacidade máxima de 1000 itens
- Chaves baseadas em hash MD5
- Métricas de cache hits/misses

### 7. Normalizador (`normalizador.py`)
**Responsabilidade**: Normalizar texto para análise.

**Operações**:
- Conversão para minúsculas
- Remoção de acentos (usando unidecode)
- Cache LRU (512 itens) para evitar reprocessamento

### 8. Constantes (`constantes.py`)
**Responsabilidade**: Armazenar todas as constantes do módulo.

**Conteúdo**:
- `PALAVRAS_CHAVE_DE_SISTEMA` - 44 palavras-chave para detecção de integrações
- `SCOPE_CACHE` - 8 padrões conhecidos para lookup rápido

## Métricas de Performance

O módulo mede latência em cada etapa:
- **extracao_ms** - Tempo de extração da mensagem
- **cache_lookup_ms** - Tempo de consulta ao cache
- **normalizacao_ms** - Tempo de normalização
- **classificacao_ms** - Tempo de classificação
- **construcao_payload_ms** - Tempo de construção do payload
- **total_ms** - Tempo total de processamento

**Performance típica**:
- Cache hit: ~0.15ms
- Cache miss: 0.4-0.8ms

## Exemplo de Uso

```python
from app.services.analisador import AnalisadorDeMensagem

# Criar instância
payload = {
    "message": "enviar email para joão",
    "ctx": {"lang": "pt", "temperature": 0.3},
    "history": []
}

analisador = AnalisadorDeMensagem(payload)

# Processar mensagem (assíncrono)
resultado = await analisador.processar_mensagem()

# Resultado contém:
# - mensagem_completa
# - texto_normalizado
# - openaiPayload (pronto para envio)
# - classification (bucket, reasons, scope)
# - performance (métricas de latência)
```

## Vantagens da Estrutura Modular

1. **Manutenibilidade** ✅
   - Cada componente tem responsabilidade única
   - Fácil localizar e modificar funcionalidades específicas

2. **Testabilidade** ✅
   - Cada módulo pode ser testado isoladamente
   - Mocks e stubs são mais simples

3. **Legibilidade** ✅
   - Código organizado em arquivos de ~80-150 linhas
   - Nomes descritivos e documentação clara

4. **Extensibilidade** ✅
   - Fácil adicionar novos detectores ou classificadores
   - Novos scopes podem ser adicionados em constantes.py

5. **Performance** ✅
   - Mantém todas as otimizações originais
   - Cache, regex pré-compiladas, LRU cache preservados

## Regras de Desenvolvimento

1. **Não altere a lógica funcional** - A estrutura modular deve manter 100% de equivalência com o código original
2. **Mantenha as otimizações** - Cache, regex pré-compiladas e LRU devem ser preservados
3. **Documente mudanças** - Sempre atualize este README ao adicionar componentes
4. **Testes obrigatórios** - Novos componentes devem ter testes unitários

## Migração do Código Original

O arquivo `app/services/analisador.py` original (544 linhas) foi dividido em 8 módulos menores:

- `analisador_principal.py` - 124 linhas (orquestração)
- `classificador.py` - 89 linhas (classificação)
- `construtor_payload.py` - 149 linhas (payload OpenAI)
- `detector_scopes.py` - 101 linhas (scopes)
- `detector_idioma.py` - 22 linhas (idioma)
- `gerenciador_cache.py` - 58 linhas (cache)
- `normalizador.py` - 24 linhas (normalização)
- `constantes.py` - 54 linhas (configurações)

**Total**: 621 linhas (vs 544 originais) - ~15% de overhead em comentários e imports, mas muito mais organizado!
