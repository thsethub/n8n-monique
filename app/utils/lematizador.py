"""
Módulo de lematização de verbos em português.
Normaliza diferentes conjugações verbais para sua forma infinitiva.

Sistema Híbrido Inteligente:
1. Dicionário estático (verbos comuns - rápido)
2. Dicionário dinâmico (verbos aprendidos - rápido)
3. spaCy fallback (verbos novos - inteligente)
4. Aprendizado automático (salva verbos novos descobertos)
"""
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Set, Optional
from threading import Lock

# Configuração de logging
logger = logging.getLogger(__name__)

# ============================================================================
# MAPEAMENTO DE CONJUGAÇÕES PARA INFINITIVO
# ============================================================================

# Verbos de ação (sistema/APIs) com suas variações mais comuns
MAPEAMENTO_VERBOS: Dict[str, str] = {
    # ENVIAR
    "enviar": "enviar",
    "envie": "enviar",
    "envia": "enviar",
    "enviando": "enviar",
    "enviado": "enviar",
    "enviada": "enviar",
    "enviei": "enviar",
    "enviou": "enviar",
    "enviaram": "enviar",
    
    # CRIAR
    "criar": "criar",
    "crie": "criar",
    "cria": "criar",
    "criando": "criar",
    "criado": "criar",
    "criada": "criar",
    "criei": "criar",
    "criou": "criar",
    "criaram": "criar",
    
    # AGENDAR
    "agendar": "agendar",
    "agende": "agendar",
    "agenda": "agendar",
    "agendando": "agendar",
    "agendado": "agendar",
    "agendada": "agendar",
    "agendei": "agendar",
    "agendou": "agendar",
    "agendaram": "agendar",
    
    # MARCAR
    "marcar": "marcar",
    "marque": "marcar",
    "marca": "marcar",
    "marcando": "marcar",
    "marcado": "marcar",
    "marcada": "marcar",
    "marquei": "marcar",
    "marcou": "marcar",
    "marcaram": "marcar",
    
    # EXCLUIR
    "excluir": "excluir",
    "exclua": "excluir",
    "exclui": "excluir",
    "excluindo": "excluir",
    "excluido": "excluir",
    "excluida": "excluir",
    "exclui": "excluir",
    "excluiu": "excluir",
    "excluiram": "excluir",
    
    # DELETAR
    "deletar": "deletar",
    "delete": "deletar",
    "deleta": "deletar",
    "deletando": "deletar",
    "deletado": "deletar",
    "deletada": "deletar",
    "deletei": "deletar",
    "deletou": "deletar",
    "deletaram": "deletar",
    
    # REMOVER
    "remover": "remover",
    "remova": "remover",
    "remove": "remover",
    "removendo": "remover",
    "removido": "remover",
    "removida": "remover",
    "removi": "remover",
    "removeu": "remover",
    "removeram": "remover",
    
    # COMPARTILHAR
    "compartilhar": "compartilhar",
    "compartilhe": "compartilhar",
    "compartilha": "compartilhar",
    "compartilhando": "compartilhar",
    "compartilhado": "compartilhar",
    "compartilhada": "compartilhar",
    "compartilhei": "compartilhar",
    "compartilhou": "compartilhar",
    "compartilharam": "compartilhar",
    
    # EDITAR
    "editar": "editar",
    "edite": "editar",
    "edita": "editar",
    "editando": "editar",
    "editado": "editar",
    "editada": "editar",
    "editei": "editar",
    "editou": "editar",
    "editaram": "editar",
    
    # ATUALIZAR
    "atualizar": "atualizar",
    "atualize": "atualizar",
    "atualiza": "atualizar",
    "atualizando": "atualizar",
    "atualizado": "atualizar",
    "atualizada": "atualizar",
    "atualizei": "atualizar",
    "atualizou": "atualizar",
    "atualizaram": "atualizar",
    
    # MODIFICAR
    "modificar": "modificar",
    "modifique": "modificar",
    "modifica": "modificar",
    "modificando": "modificar",
    "modificado": "modificar",
    "modificada": "modificar",
    "modifiquei": "modificar",
    "modificou": "modificar",
    "modificaram": "modificar",
    
    # RESPONDER
    "responder": "responder",
    "responda": "responder",
    "responde": "responder",
    "respondendo": "responder",
    "respondido": "responder",
    "respondida": "responder",
    "respondi": "responder",
    "respondeu": "responder",
    "responderam": "responder",
    
    # ENCAMINHAR
    "encaminhar": "encaminhar",
    "encaminhe": "encaminhar",
    "encaminha": "encaminhar",
    "encaminhando": "encaminhar",
    "encaminhado": "encaminhar",
    "encaminhada": "encaminhar",
    "encaminhei": "encaminhar",
    "encaminhou": "encaminhar",
    "encaminharam": "encaminhar",
    
    # ARQUIVAR
    "arquivar": "arquivar",
    "arquive": "arquivar",
    "arquiva": "arquivar",
    "arquivando": "arquivar",
    "arquivado": "arquivar",
    "arquivada": "arquivar",
    "arquivei": "arquivar",
    "arquivou": "arquivar",
    "arquivaram": "arquivar",
    
    # BAIXAR / FAZER DOWNLOAD
    "baixar": "baixar",
    "baixe": "baixar",
    "baixa": "baixar",
    "baixando": "baixar",
    "baixado": "baixar",
    "baixada": "baixar",
    "baixei": "baixar",
    "baixou": "baixar",
    "baixaram": "baixar",
    "download": "baixar",
    "fazer download": "baixar",
    
    # FAZER UPLOAD
    "upload": "fazer upload",
    "fazer upload": "fazer upload",
    "subir": "fazer upload",
    "suba": "fazer upload",
    "sobe": "fazer upload",
    "subindo": "fazer upload",
    "subido": "fazer upload",
    "subida": "fazer upload",
    "subi": "fazer upload",
    "subiu": "fazer upload",
    "subiram": "fazer upload",
    
    # BUSCAR / PROCURAR / PESQUISAR
    "buscar": "buscar",
    "busque": "buscar",
    "busca": "buscar",
    "buscando": "buscar",
    "buscado": "buscar",
    "buscada": "buscar",
    "busquei": "buscar",
    "buscou": "buscar",
    "buscaram": "buscar",
    "procurar": "buscar",
    "procure": "buscar",
    "procura": "buscar",
    "procurando": "buscar",
    "pesquisar": "buscar",
    "pesquise": "buscar",
    "pesquisa": "buscar",
    "pesquisando": "buscar",
    
    # LISTAR
    "listar": "listar",
    "liste": "listar",
    "lista": "listar",
    "listando": "listar",
    "listado": "listar",
    "listada": "listar",
    "listei": "listar",
    "listou": "listar",
    "listaram": "listar",
    
    # CONSULTAR
    "consultar": "consultar",
    "consulte": "consultar",
    "consulta": "consultar",
    "consultando": "consultar",
    "consultado": "consultar",
    "consultada": "consultar",
    "consultei": "consultar",
    "consultou": "consultar",
    "consultaram": "consultar",
    
    # VER / VISUALIZAR
    "ver": "ver",
    "veja": "ver",
    "ve": "ver",
    "vendo": "ver",
    "visto": "ver",
    "vista": "ver",
    "vi": "ver",
    "viu": "ver",
    "viram": "ver",
    "visualizar": "ver",
    "visualize": "ver",
    "visualiza": "ver",
    "visualizando": "ver",
    
    # ABRIR
    "abrir": "abrir",
    "abra": "abrir",
    "abre": "abrir",
    "abrindo": "abrir",
    "aberto": "abrir",
    "aberta": "abrir",
    "abri": "abrir",
    "abriu": "abrir",
    "abriram": "abrir",
    
    # FECHAR
    "fechar": "fechar",
    "feche": "fechar",
    "fecha": "fechar",
    "fechando": "fechar",
    "fechado": "fechar",
    "fechada": "fechar",
    "fechei": "fechar",
    "fechou": "fechar",
    "fecharam": "fechar",
    
    # CANCELAR
    "cancelar": "cancelar",
    "cancele": "cancelar",
    "cancela": "cancelar",
    "cancelando": "cancelar",
    "cancelado": "cancelar",
    "cancelada": "cancelar",
    "cancelei": "cancelar",
    "cancelou": "cancelar",
    "cancelaram": "cancelar",
    
    # REAGENDAR
    "reagendar": "reagendar",
    "reagende": "reagendar",
    "reagenda": "reagendar",
    "reagendando": "reagendar",
    "reagendado": "reagendar",
    "reagendada": "reagendar",
    "reagendei": "reagendar",
    "reagendou": "reagendar",
    "reagendaram": "reagendar",
    
    # MANDAR (sinônimo de enviar)
    "mandar": "mandar",
    "mande": "mandar",
    "manda": "mandar",
    "mandando": "mandar",
    "mandado": "mandar",
    "mandada": "mandar",
    "mandei": "mandar",
    "mandou": "mandar",
    "mandaram": "mandar",
    
    # DISPARAR (enviar automático)
    "disparar": "disparar",
    "dispare": "disparar",
    "dispara": "disparar",
    "disparando": "disparar",
    "disparado": "disparar",
    "disparada": "disparar",
    "disparei": "disparar",
    "disparou": "disparar",
    "dispararam": "disparar",
    
    # RESERVAR (agendar recursos)
    "reservar": "reservar",
    "reserve": "reservar",
    "reserva": "reservar",
    "reservando": "reservar",
    "reservado": "reservar",
    "reservada": "reservar",
    "reservei": "reservar",
    "reservou": "reservar",
    "reservaram": "reservar",
    
    # PRODUZIR (criar/gerar)
    "produzir": "produzir",
    "produza": "produzir",
    "produz": "produzir",
    "produzindo": "produzir",
    "produzido": "produzir",
    "produzida": "produzir",
    "produzi": "produzir",
    "produziu": "produzir",
    "produziram": "produzir",
    
    # SINCRONIZAR
    "sincronizar": "sincronizar",
    "sincronize": "sincronizar",
    "sincroniza": "sincronizar",
    "sincronizando": "sincronizar",
    "sincronizado": "sincronizar",
    "sincronizada": "sincronizar",
    "sincronizei": "sincronizar",
    "sincronizou": "sincronizar",
    "sincronizaram": "sincronizar",
    
    # FAZER (genérico)
    "fazer": "fazer",
    "faca": "fazer",
    "faz": "fazer",
    "fazendo": "fazer",
    "feito": "fazer",
    "feita": "fazer",
    "fiz": "fazer",
    "fez": "fazer",
    "fizeram": "fazer",
    
    # GERAR
    "gerar": "gerar",
    "gere": "gerar",
    "gera": "gerar",
    "gerando": "gerar",
    "gerado": "gerar",
    "gerada": "gerar",
    "gerei": "gerar",
    "gerou": "gerar",
    "geraram": "gerar",
    
    # EMITIR
    "emitir": "emitir",
    "emita": "emitir",
    "emite": "emitir",
    "emitindo": "emitir",
    "emitido": "emitir",
    "emitida": "emitir",
    "emiti": "emitir",
    "emitiu": "emitir",
    "emitiram": "emitir",
    
    # PAGAR
    "pagar": "pagar",
    "pague": "pagar",
    "paga": "pagar",
    "pagando": "pagar",
    "pago": "pagar",
    "paga": "pagar",
    "paguei": "pagar",
    "pagou": "pagar",
    "pagaram": "pagar",
    
    # TRANSFERIR
    "transferir": "transferir",
    "transfira": "transferir",
    "transfere": "transferir",
    "transferindo": "transferir",
    "transferido": "transferir",
    "transferida": "transferir",
    "transferi": "transferir",
    "transferiu": "transferir",
    "transferiram": "transferir",
    
    # ORGANIZAR
    "organizar": "organizar",
    "organize": "organizar",
    "organiza": "organizar",
    "organizando": "organizar",
    "organizado": "organizar",
    "organizada": "organizar",
    "organizei": "organizar",
    "organizou": "organizar",
    "organizaram": "organizar",
    
    # ADICIONAR
    "adicionar": "adicionar",
    "adicione": "adicionar",
    "adiciona": "adicionar",
    "adicionando": "adicionar",
    "adicionado": "adicionar",
    "adicionada": "adicionar",
    "adicionei": "adicionar",
    "adicionou": "adicionar",
    "adicionaram": "adicionar",
    
    # INSERIR
    "inserir": "inserir",
    "insira": "inserir",
    "insere": "inserir",
    "inserindo": "inserir",
    "inserido": "inserir",
    "inserida": "inserir",
    "inseri": "inserir",
    "inseriu": "inserir",
    "inseriram": "inserir",
    
    # ANEXAR
    "anexar": "anexar",
    "anexe": "anexar",
    "anexa": "anexar",
    "anexando": "anexar",
    "anexado": "anexar",
    "anexada": "anexar",
    "anexei": "anexar",
    "anexou": "anexar",
    "anexaram": "anexar",
    
    # COPIAR
    "copiar": "copiar",
    "copie": "copiar",
    "copia": "copiar",
    "copiando": "copiar",
    "copiado": "copiar",
    "copiada": "copiar",
    "copiei": "copiar",
    "copiou": "copiar",
    "copiaram": "copiar",
    
    # MOVER
    "mover": "mover",
    "mova": "mover",
    "move": "mover",
    "movendo": "mover",
    "movido": "mover",
    "movida": "mover",
    "movi": "mover",
    "moveu": "mover",
    "moveram": "mover",
    
    # SALVAR
    "salvar": "salvar",
    "salve": "salvar",
    "salva": "salvar",
    "salvando": "salvar",
    "salvo": "salvar",
    "salva": "salvar",
    "salvei": "salvar",
    "salvou": "salvar",
    "salvaram": "salvar",
    
    # IMPRIMIR
    "imprimir": "imprimir",
    "imprima": "imprimir",
    "imprime": "imprimir",
    "imprimindo": "imprimir",
    "impresso": "imprimir",
    "impressa": "imprimir",
    "imprimi": "imprimir",
    "imprimiu": "imprimir",
    "imprimiram": "imprimir",
    
    # EXPORTAR
    "exportar": "exportar",
    "exporte": "exportar",
    "exporta": "exportar",
    "exportando": "exportar",
    "exportado": "exportar",
    "exportada": "exportar",
    "exportei": "exportar",
    "exportou": "exportar",
    "exportaram": "exportar",
    
    # IMPORTAR
    "importar": "importar",
    "importe": "importar",
    "importa": "importar",
    "importando": "importar",
    "importado": "importar",
    "importada": "importar",
    "importei": "importar",
    "importou": "importar",
    "importaram": "importar",
}

