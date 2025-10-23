"""
Módulo responsável pela classificação de mensagens em categorias.
"""

from typing import List, Tuple
from app.utils.regex import (
    REGEX_PERGUNTA_FACTUAL,
    REGEX_REFERENCIAS_PESSOAIS,
    REGEX_PLANO_ESTRATEGIA,
    REGEX_MULTIPLAS_FRASES,
)
from app.utils.lematizador import (
    lematizar_texto,
    extrair_verbos_de_acao,
    tem_verbo_de_acao,
    eh_pergunta_interrogativa,
    VERBOS_INFINITIVOS,
    OBJETOS_INTEGRACAO,
    CONTEXTOS_EMAIL,
    CONTEXTOS_COMPARTILHAR,
    CONTEXTOS_AGENDAMENTO,
    CONTEXTOS_CANCELAMENTO,
    EXCLUSOES_INTEGRACAO,
)
from .constantes import PALAVRAS_CHAVE_DE_SISTEMA


class Classificador:
    """Classifica mensagens em categorias (system, messages, user)."""

    @staticmethod
    def determinar_categoria(
        mensagem_original: str, texto_normalizado: str
    ) -> Tuple[str, List[str]]:
        """
        Determina a categoria da mensagem (system, messages, user).
        Otimizado com buscas 'in' ao invés de regex onde possível.

        Args:
            mensagem_original: Mensagem original do usuário
            texto_normalizado: Texto normalizado para análise

        Returns:
            Tupla com (categoria, lista de motivos)
        """

        # Prioridade 1: É um pedido que envolve sistemas/integrações?
        # REGRA: Deve ter intenção clara de ação + objeto/contexto de integração
        palavras_encontradas = [
            p for p in PALAVRAS_CHAVE_DE_SISTEMA if p in texto_normalizado
        ]
        if palavras_encontradas and Classificador._tem_intencao_clara_de_integracao(
            texto_normalizado
        ):
            motivo = f"Palavras-chave de sistemas/APIs: {', '.join(palavras_encontradas[:6])}"
            return "system", [motivo]

        # Prioridade 1.5A: NARRATIVAS DE TERCEIRA PESSOA → USER
        # "ele deletou o arquivo", "maria enviou email", "a equipe criou planilha"
        pronomes_terceira_pessoa = ["ele ", "ela ", "eles ", "elas ", "alguem ", "voce viu que "]
        nomes_proprios_comuns = ["maria ", "joao ", "jose ", "ana ", "pedro ", "paulo ", "lucas ", "carlos "]
        grupos_terceira_pessoa = ["a equipe ", "o time ", "os hackers ", "a empresa ", "o grupo "]
        
        # Verbos no passado que indicam narrativa
        verbos_passado = [
            " deletou ", " enviou ", " criou ", " compartilhou ",
            " agendou ", " cancelou ", " removeu ", " excluiu ",
            " baixou ", " baixaram ", " enviaram ", " criaram ",
            " compartilharam ", " agendaram ",
        ]
        
        tem_terceira_pessoa = any(p in texto_normalizado for p in pronomes_terceira_pessoa + nomes_proprios_comuns + grupos_terceira_pessoa)
        tem_verbo_passado = any(v in texto_normalizado for v in verbos_passado)
        
        # Se é narrativa sobre terceiro → USER (não SYSTEM nem MESSAGES)
        if tem_terceira_pessoa and tem_verbo_passado:
            return "user", ["Narrativa sobre terceira pessoa (não é comando)"]
        
        # Prioridade 1.5B: PERGUNTAS DE CAPACIDADE → MESSAGES
        # "você pode enviar email?", "você consegue agendar?"
        perguntas_capacidade = [
            "voce pode", "voce consegue", "e possivel", "da pra",
            "como faco", "como fazer", "onde esta", "onde fica"
        ]
        if any(p in texto_normalizado for p in perguntas_capacidade):
            return "messages", ["Pergunta sobre capacidade (não é comando)"]
        
        # Prioridade 1.5C: TAREFAS ABSTRATAS/PESSOAIS → USER
        # "melhorar meu email", "organizar mentalmente", "criar estratégia"
        palavras_tarefas_pessoais = [
            "melhorar meu", "melhorar minha", "organizar meu", "organizar minha",
            "mentalmente", "estrategia", "plano de", "praticas para", "melhores praticas"
        ]
        if any(p in texto_normalizado for p in palavras_tarefas_pessoais):
            return "user", ["Tarefa pessoal/abstrata (não comando de API)"]
        
        # Prioridade 1.5D: PEDIDOS DE AJUDA GENÉRICOS → MESSAGES
        # "me ajude", "tutorial de", "dicas de"
        pedidos_ajuda_genericos = [
            "me ajude", "me ajuda", "preciso de ajuda",
            "tutorial de", "tutorial sobre", "como usar",
            "dicas de", "dicas sobre", "dica de"
        ]
        if any(p in texto_normalizado for p in pedidos_ajuda_genericos):
            return "messages", ["Pedido de ajuda genérico (não comando específico)"]
        
        # Prioridade 1.5E: SAUDAÇÕES INTERROGATIVAS → USER
        # "tudo bem?", "como vai?", "e ai?"
        saudacoes_interrogativas = [
            "tudo bem", "como vai", "como voce esta", "e ai", "beleza"
        ]
        if any(s in texto_normalizado for s in saudacoes_interrogativas) and "?" in mensagem_original:
            return "user", ["Saudação conversacional"]
        
        # Prioridade 1.5F: FRASES CONDICIONAIS VAGAS → MESSAGES
        # "enviaria se pudesse", "faria se tivesse", "gostaria mas não posso"
        marcadores_condicionais = [
            "se pudesse", "se tivesse", "se fosse", "se conseguisse",
            "mas nao posso", "porem nao", "todavia nao"
        ]
        if any(c in texto_normalizado for c in marcadores_condicionais):
            return "messages", ["Frase condicional/hipotética (não comando direto)"]
        
        # Prioridade 1.5G: COMANDOS COM OBJETOS GENÉRICOS (antes da verificação de tamanho)
        # Mesmo curtos, comandos como "envia o relatório" devem ser SYSTEM
        objetos_genericos_comandos = [
            "relatorio", "arquivo", "documento", "dados", "backup",
            "nota", "texto", "mensagem", "foto", "imagem", "video", "email",
            "valor", "dinheiro", "pagamento", "boleto"  # Adicionado: objetos financeiros
        ]
        
        # Palavras que indicam tarefa abstrata (não comando de API)
        palavras_abstratas = ["mentalmente", "estrategia", "plano de", "melhorar meu", "organizar meu"]
        tem_contexto_abstrato = any(p in texto_normalizado for p in palavras_abstratas)
        
        tem_objeto_generico_comando = any(obj in texto_normalizado for obj in objetos_genericos_comandos)
        tem_verbo_integracao = any(verbo in lematizar_texto(texto_normalizado) for verbo in VERBOS_INFINITIVOS)
        
        # Mas não considerar perguntas como comandos, nem tarefas abstratas
        eh_pergunta = "?" in mensagem_original
        if tem_objeto_generico_comando and tem_verbo_integracao and not eh_pergunta and not tem_contexto_abstrato:
            return "system", ["Comando com verbo de integração e objeto genérico"]

        # Prioridade 2: É uma pergunta direta e objetiva?
        if Classificador._e_pergunta_direta_e_objetiva(
            mensagem_original, texto_normalizado
        ):
            return "messages", ["Pergunta direta/fechada detectada."]
        
        # Prioridade 2A: PERGUNTAS DETECTADAS POR spaCy → MESSAGES
        # Usa análise linguística avançada para detectar perguntas (mesmo sem "?")
        # Exemplos: "me explica como funciona", "quero saber sobre git", "pode me dizer"
        if eh_pergunta_interrogativa(mensagem_original):
            # Verifica se é pergunta técnica/conceitual
            palavras_tecnicas_pergunta = [
                "como funciona", "o que e", "como usar", "quero entender",
                "quero aprender", "como fazer", "qual a diferenca", "me explique",
                "entender conceito", "entender os conceito",
                # Termos técnicos comuns
                "git", "python", "javascript", "api", "sistema", "versionamento",
                "programacao", "codigo", "algoritmo", "tecnologia", "framework",
                "branch", "merge", "pull request", "commit", "database"
            ]
            if any(p in texto_normalizado for p in palavras_tecnicas_pergunta):
                return "messages", ["Pergunta técnica/conceitual (spaCy)"]
            else:
                return "messages", ["Pergunta detectada por análise linguística"]

        # Prioridade 3: É uma mensagem complexa ou pessoal?
        if Classificador._e_mensagem_complexa_ou_pessoal(
            mensagem_original, texto_normalizado
        ):
            return "user", ["Mensagem com necessidade de personalização/contexto."]

        # Prioridade 4 (Fallback): Se não se encaixou em nenhuma regra específica
        # Analisa características sutis para decidir
        
        # Se tem múltiplas frases ou é muito longa → provavelmente USER
        num_frases = len([s for s in mensagem_original.split('.') if s.strip()]) + \
                     len([s for s in mensagem_original.split('?') if s.strip()]) + \
                     len([s for s in mensagem_original.split('!') if s.strip()])
        
        if num_frases > 2 or len(mensagem_original) > 150:
            return "user", ["Mensagem longa ou com múltiplas ideias - requer contexto"]
        
        # Se tem pronomes pessoais (meu, minha, eu, me) → provavelmente USER
        pronomes_pessoais = [" meu ", " minha ", " meus ", " minhas ", " eu ", " me ", " comigo "]
        if any(p in f" {texto_normalizado} " for p in pronomes_pessoais):
            return "user", ["Contém contexto pessoal"]
        
        # Default final: MESSAGES (resposta simples e direta)
        # Mas mensagens muito curtas sem contexto específico → USER (saudações, etc)
        if len(mensagem_original.strip()) < 20:
            return "user", ["Mensagem curta conversacional"]
        
        return "messages", ["Mensagem genérica sem indicadores específicos"]

    @staticmethod
    def _tem_intencao_clara_de_integracao(texto_normalizado: str) -> bool:
        """
        Verifica se há intenção clara de usar integração/ferramenta.
        REGRA CHAVE: verbo de ação + objeto específico de integração + NÃO ser narrativa
        
        MELHORIA: Agora usa lematização para detectar qualquer conjugação verbal
        (ex: "exclua", "excluindo", "excluído" → todos detectados como "excluir")
        
        IMPORTANTE: Todos os verbos são gerenciados centralmente no lematizador.
        Qualquer verbo novo adicionado lá será automaticamente reconhecido aqui.

        Args:
            texto_normalizado: Texto normalizado

        Returns:
            True se houver intenção clara de integração
        """
        # ===================================================================
        # FILTROS DE EXCLUSÃO RÁPIDOS (verificar ANTES de tudo)
        # ===================================================================
        
        # EXCLUSÃO 1: Perguntas sobre capacidade (não são comandos)
        perguntas_capacidade = [
            "voce pode",
            "voce consegue",
            "e possivel",
            "da pra",
            "como faco",
            "como fazer",
            "onde esta",
            "onde fica",
        ]
        if any(p in texto_normalizado for p in perguntas_capacidade):
            return False
        
        # EXCLUSÃO 2: Narrativas sobre terceiros (passado + pronome de terceira pessoa)
        # "ele deletou", "maria enviou", "a equipe criou", "joão compartilhou"
        pronomes_terceira_pessoa = ["ele ", "ela ", "eles ", "elas ", "alguem ", "voce viu que "]
        nomes_proprios_comuns = ["maria ", "joao ", "jose ", "ana ", "pedro ", "paulo ", "lucas ", "carlos ", "fernando "]
        grupos_terceira_pessoa = ["a equipe ", "o time ", "os hackers ", "a empresa ", "o grupo ", "eles ", "alguem "]
        
        # Verbos no passado que indicam narrativa (não comando)
        verbos_passado_narrativa = [
            " deletou ", " enviou ", " criou ", " compartilhou ",
            " agendou ", " cancelou ", " removeu ", " excluiu ",
            " baixou ", " baixaram ", " enviaram ", " criaram ",
            " compartilharam ", " agendaram ", " cancelaram ",
        ]
        
        # Se tem pronome/nome de terceira + verbo no passado = narrativa, não comando
        eh_narrativa_terceira_pessoa = (
            any(p in texto_normalizado for p in pronomes_terceira_pessoa + nomes_proprios_comuns + grupos_terceira_pessoa)
            and any(v in texto_normalizado for v in verbos_passado_narrativa)
        )
        
        if eh_narrativa_terceira_pessoa:
            return False
        
        # EXCLUSÃO 3: Frases genéricas importadas do lematizador
        if any(exc in texto_normalizado for exc in EXCLUSOES_INTEGRACAO):
            return False
        
        # ===================================================================
        # DETECÇÃO DE INTEGRAÇÃO (após passar pelos filtros)
        # ===================================================================
        
        # Lematiza o texto para normalizar verbos (imperativo → infinitivo)
        texto_lematizado = lematizar_texto(texto_normalizado)
        
        # Extrai verbos de ação presentes no texto (já em infinitivo)
        verbos_encontrados = extrair_verbos_de_acao(texto_normalizado)
        
        # FONTE ÚNICA: usa todos os verbos do lematizador (46 verbos, 409+ conjugações)
        verbos_integracao = VERBOS_INFINITIVOS
        
        # Verifica se tem verbo de integração
        tem_verbo = bool(verbos_encontrados & verbos_integracao)

        # FONTE ÚNICA: Objetos específicos importados do lematizador
        tem_objeto_especifico = any(
            obj in texto_normalizado for obj in OBJETOS_INTEGRACAO
        )
        
        # Objetos genéricos que se tornam específicos com verbo
        objetos_genericos_com_verbo = [
            "relatorio", "arquivo", "documento", "dados", "backup",
            "nota", "texto", "mensagem", "foto", "imagem", "video",
        ]
        tem_objeto_generico = any(obj in texto_normalizado for obj in objetos_genericos_com_verbo)

        # EMAIL com "@" ou destinatário SEMPRE é integração
        tem_email_com_destinatario = (
            "@" in texto_normalizado or ".com" in texto_normalizado
        )

        tem_email_com_contexto = (
            ("email" in texto_normalizado or "e-mail" in texto_normalizado)
            and (tem_verbo or "para" in texto_normalizado or "@" in texto_normalizado)
            and any(p in texto_normalizado for p in CONTEXTOS_EMAIL)
        )

        tem_documento_com_acao = (
            (
                "documento" in texto_normalizado
                or "doc " in texto_normalizado
                or " doc " in texto_normalizado
                or texto_normalizado.endswith("doc")
                or texto_normalizado.startswith("doc ")
            )
            and tem_verbo
        )

        tem_arquivo_com_acao = "arquivo" in texto_normalizado and (
            tem_verbo
            or "baixar" in texto_lematizado
            or "compartilhado" in texto_normalizado
        )

        tem_calendario_com_contexto = (
            ("agenda" in texto_normalizado or "calendar" in texto_normalizado)
            and tem_verbo
            and "tempo" not in texto_normalizado
        )

        tem_compartilhamento = "compartilhar" in texto_lematizado and any(
            ctx in texto_normalizado for ctx in CONTEXTOS_COMPARTILHAR
        )

        tem_agendamento_horario = (
            "marcar" in texto_lematizado
            or "agendar" in texto_lematizado
            or "reservar" in texto_lematizado
        ) and any(ctx in texto_normalizado for ctx in CONTEXTOS_AGENDAMENTO)
        
        tem_cancelamento_ou_reagendamento = (
            "cancelar" in texto_lematizado or "reagendar" in texto_lematizado
        ) and any(ctx in texto_normalizado for ctx in CONTEXTOS_CANCELAMENTO)
        
        # Verbo de integração + objeto genérico = integração
        # Ex: "envie o relatório", "baixe os dados"
        tem_verbo_com_objeto_generico = tem_verbo and tem_objeto_generico

        tem_integracao = (
            tem_objeto_especifico
            or tem_email_com_contexto
            or tem_email_com_destinatario
            or tem_documento_com_acao
            or tem_arquivo_com_acao
            or tem_calendario_com_contexto
            or tem_compartilhamento
            or tem_agendamento_horario
            or tem_cancelamento_ou_reagendamento
            or tem_verbo_com_objeto_generico  # NOVO: aceita objetos genéricos com verbo
        )

        return tem_integracao

    @staticmethod
    def _e_pergunta_direta_e_objetiva(texto: str, texto_normalizado: str) -> bool:
        """
        Verifica se é uma pergunta direta usando regex pré-compilada.

        Args:
            texto: Texto original
            texto_normalizado: Texto normalizado

        Returns:
            True se for pergunta direta e objetiva
        """
        e_curta_e_termina_com_interrogacao = len(texto) <= 80 and texto.endswith("?")
        contem_termos_factuais = bool(REGEX_PERGUNTA_FACTUAL.search(texto_normalizado))
        return e_curta_e_termina_com_interrogacao or contem_termos_factuais

    @staticmethod
    def _e_mensagem_complexa_ou_pessoal(texto: str, texto_normalizado: str) -> bool:
        """
        Verifica complexidade da mensagem usando regex pré-compiladas.
        
        NOTA: Não usa mais verificação de tamanho - apenas features linguísticas.

        Args:
            texto: Texto original
            texto_normalizado: Texto normalizado sem acentos

        Returns:
            True se for mensagem complexa ou pessoal
        """

        usa_referencias_pessoais = bool(REGEX_REFERENCIAS_PESSOAIS.search(texto))
        pede_um_plano_ou_estrategia = bool(REGEX_PLANO_ESTRATEGIA.search(texto))
        tem_multiplas_frases = len(REGEX_MULTIPLAS_FRASES.findall(texto)) > 1

        # Mensagens curtas com "plano", "ideias", "estratégia" são tarefas simples, não USER
        palavras_tarefas_simples = [
            "plano de",
            "minhas ideias",
            "uma estrategia",
            "meus documentos",
            "preparar uma",
            "melhorar meu email",
            "criar um roteiro",
            "organizar pensamentos",
            "organizar prioridades",
            "criar um metodo",
            "otimizar meu",
        ]
        e_tarefa_simples = (
            any(t in texto_normalizado for t in palavras_tarefas_simples)
            and len(texto) < 80
        )

        if e_tarefa_simples:
            return False

        # Palavras que indicam necessidade de personalização (em contextos complexos)
        palavras_personalizacao = [
            "estou me sentindo",
            "queria entender melhor",
            "preciso de conselhos",
            "preciso de ajuda para",
            "gostaria de aprender",
            "com dificuldade",
            "sobrecarregado",
            "crescer profissionalmente",
            "estou buscando maneiras",
            "quero desenvolver",
            "procuro formas",
            "preciso repensar",
            "gostaria de feedback",
            # Contextos de melhoria pessoal
            "gostaria de melhorar",
        ]
        tem_personalizacao = any(
            p in texto_normalizado for p in palavras_personalizacao
        )

        # Verifica se tem "gostaria de melhorar" em contexto pessoal/profissional (não sistema)
        tem_melhoria_pessoal = "melhorar minha comunicacao" in texto_normalizado or (
            "melhorar" in texto_normalizado
            and any(
                ctx in texto_normalizado
                for ctx in ["relacionamento", "desempenho", "no trabalho"]
            )
        )

        return (
            usa_referencias_pessoais
            or pede_um_plano_ou_estrategia
            or tem_multiplas_frases
            or tem_personalizacao
            or tem_melhoria_pessoal
        )
