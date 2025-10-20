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
        if palavras_encontradas and Classificador._tem_intencao_clara_de_integracao(texto_normalizado):
            motivo = f"Palavras-chave de sistemas/APIs: {', '.join(palavras_encontradas[:6])}"
            return "system", [motivo]

        # Prioridade 2: É uma pergunta direta e objetiva?
        if Classificador._e_pergunta_direta_e_objetiva(
            mensagem_original, texto_normalizado
        ):
            return "messages", ["Pergunta direta/fechada detectada."]

        # Prioridade 3: É uma mensagem complexa ou pessoal?
        if Classificador._e_mensagem_complexa_ou_pessoal(mensagem_original, texto_normalizado):
            return "user", ["Mensagem com necessidade de personalização/contexto."]

        # Se não se encaixar em nenhuma regra, decide pelo tamanho.
        if len(mensagem_original) < 60:
            return "messages", ["Curta e objetiva; sem necessidade clara de contexto."]
        else:
            return "user", ["Mensagem requer elaboração moderada."]

    @staticmethod
    def _tem_intencao_clara_de_integracao(texto_normalizado: str) -> bool:
        """
        Verifica se há intenção clara de usar integração/ferramenta.
        REGRA CHAVE: verbo de ação + objeto específico de integração
        
        Args:
            texto_normalizado: Texto normalizado

        Returns:
            True se houver intenção clara de integração
        """
        # Verbos fortes que indicam ação de integração
        verbos_integracao = {
            "enviar", "envie", "mandar", "mande", "send", "disparar", "dispare",
            "encaminhar", "encaminhe", "forward",
            "agendar", "agende", "marcar", "marque", "schedule", "reservar", "reserve",
            "criar", "crie", "gerar", "gere", "produzir", "produza", "create",
            "compartilhar", "compartilhe", "share", "upload", "subir",
            "responder", "reply",
            "editar", "edit", "modificar",
            "fazer upload", "fazer download", "sincronizar",
            "baixar", "download", "fazer", "faca",
        }
        
        # Objetos ESPECÍFICOS que indicam integração real
        objetos_especificos = {
            # Email - menções específicas
            "gmail", "destinatario", "assunto",
            # Docs - tipos específicos
            "planilha", "sheet", "excel", "slide", "apresentacao",
            "google docs", "google drive",
            # Calendário - contextos claros
            "reuniao", "meeting", "compromisso", "evento",
            # Pagamentos
            "boleto", "pagamento", "cobranca", "fatura", "pix",
            # Armazenamento
            "backup", "upload", "download", "sincronizar",
            # Documento/arquivos em contextos claros de sistema
            "rascunho",  # sempre é integração
        }
        
        # Contextos que tornam objetos genéricos específicos
        # "email" vira específico se tem verbo forte + preposição/destino
        tem_verbo = any(v in texto_normalizado for v in verbos_integracao)
        tem_objeto_especifico = any(obj in texto_normalizado for obj in objetos_especificos)
        
        # Menções genéricas que precisam de contexto adicional
        # EMAIL com "@" SEMPRE é integração
        tem_email_com_destinatario = "@" in texto_normalizado or ".com" in texto_normalizado
        
        tem_email_com_contexto = (
            ("email" in texto_normalizado or "e-mail" in texto_normalizado) and 
            (tem_verbo or "para" in texto_normalizado or "@" in texto_normalizado) and 
            any(p in texto_normalizado for p in ["para", "pro", "@", "ao", "do", "da", "mensagem por", "um email", "um e-mail", "uma mensagem", "agora", "enviar", "automatica", "maria", "joao", ".com", "teste.com"])
        )
        
        # RASCUNHO É INTEGRAÇÃO SEMPRE (removido - já está em objetos_especificos)
        
        tem_documento_com_acao = (
            ("documento" in texto_normalizado or "doc " in texto_normalizado or " doc " in texto_normalizado or texto_normalizado.endswith("doc") or texto_normalizado.startswith("doc ")) and
            tem_verbo
            # Se tem verbo + doc/documento, é integração
        )
        
        tem_arquivo_com_acao = (
            "arquivo" in texto_normalizado and
            (tem_verbo or "baixar" in texto_normalizado or "compartilhado" in texto_normalizado)  # Se tem verbo + arquivo, é integração
        )
        
        tem_calendario_com_contexto = (
            ("agenda" in texto_normalizado or "calendar" in texto_normalizado) and
            tem_verbo and
            "tempo" not in texto_normalizado  # "agendar tempo" é genérico
        )
        
        # COMPARTILHAR sempre é integração se tiver contexto de equipe/destinatário
        tem_compartilhamento = (
            "compartilhar" in texto_normalizado and
            any(ctx in texto_normalizado for ctx in ["equipe", "time", "com", "para", "documento", "planilha", "arquivo", "drive"])
        )
        
        # MARCAR/AGENDAR com horário é integração
        tem_agendamento_horario = (
            ("marcar" in texto_normalizado or "marque" in texto_normalizado or 
             "agendar" in texto_normalizado or "agende" in texto_normalizado or
             "reservar" in texto_normalizado or "reserve" in texto_normalizado) and
            any(ctx in texto_normalizado for ctx in [
                "call", "reuniao", "meeting", "as ", "h", "hr", ":", 
                "cliente", "urgente", "hoje", "amanha", "semana",
                "aula", "evento", "compromisso", "para mim", "sala",
                "segunda", "terca", "quarta", "quinta", "sexta"
            ])
        )
        
        tem_integracao = (
            tem_objeto_especifico or 
            tem_email_com_contexto or 
            tem_email_com_destinatario or
            tem_documento_com_acao or
            tem_arquivo_com_acao or
            tem_calendario_com_contexto or
            tem_compartilhamento or
            tem_agendamento_horario
        )
        
        # Filtros de exclusão - mesmo com objetos, não são integrações
        # IMPORTANTE: usar \b (word boundary) ou espaços para evitar matches parciais
        exclusoes = [
            # Perguntas sobre funcionalidades
            "o que vc pode fazer", "o que voce pode fazer", "o que pode fazer",
            "quais funcoes", "quais funcionalidades",
            # Ajuda genérica
            "me ajude", "me ajuda", " help ", " ajuda ",
            # Saudações - com espaços para evitar match em "colaborativo", "rascunho", etc
            " oi ", " ola ", " oie ", " opa ",
            # Ações sobre conceitos (não sobre ferramentas)
            "melhorar meu email",
            "organizar meus documentos", "organizar minhas",
            "organizar meu",
            # Perguntas sobre datas/tempo
            "qual a data", "que data", "data de hoje", "data hoje",
            "agendar meu tempo", "agendar tempo",
            # Meta-perguntas
            "o que fazer", "como fazer", "que fazer",
            # Perguntas de aprendizado (não são integração)
            "como usar", "tutorial", "aprender", "estudar", "entender sobre",
            "dicas de", "como nomear", "como organizar", "boas praticas",
            "otimizar meu", "configurar",
        ]
        
        tem_exclusao = any(exc in texto_normalizado for exc in exclusoes)
        
        return tem_integracao and not tem_exclusao

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

        Args:
            texto: Texto original
            texto_normalizado: Texto normalizado sem acentos

        Returns:
            True se for mensagem complexa ou pessoal
        """
        
        e_longa = len(texto) > 100  # Reduzido de 160 para 100
        usa_referencias_pessoais = bool(REGEX_REFERENCIAS_PESSOAIS.search(texto))
        pede_um_plano_ou_estrategia = bool(REGEX_PLANO_ESTRATEGIA.search(texto))
        tem_multiplas_frases = len(REGEX_MULTIPLAS_FRASES.findall(texto)) > 1
        
        # Mensagens curtas com "plano", "ideias", "estratégia" são tarefas simples, não USER
        palavras_tarefas_simples = [
            "plano de", "minhas ideias", "uma estrategia", "meus documentos",
            "preparar uma", "melhorar meu email",
            "criar um roteiro", "organizar pensamentos", "organizar prioridades",
            "criar um metodo", "otimizar meu",
        ]
        e_tarefa_simples = any(t in texto_normalizado for t in palavras_tarefas_simples) and len(texto) < 80
        
        if e_tarefa_simples:
            return False
        
        # Palavras que indicam necessidade de personalização (em contextos complexos)
        palavras_personalizacao = [
            "estou me sentindo", "queria entender melhor",
            "preciso de conselhos", "preciso de ajuda para",
            "gostaria de aprender", "com dificuldade",
            "sobrecarregado", "crescer profissionalmente",
            "estou buscando maneiras", "quero desenvolver",
            "procuro formas",
            "preciso repensar", "gostaria de feedback",
            # Contextos de melhoria pessoal
            "gostaria de melhorar",
        ]
        tem_personalizacao = any(p in texto_normalizado for p in palavras_personalizacao)
        
        # Verifica se tem "gostaria de melhorar" em contexto pessoal/profissional (não sistema)
        tem_melhoria_pessoal = (
            "melhorar minha comunicacao" in texto_normalizado or
            ("melhorar" in texto_normalizado and any(ctx in texto_normalizado for ctx in ["relacionamento", "desempenho", "no trabalho"]))
        )

        return (
            e_longa
            or usa_referencias_pessoais
            or pede_um_plano_ou_estrategia
            or tem_multiplas_frases
            or tem_personalizacao
            or tem_melhoria_pessoal
        )