# Conjunto de verbos infinitivos para validação rápida
VERBOS_INFINITIVOS: Set[str] = set(MAPEAMENTO_VERBOS.values())

# Adiciona sinônimos importantes que são usados como consulta
# (mesmo que sejam mapeados para outros verbos internamente)
VERBOS_INFINITIVOS.update([
    "subir",           # sinônimo de "fazer upload"
    "fazer download",  # sinônimo de "baixar"
])


# ============================================================================
# DICIONÁRIOS DE CONTEXTO PARA CLASSIFICAÇÃO
# ============================================================================

# Objetos específicos que indicam integração com sistemas/APIs
OBJETOS_INTEGRACAO: Set[str] = {
    # Email - menções específicas
    "gmail",
    "destinatario",
    "assunto",
    # Docs - tipos específicos
    "planilha",
    "sheet",
    "excel",
    "slide",
    "apresentacao",
    "google docs",
    "google drive",
    # Calendário - contextos claros
    "reuniao",
    "meeting",
    "compromisso",
    "evento",
    # Pagamentos
    "boleto",
    "pagamento",
    "cobranca",
    "fatura",
    "pix",
    # Armazenamento
    "backup",
    "upload",
    "download",
    "sincronizar",
    # Documento/arquivos em contextos claros de sistema
    "rascunho",
}

