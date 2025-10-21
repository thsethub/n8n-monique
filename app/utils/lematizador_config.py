"""
Configuração do sistema de lematização híbrido.
"""

class LematizadorConfig:
    """Configurações do sistema de lematização inteligente."""
    
    # ========================================================================
    # MODO DE OPERAÇÃO
    # ========================================================================
    
    # Modo: "hybrid" (recomendado), "dict-only", "spacy-only"
    MODE = "hybrid"
    
    # ========================================================================
    # CACHE
    # ========================================================================
    
    # Tamanho do cache LRU
    CACHE_SIZE = 2000
    
    # ========================================================================
    # APRENDIZADO DINÂMICO
    # ========================================================================
    
    # Habilita aprendizado automático
    ENABLE_LEARNING = True
    
    # Tamanho do batch para salvar (evita I/O excessivo)
    BATCH_SAVE_SIZE = 10
    
    # Caminho do arquivo de verbos aprendidos
    LEARNED_DICT_FILE = "data/learned_verbs.json"
    
    # ========================================================================
    # spaCy
    # ========================================================================
    
    # Lazy loading (carrega só quando necessário)
    SPACY_LAZY_LOAD = True
    
    # Modelo spaCy a usar (pt_core_news_sm, pt_core_news_md, pt_core_news_lg)
    # sm = pequeno (43MB), md = médio (138MB), lg = grande (545MB)
    SPACY_MODEL = "pt_core_news_sm"
    
    # Fallback gracioso se spaCy não disponível
    SPACY_FALLBACK_TO_DICT = True
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    # Nível de log para lematizador
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    # Log de palavras aprendidas
    LOG_LEARNED_WORDS = True
    
    # ========================================================================
    # PERFORMANCE
    # ========================================================================
    
    # Thread-safety para ambientes multi-threaded
    THREAD_SAFE = True
    
    # Pré-aquecimento: carrega spaCy na inicialização (False = lazy)
    PRELOAD_SPACY = False