# Contextos que tornam "email" uma integração
CONTEXTOS_EMAIL: Set[str] = {
    "para", "pro", "@", "ao", "do", "da",
    "mensagem por", "um email", "um e-mail", "uma mensagem",
    "agora", "enviar", "automatica",
    "maria", "joao", ".com", "teste.com",
}

# Contextos que tornam "compartilhar" uma integração
CONTEXTOS_COMPARTILHAR: Set[str] = {
    "equipe", "time", "com", "para",
    "documento", "planilha", "arquivo", "drive",
}

# Contextos de agendamento/marcação
CONTEXTOS_AGENDAMENTO: Set[str] = {
    "call", "reuniao", "meeting", "as ", "h", "hr", ":",
    "cliente", "urgente", "hoje", "amanha", "semana",
    "aula", "evento", "compromisso", "para mim", "sala",
    "segunda", "terca", "quarta", "quinta", "sexta",
}

# Contextos de cancelamento/reagendamento
CONTEXTOS_CANCELAMENTO: Set[str] = {
    "agendamento", "reuniao", "meeting", "compromisso", "evento",
    "marcado", "marcada", "agendado", "agendada", "call", "aula",
}

# Exclusões - frases que NÃO são integração (mesmo com verbos/objetos)
EXCLUSOES_INTEGRACAO: Set[str] = {
    # Perguntas sobre funcionalidades
    "o que vc pode fazer",
    "o que voce pode fazer",
    "o que pode fazer",
    "quais funcoes",
    "quais funcionalidades",
    # Ajuda genérica
    "me ajude",
    "me ajuda",
    " help ",
    " ajuda ",
    # Saudações
    " oi ",
    " ola ",
    " oie ",
    " opa ",
    # Ações sobre conceitos (não sobre ferramentas)
    "melhorar meu email",
    "organizar meus documentos",
    "organizar minhas",
    "organizar meu",
    # Perguntas sobre datas/tempo
    "qual a data",
    "que data",
    "data de hoje",
    "data hoje",
    "agendar meu tempo",
    "agendar tempo",
    # Meta-perguntas
    "o que fazer",
    "como fazer",
    "que fazer",
    # Perguntas de aprendizado
    "como usar",
    "tutorial",
    "aprender",
    "estudar",
    "entender sobre",
    "dicas de",
    "como nomear",
    "como organizar",
    "boas praticas",
    "otimizar meu",
    "configurar",
}


# ============================================================================
# SISTEMA DE APRENDIZADO DINÂMICO
# ============================================================================

# Caminho para arquivo de verbos aprendidos
LEARNED_DICT_PATH = Path("data/learned_verbs.json")

# Dicionário dinâmico (carregado do arquivo + novos aprendizados)
DICIONARIO_APRENDIDO: Dict[str, str] = {}

# Lock para thread-safety ao salvar
_save_lock = Lock()

# Contador para batch save (evita salvar a cada palavra)
_palavras_desde_ultimo_save = 0
BATCH_SAVE_SIZE = 10  # Salva a cada 10 palavras novas


def carregar_dicionario_aprendido() -> None:
    """
    Carrega verbos aprendidos de execuções anteriores.
    Chamado automaticamente na inicialização do módulo.
    """
    global DICIONARIO_APRENDIDO
    
    if not LEARNED_DICT_PATH.exists():
        logger.info("📚 Arquivo de verbos aprendidos não encontrado. Criando novo...")
        return
    
    try:
        with open(LEARNED_DICT_PATH, 'r', encoding='utf-8') as f:
            DICIONARIO_APRENDIDO = json.load(f)
        
        logger.info(f"✅ Carregou {len(DICIONARIO_APRENDIDO)} verbos aprendidos de execuções anteriores")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dicionário aprendido: {e}")
        DICIONARIO_APRENDIDO = {}


def salvar_dicionario_aprendido(force: bool = False) -> None:
    """
    Salva verbos aprendidos em arquivo JSON.
    
    Args:
        force: Se True, salva imediatamente (ignora batch)
    """
    global _palavras_desde_ultimo_save
    
    # Batch save: só salva a cada N palavras (performance)
    if not force and _palavras_desde_ultimo_save < BATCH_SAVE_SIZE:
        return
    
    with _save_lock:
        try:
            # Cria diretório se não existir
            LEARNED_DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva com formatação legível
            with open(LEARNED_DICT_PATH, 'w', encoding='utf-8') as f:
                json.dump(
                    DICIONARIO_APRENDIDO,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True
                )
            
            _palavras_desde_ultimo_save = 0
            logger.debug(f"💾 Salvou {len(DICIONARIO_APRENDIDO)} verbos aprendidos")
        
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dicionário aprendido: {e}")


def adicionar_ao_dicionario_aprendido(palavra: str, lemma: str) -> None:
    """
    Adiciona uma palavra nova ao dicionário aprendido.
    
    Args:
        palavra: Palavra original (conjugação)
        lemma: Forma lematizada (infinitivo)
    """
    global _palavras_desde_ultimo_save
    
    if palavra not in DICIONARIO_APRENDIDO:
        DICIONARIO_APRENDIDO[palavra] = lemma
        _palavras_desde_ultimo_save += 1
        
        logger.debug(f"🧠 Aprendeu: '{palavra}' → '{lemma}'")
        
        # Salva em batch
        salvar_dicionario_aprendido()


# ============================================================================
# INTEGRAÇÃO COM spaCy (LAZY LOADING)
# ============================================================================

_nlp = None
_spacy_disponivel = None


def _verificar_spacy_disponivel() -> bool:
    """
    Verifica se spaCy está instalado e modelo português disponível.
    """
    global _spacy_disponivel
    
    if _spacy_disponivel is not None:
        return _spacy_disponivel
    
    try:
        import spacy
        # Tenta carregar modelo português
        spacy.load("pt_core_news_sm")
        _spacy_disponivel = True
        logger.info("✅ spaCy disponível com modelo pt_core_news_sm")
        return True
    except (ImportError, OSError):
        _spacy_disponivel = False
        logger.warning(
            "⚠️ spaCy não disponível. "
            "Instale com: pip install spacy && python -m spacy download pt_core_news_sm"
        )
        return False


def _get_nlp():
    """
    Retorna instância do spaCy (lazy loading).
    Carrega modelo só quando necessário.
    """
    global _nlp
    
    if _nlp is None:
        if not _verificar_spacy_disponivel():
            raise RuntimeError(
                "spaCy não está disponível. "
                "Instale com: pip install spacy && python -m spacy download pt_core_news_sm"
            )
        
        import spacy
        _nlp = spacy.load("pt_core_news_sm")
        logger.info("🚀 spaCy carregado e pronto para uso")
    
    return _nlp


def _lematizar_com_spacy(palavra: str) -> str:
    """
    Lematiza palavra usando spaCy (fallback inteligente).
    
    Args:
        palavra: Palavra a ser lematizada
    
    Returns:
        Forma lematizada da palavra
    """
    try:
        nlp = _get_nlp()
        doc = nlp(palavra)
        
        if len(doc) > 0:
            lemma = doc[0].lemma_
            
            # Se for verbo, aprende automaticamente
            if doc[0].pos_ == "VERB":
                adicionar_ao_dicionario_aprendido(palavra, lemma)
            
            return lemma
        
        return palavra
    
    except Exception as e:
        logger.error(f"❌ Erro ao usar spaCy para '{palavra}': {e}")
        return palavra


# ============================================================================
# FUNÇÕES DE LEMATIZAÇÃO (HÍBRIDAS)
# ============================================================================

@lru_cache(maxsize=2000)
def lematizar_palavra(palavra: str) -> str:
    """
    Converte uma palavra para sua forma lematizada (infinitivo se for verbo).
    
    Sistema Híbrido Inteligente:
    1. Tenta dicionário estático (400 conjugações - 0.05ms)
    2. Tenta dicionário aprendido (verbos descobertos - 0.05ms)
    3. Fallback para spaCy (verbos novos - 1-2ms + aprende)
    
    Args:
        palavra: Palavra a ser lematizada (já normalizada: lowercase, sem acentos)
    
    Returns:
        Forma lematizada da palavra (infinitivo se verbo, ou a própria palavra)
    
    Examples:
        >>> lematizar_palavra("exclua")
        "excluir"
        >>> lematizar_palavra("enviando")
        "enviar"
        >>> lematizar_palavra("correndo")  # Novo verbo
        "correr"  # ← Usa spaCy e aprende automaticamente
        >>> lematizar_palavra("correndo")  # 2ª vez
        "correr"  # ← Agora usa dicionário aprendido (rápido!)
    """
    # PRIORIDADE 1: Dicionário estático (verbos mais comuns)
    if palavra in MAPEAMENTO_VERBOS:
        return MAPEAMENTO_VERBOS[palavra]
    
    # PRIORIDADE 2: Dicionário aprendido (verbos descobertos antes)
    if palavra in DICIONARIO_APRENDIDO:
        return DICIONARIO_APRENDIDO[palavra]
    
    # PRIORIDADE 3: spaCy fallback (verbos novos - aprende automaticamente)
    if _verificar_spacy_disponivel():
        return _lematizar_com_spacy(palavra)
    
    # FALLBACK FINAL: Retorna palavra original (spaCy não disponível)
    return palavra


def lematizar_texto(texto: str) -> str:
    """
    Lematiza todas as palavras de um texto.
    
    Args:
        texto: Texto normalizado (lowercase, sem acentos)
    
    Returns:
        Texto com verbos convertidos para infinitivo
    
    Examples:
        >>> lematizar_texto("exclua o documento")
        "excluir o documento"
        >>> lematizar_texto("enviando email para joao")
        "enviar email para joao"
    """
    palavras = texto.split()
    palavras_lematizadas = [lematizar_palavra(p) for p in palavras]
    return " ".join(palavras_lematizadas)


def extrair_verbos_de_acao(texto: str) -> Set[str]:
    """
    Extrai verbos de ação (infinitivo) presentes no texto.
    
    Args:
        texto: Texto normalizado (lowercase, sem acentos)
    
    Returns:
        Conjunto de verbos de ação encontrados (na forma infinitiva)
    
    Examples:
        >>> extrair_verbos_de_acao("exclua o documento e envie email")
        {"excluir", "enviar"}
        >>> extrair_verbos_de_acao("qual a capital da franca?")
        set()
    """
    palavras = texto.split()
    verbos_encontrados = set()
    
    for palavra in palavras:
        verbo_infinitivo = lematizar_palavra(palavra)
        if verbo_infinitivo in VERBOS_INFINITIVOS:
            verbos_encontrados.add(verbo_infinitivo)
    
    return verbos_encontrados


def tem_verbo_de_acao(texto: str) -> bool:
    """
    Verifica se o texto contém algum verbo de ação (em qualquer conjugação).
    
    Args:
        texto: Texto normalizado (lowercase, sem acentos)
    
    Returns:
        True se contém verbo de ação, False caso contrário
    
    Examples:
        >>> tem_verbo_de_acao("exclua o documento")
        True
        >>> tem_verbo_de_acao("me explica como funciona")
        False
    """
    return len(extrair_verbos_de_acao(texto)) > 0


# ============================================================================
# ESTATÍSTICAS
# ============================================================================

def obter_estatisticas() -> dict:
    """
    Retorna estatísticas sobre o sistema de lematização.
    
    Returns:
        Dict com estatísticas completas do sistema híbrido
    """
    total_conjugacoes_estaticas = len(MAPEAMENTO_VERBOS)
    verbos_unicos_estaticos = len(VERBOS_INFINITIVOS)
    cobertura_media = total_conjugacoes_estaticas / verbos_unicos_estaticos if verbos_unicos_estaticos > 0 else 0
    
    # Estatísticas do cache LRU
    cache_info = lematizar_palavra.cache_info()
    total_chamadas = cache_info.hits + cache_info.misses
    taxa_acerto_cache = (cache_info.hits / total_chamadas * 100) if total_chamadas > 0 else 0
    
    return {
        # Dicionário estático
        "dicionario_estatico": {
            "total_conjugacoes": total_conjugacoes_estaticas,
            "verbos_unicos_infinitivo": verbos_unicos_estaticos,
            "cobertura_media_por_verbo": round(cobertura_media, 2),
        },
        
        # Dicionário aprendido
        "dicionario_aprendido": {
            "total_palavras_aprendidas": len(DICIONARIO_APRENDIDO),
            "palavras_desde_ultimo_save": _palavras_desde_ultimo_save,
        },
        
        # Cache LRU
        "cache": {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "tamanho_atual": cache_info.currsize,
            "tamanho_maximo": cache_info.maxsize,
            "taxa_acerto_pct": round(taxa_acerto_cache, 2),
        },
        
        # spaCy
        "spacy": {
            "disponivel": _verificar_spacy_disponivel(),
            "carregado": _nlp is not None,
        },
        
        # Total geral
        "total_palavras_conhecidas": total_conjugacoes_estaticas + len(DICIONARIO_APRENDIDO),
    }


# ============================================================================
# UTILITÁRIOS PARA EXPANSÃO
# ============================================================================

def adicionar_verbo(infinitivo: str, conjugacoes: list[str]) -> None:
    """
    Adiciona um novo verbo e suas conjugações ao mapeamento ESTÁTICO.
    Útil para expandir manualmente o dicionário base.
    
    Args:
        infinitivo: Forma infinitiva do verbo (ex: "conectar")
        conjugacoes: Lista de conjugações (ex: ["conecte", "conecta", "conectando"])
    
    Examples:
        >>> adicionar_verbo("conectar", ["conecte", "conecta", "conectando"])
    """
    # Adiciona o próprio infinitivo
    MAPEAMENTO_VERBOS[infinitivo] = infinitivo
    VERBOS_INFINITIVOS.add(infinitivo)
    
    # Adiciona as conjugações
    for conjugacao in conjugacoes:
        MAPEAMENTO_VERBOS[conjugacao] = infinitivo
    
    # Limpa o cache para refletir as mudanças
    lematizar_palavra.cache_clear()
    
    logger.info(f"➕ Verbo '{infinitivo}' adicionado manualmente com {len(conjugacoes)} conjugações")


def limpar_cache() -> None:
    """Limpa o cache LRU de lematização."""
    lematizar_palavra.cache_clear()
    logger.info("🧹 Cache de lematização limpo")


def eh_pergunta_interrogativa(texto: str) -> bool:
    """
    Detecta se o texto é uma pergunta usando spaCy + análise linguística.
    
    Detecta perguntas mesmo sem "?":
    - "me diga como funciona" (verbo interrogativo)
    - "quero saber sobre git" (intenção de pergunta)
    - "voce pode explicar" (pedido de informação)
    
    IMPORTANTE: Não considera perguntas de natureza pessoal/desenvolvimento
    como "gostaria de aprender programação" (isso é USER, não MESSAGES)
    
    Args:
        texto: Texto a ser analisado
        
    Returns:
        True se o texto é uma pergunta factual/técnica
    """
    texto_lower = texto.lower()
    
    # 0. EXCLUSÃO: Frases de natureza pessoal/desenvolvimento NÃO são perguntas técnicas
    # "gostaria de aprender", "quero melhorar", "preciso desenvolver"
    contextos_pessoais = [
        "gostaria de aprender", "gostaria de melhorar", "gostaria de desenvolver",
        "quero aprender", "quero melhorar", "quero desenvolver",
        "preciso aprender", "preciso melhorar", "preciso desenvolver",
        "desejo aprender", "desejo melhorar",
        "estou tentando aprender", "estou buscando aprender"
    ]
    if any(ctx in texto_lower for ctx in contextos_pessoais):
        return False
    
    # Perguntas explicativas detalhadas → USER (não MESSAGES)
    # "me explique detalhadamente", "explique passo a passo", "processo de aprendizado"
    indicadores_explicacao_complexa = [
        "detalhadamente", "passo a passo", "em detalhes",
        "processo de aprendizado", "processo de desenvolvimento",
        "me ajude a entender o processo", "me explique o processo"
    ]
    if any(ind in texto_lower for ind in indicadores_explicacao_complexa):
        return False
    
    # 1. Tem interrogação explícita?
    if "?" in texto:
        return True
    
    # 2. Começa com palavra interrogativa?
    palavras_interrogativas_inicio = [
        "como", "quando", "onde", "por que", "porque", "qual", "quais",
        "quem", "quanto", "quantos", "quantas", "que", "o que"
    ]
    primeira_palavra = texto_lower.split()[0] if texto_lower.split() else ""
    if primeira_palavra in palavras_interrogativas_inicio:
        return True
    
    # 3. Contém estrutura interrogativa?
    estruturas_interrogativas = [
        "me diga", "me explique", "me fale", "me conte",
        "quero saber", "quero entender",  # Removido "quero aprender" (muito pessoal)
        "gostaria de saber", "preciso saber", "preciso entender",
        "voce pode explicar", "voce consegue explicar",
        "pode me dizer", "consegue me dizer"
    ]
    if any(estrutura in texto_lower for estrutura in estruturas_interrogativas):
        return True
    
    # 4. Usa spaCy para análise mais profunda (se disponível)
    if _nlp is not None:
        try:
            doc = _nlp(texto[:200])  # Limita para performance
            
            # Verifica se tem pronome interrogativo
            for token in doc:
                # Pronomes interrogativos: que, qual, quem, quanto, como, quando, onde
                if token.pos_ == "PRON" and token.text.lower() in ["que", "qual", "quem", "quanto"]:
                    return True
                
                # Advérbios interrogativos: como, quando, onde, por que
                if token.pos_ == "ADV" and token.text.lower() in ["como", "quando", "onde", "porque"]:
                    return True
            
            # Verifica padrão de pergunta indireta (mas factual)
            # Ex: "gostaria de saber como funciona" (factual)
            # NÃO: "gostaria de aprender programação" (pessoal)
            verbos_pedido_info_factual = ["saber", "entender", "conhecer", "descobrir"]
            for token in doc:
                if token.lemma_ in verbos_pedido_info_factual:
                    return True
                    
        except Exception:
            pass  # Se spaCy falhar, usa apenas as regras anteriores
    
    return False


def resetar_dicionario_aprendido() -> None:
    """
    Reseta o dicionário aprendido (útil para testes ou manutenção).
    ATENÇÃO: Apaga todo o aprendizado acumulado!
    """
    global DICIONARIO_APRENDIDO, _palavras_desde_ultimo_save
    
    DICIONARIO_APRENDIDO.clear()
    _palavras_desde_ultimo_save = 0
    
    if LEARNED_DICT_PATH.exists():
        LEARNED_DICT_PATH.unlink()
    
    logger.warning("⚠️ Dicionário aprendido foi resetado!")


# ============================================================================
# INICIALIZAÇÃO DO MÓDULO
# ============================================================================

# Carrega dicionário aprendido automaticamente ao importar o módulo
try:
    carregar_dicionario_aprendido()
except Exception as e:
    logger.error(f"❌ Erro na inicialização do lematizador: {e}")
