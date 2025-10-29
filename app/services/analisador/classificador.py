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
        Determina a categoria da mensagem (system, messages, user, unclear).
        
        CATEGORIAS:
        - system: Comandos diretos de integração (enviar email, criar planilha)
        - messages: Perguntas factuais e informativas (O que é X?, Como funciona Y?)
        - user: Mensagens complexas/pessoais (saudações, contexto emocional)
        - unclear: Intenção ambígua ou incerta (não conseguimos determinar)
        
        Otimizado com buscas 'in' ao invés de regex onde possível.

        Args:
            mensagem_original: Mensagem original do usuário
            texto_normalizado: Texto normalizado para análise

        Returns:
            Tupla com (categoria, lista de motivos)
        """
        
        # ===================================================================
        # PRIORIDADE 0: MENSAGENS AMBÍGUAS/INCOMPLETAS → UNCLEAR
        # ===================================================================
        # Verifica ANTES de tudo se a mensagem é clara o suficiente
        
        # Mensagens muito curtas (<= 15 caracteres) sem estrutura clara
        eh_ultra_curta = len(mensagem_original.strip()) <= 15
        num_palavras = len(texto_normalizado.split())
        
        if eh_ultra_curta and num_palavras <= 2:
            # Saudações comuns são exceção (USER, não UNCLEAR)
            saudacoes_comuns = [
                "oi", "ola", "oie", "opa", "e ai", "eai", 
                "bom dia", "boa tarde", "boa noite",
                "como vai", "tudo bem", "blz", "beleza"
            ]
            if any(s in texto_normalizado for s in saudacoes_comuns):
                return "user", ["Saudação conversacional"]
            
            # Confirmações/feedback são USER
            confirmacoes = ["ok", "sim", "nao", "entendi", "certo", "beleza", "hmm", "talvez"]
            if texto_normalizado.strip() in confirmacoes:
                return "user", ["Resposta/feedback conversacional"]
            
            # Expressões de incerteza → UNCLEAR
            incertezas = ["nao sei", "sei la", "talvez", "acho que"]
            if any(inc in texto_normalizado for inc in incertezas):
                return "unclear", ["Expressão de incerteza - precisa de esclarecimento"]
            
            # Palavras soltas sem contexto → UNCLEAR
            palavras_genericas = ["documento", "email", "arquivo", "planilha", "fazer", "criar", "enviar"]
            if any(p == texto_normalizado.strip() for p in palavras_genericas):
                return "unclear", ["Palavra solta sem contexto - precisa de esclarecimento"]
            
            # Pronomes/demonstrativos sozinhos → UNCLEAR
            pronomes_demonstrativos = ["isso", "aquilo", "este", "esse", "aquele", "la", "ca"]
            if texto_normalizado.strip() in pronomes_demonstrativos:
                return "unclear", ["Referência ambígua - precisa de contexto"]
            
            # Palavras interrogativas sozinhas → UNCLEAR
            interrogativas_sozinhas = ["como", "quando", "onde", "que", "qual", "quem", "quanto"]
            if texto_normalizado.strip() in interrogativas_sozinhas:
                return "unclear", ["Pergunta incompleta - precisa de mais informação"]
            
            # Palavras muito curtas sem significado claro
            if num_palavras == 1 and len(texto_normalizado.strip()) < 6:
                return "unclear", ["Mensagem muito curta sem contexto claro"]
        
        # Frases que parecem teste/sem sentido (2-3 palavras aleatórias)
        if num_palavras <= 3 and len(mensagem_original.strip()) < 20:
            # Verifica se tem palavras muito comuns ou padrão de teste
            palavras_teste = ["teste", "abc", "xyz", "123", "aaa", "bbb"]
            if any(pt in texto_normalizado for pt in palavras_teste):
                return "unclear", ["Parece mensagem de teste - sem intenção clara"]
        
        # ===================================================================
        # PRIORIDADE 0.2: AMBIGUIDADE CONTEXTUAL/SEMÂNTICA → UNCLEAR
        # ===================================================================
        # Detecta 3 tipos de ambiguidade real:
        # 1️⃣ Contextual: referências sem antecedente ("manda pra ela", "abre isso")
        # 2️⃣ Incompleto semântico: objetos/destinos indefinidos ("gera o documento")
        # 3️⃣ Intenção dupla: múltiplas ações conflitantes ("pode criar ou editar?")
        
        # 1️⃣ AMBIGUIDADE CONTEXTUAL - Pronomes/demonstrativos sem referência clara
        # EXCEÇÃO: Mensagens conversacionais leves (confirmações, feedback) NÃO são ambíguas
        mensagens_conversacionais_claras = [
            "beleza", "ok", "certo", "entendi", "obrigado", "obrigada",
            "valeu", "legal", "otimo", "perfeito", "maravilha",
            "pode continuar", "pode seguir", "tudo certo", "esta certo",
            "deu certo", "ficou otimo", "ficou bom", "ta bom",
            "entao ta", "deixa como esta", "nao precisa",
            "me lembra", "era isso", "e isso mesmo", "me atualiza"
            # NOTA: "me avisa" removido para não conflitar com comandos
        ]
        
        # Se é mensagem conversacional clara, retorna MESSAGE (não UNCLEAR)
        if any(msg in texto_normalizado for msg in mensagens_conversacionais_claras):
            return "message", ["Mensagem conversacional (confirmação/feedback)"]
        
        # Frases com "o resto", "depois que terminar" são ambíguas
        frases_resto_ambiguas = [
            "faz o resto", "faz o restante", "depois que terminar",
            "quando acabar", "quando finalizar"
        ]
        
        if any(frase in texto_normalizado for frase in frases_resto_ambiguas):
            return "unclear", ["Referência vaga - 'o resto' ou condição temporal indefinida"]
        
        pronomes_sem_contexto = [
            (" ela ", "ela"), (" ele ", "ele"), (" eles ", "eles"), (" elas ", "elas"),
            (" isso ", "isso"), (" aquilo ", "aquilo"), (" disso ", "disso"), (" daquilo ", "daquilo"),
            (" esse ", "esse"), (" esta ", "esta"),
            # NOTA: Removidos "essa" (falso positivo em "sessão"), "este", "aqui", "ali"
            # para evitar detecções incorretas em palavras compostas
        ]
        
        # EXCEÇÃO: Mensagens longas conversacionais (>100 chars, >15 palavras)
        # Não aplicar regra de pronome ambíguo em textos conversacionais extensos
        eh_mensagem_longa_conversacional = (
            len(mensagem_original) > 100 and 
            num_palavras > 15 and
            any(termo in texto_normalizado for termo in ["gostaria", "poderia", "agradecer", "obrigado", "poderia me ajudar", "me ajudar"])
        )
        
        if not eh_mensagem_longa_conversacional:
            tem_pronome_ambiguo = False
            pronome_encontrado = ""
            
            for busca, nome in pronomes_sem_contexto:
                if busca in texto_normalizado:
                    # Verifica se NÃO tem antecedente claro (substantivo específico antes)
                    # Ex: "manda pra ela" → ambíguo | "manda pra maria" → claro
                    substantivos_claros = [
                        "maria", "joao", "pedro", "ana", "carlos", "jose",
                        "arquivo", "documento", "planilha", "email", "relatorio"
                    ]
                    
                    # Se tem pronome mas não tem substantivo específico → ambíguo
                    if not any(subst in texto_normalizado for subst in substantivos_claros):
                        tem_pronome_ambiguo = True
                        pronome_encontrado = nome
                        break
            
            # Caso especial: múltiplos destinatários com pronome ambíguo
            # "manda pro João e pra ela também" → "ela" é ambígua mesmo tendo "João"
            # "troca o nome e manda pra ela" → "ela" é ambígua
            if " e pra ela" in texto_normalizado or " e pra ele" in texto_normalizado:
                tem_pronome_ambiguo = True
                pronome_encontrado = "ela/ele" if " e pra ela" in texto_normalizado else "ele"
            
            # "manda pra ela" sozinho também é ambíguo
            if " pra ela" in texto_normalizado or " pra ele" in texto_normalizado:
                # Exceção: se tem nome próprio específico antes não é ambíguo
                nomes_proprios = ["maria", "joao", "ana", "pedro", "carlos", "jose", "paulo"]
                if not any(nome in texto_normalizado for nome in nomes_proprios):
                    tem_pronome_ambiguo = True
                    pronome_encontrado = "ela" if " pra ela" in texto_normalizado else "ele"
            
            if tem_pronome_ambiguo:
                return "unclear", [f"Referência ambígua ('{pronome_encontrado}') sem antecedente claro"]        # Referências temporais/comparativas ambíguas
        referencias_temporais_ambiguas = [
            "de antes", "da outra vez", "do outro dia", "de ontem",
            "mesmo lugar", "mesmo jeito", "o mesmo que", "igual ao",
            "o que a gente", "o que voce", "o que eu",
            "aquele problema", "aquele erro", "aquele arquivo", "aquele documento"
        ]
        
        if any(ref in texto_normalizado for ref in referencias_temporais_ambiguas):
            return "unclear", ["Referência temporal/comparativa ambígua - depende de contexto anterior"]
        
        # Termos vagos/subjetivos sem definição
        termos_vagos = [
            "o necessario", "o que precisar", "o que for melhor",
            "tudo certo", "deixa certo", "ajeita", "resolve",
            "cuida disso", "da um jeito", "faz funcionar"
        ]
        
        if any(termo in texto_normalizado for termo in termos_vagos):
            return "unclear", ["Termo vago/subjetivo sem definição clara da ação"]
        
        # Expressões condicionais/temporais indefinidas
        condicoes_indefinidas = [
            "se for o caso", "se precisar", "se der",
            "quando der", "quando puder", "quando for possivel",
            "talvez precise", "pode ser que", "acho que talvez"
        ]
        
        if any(cond in texto_normalizado for cond in condicoes_indefinidas):
            return "unclear", ["Condição temporal/condicional indefinida - falta clareza sobre quando/se executar"]
        
        # 2️⃣ AMBIGUIDADE DE OBJETO INCOMPLETO - Ações com objetos genéricos indefinidos
        # "gera o documento" (qual?), "envia pro Google" (o quê?), "salva na planilha" (qual?)
        acoes_com_objeto_generico = [
            ("gera o", "objeto a gerar não especificado"),
            ("cria o", "objeto a criar não especificado"),
            ("envia o", "objeto a enviar não especificado"),
            ("manda o", "objeto a enviar não especificado"),
            ("salva o", "objeto a salvar não especificado"),
            ("abre o", "objeto a abrir não especificado"),
            ("deleta o", "objeto a deletar não especificado"),
            ("exclui o", "objeto a excluir não especificado"),
            ("edita o", "objeto a editar não especificado"),
            ("verifica o", "objeto a verificar não especificado"),  # NOVO
            ("revisa o", "objeto a revisar não especificado"),     # NOVO
        ]
        
        for padrao, motivo in acoes_com_objeto_generico:
            if padrao in texto_normalizado:
                # Verifica se o objeto é genérico ("documento", "arquivo") sem especificação
                palavras_genericas_objeto = ["documento", "arquivo", "email", "planilha", "relatorio", "cadastro"]
                if any(gen in texto_normalizado for gen in palavras_genericas_objeto):
                    # Exceção: se tem especificação clara (nome, data, pessoa específica, contexto específico)
                    tem_especificacao = any(esp in texto_normalizado for esp in [
                        "chamado", "chamada", " reuniao ", " da reuniao ",
                        "@", ".com", ".pdf", ".docx", ".xlsx"
                    ])
                    
                    # IMPORTANTE: mesmo com "cliente" no texto, ainda pode ser ambíguo
                    # "sobe o arquivo do cliente Pedro" → qual arquivo?
                    # "verifica o cadastro" → qual cadastro?
                    
                    if not tem_especificacao:
                        return "unclear", [f"Ação incompleta: {motivo}"]
        
        # Casos adicionais: modificadores temporais sem especificação clara
        if "de novo" in texto_normalizado and any(v in texto_normalizado for v in ["cria", "gera", "faz", "envia"]):
            # "cria o documento de novo" - qual documento?
            if not any(esp in texto_normalizado for esp in [" cliente ", " projeto ", " reuniao ", "chamado"]):
                return "unclear", ["Modificador 'de novo' sem especificação - refazer qual ação/objeto?"]
        
        # Destinos genéricos sem especificação
        # IMPORTANTE: "envia o documento pro meu drive" NÃO é ambíguo (tem destino: drive)
        # Mas "envia o documento" sozinho É ambíguo
        destinos_genericos_ambiguos = [
            ("envia o documento", "documento genérico sem especificação"),
            ("envia o arquivo", "arquivo genérico sem especificação"),
            ("envia a planilha", "planilha genérica sem especificação"),
            ("manda o documento", "documento genérico sem especificação"),
            ("manda o arquivo", "arquivo genérico sem especificação"),
        ]
        
        for padrao, motivo in destinos_genericos_ambiguos:
            if padrao in texto_normalizado:
                # EXCEÇÃO 1: Se tem destino específico (drive, email, sheets, etc.)
                tem_destino_especifico = any(dest in texto_normalizado for dest in [
                    "drive", "gmail", "sheets", "docs", "calendar", "email", "slack"
                ])
                
                # EXCEÇÃO 2: Se tem especificação do arquivo (nome, tipo)
                tem_especificacao = any(esp in texto_normalizado for esp in [
                    ".pdf", ".docx", ".xlsx", "chamado", "contrato", "relatorio de"
                ])
                
                # Se não tem destino NEM especificação → UNCLEAR
                if not tem_destino_especifico and not tem_especificacao:
                    return "unclear", [f"Ação incompleta: {motivo}"]
        
        # Outros destinos genéricos
        outros_destinos_genericos = [
            ("salva na planilha", "planilha não especificada"),
            ("salva na pasta", "pasta não especificada"),
            ("coloca na pasta", "pasta não especificada"),
            ("coloca no calendario", "evento não especificado"),
            ("envia pro email", "destinatário não especificado"),
        ]
        
        for padrao, motivo in outros_destinos_genericos:
            if padrao in texto_normalizado:
                # Exceção: se tem nome específico
                if not any(esp in texto_normalizado for esp in [" cliente ", " projeto ", " chamado", " reuniao "]):
                    return "unclear", [f"Destino incompleto: {motivo}"]
        
        # 3️⃣ AMBIGUIDADE DE INTENÇÃO DUPLA - Múltiplas ações sem prioridade
        # "pode criar ou editar?", "gera e envia", "deletar ou arquivar?"
        conectores_dupla_intencao = [
            " ou ", " e ", " / ", " e/ou "
        ]
        
        # Verbos de ação (infinitivo E conjugações comuns)
        verbos_acao_sistema = [
            # Infinitivo
            "criar", "gerar", "enviar", "mandar", "deletar", "excluir",
            "editar", "modificar", "salvar", "abrir", "fechar", "arquivar",
            "fazer", "produzir", "compartilhar", "baixar", "fazer upload",
            # Conjugações comuns (3ª pessoa e imperativo)
            "cria", "gera", "envia", "manda", "deleta", "exclui",
            "edita", "modifica", "salva", "abre", "fecha", "arquiva",
            "faz", "produz", "compartilha", "baixa",
            # Imperativo
            "crie", "gere", "envie", "mande", "delete", "exclua",
            "edite", "modifique", "salve", "abra", "feche", "archive"
        ]
        
        tem_conector = any(conector in texto_normalizado for conector in conectores_dupla_intencao)
        
        if tem_conector:
            # Conta quantos verbos de ação aparecem
            verbos_encontrados_lista = [verbo for verbo in verbos_acao_sistema if verbo in texto_normalizado]
            
            if len(verbos_encontrados_lista) >= 2:
                # Exceção: se é pergunta sobre capacidade, não é unclear
                if not any(p in texto_normalizado for p in ["voce pode", "voce consegue", "e possivel"]):
                    return "unclear", [f"Múltiplas ações ({', '.join(verbos_encontrados_lista[:2])}) - qual executar?"]
        
        # 4️⃣ AMBIGUIDADE DE DOMÍNIO - Termos polissêmicos específicos
        # "sobe o arquivo" (upload ou move?), "corrige a conta" (valor ou perfil?)
        termos_polissemicos = [
            ("sobe o", "termo 'sobe' ambíguo - upload, move para pasta superior?"),
            ("sobe ", "termo 'sobe' ambíguo - upload, move para pasta superior?"),
            ("corrige a conta", "termo 'conta' ambíguo - valor financeiro ou perfil de usuário?"),
            ("corrige o", "termo 'corrige' ambíguo - qual tipo de correção?"),
            ("cria um registro", "termo 'registro' ambíguo - onde? em qual sistema/planilha?"),
        ]
        
        for padrao, motivo in termos_polissemicos:
            if padrao in texto_normalizado:
                # NOTA: mesmo com "cliente" no texto, "sobe o arquivo" é ambíguo
                # "sobe o arquivo do cliente Pedro" → upload para onde? qual arquivo?
                # A ambiguidade é do VERBO "sobe", não do objeto
                return "unclear", [f"Ambiguidade de domínio: {motivo}"]
        
        # ===================================================================
        # PRIORIDADE 0.5: PERGUNTAS DE CAPACIDADE → MESSAGES
        # ===================================================================
        # IMPORTANTE: Deve vir ANTES da verificação de SYSTEM
        # "você pode enviar email?", "você tem sincronização?" são perguntas, não comandos
        
        # EXCEÇÃO 0: Mensagens longas conversacionais (>100 chars) → USER
        # Evita que frases longas com "você poderia" sejam classificadas como MESSAGES
        if eh_mensagem_longa_conversacional:
            # Mensagem conversacional longa sem comando claro → USER
            return "user", ["Mensagem conversacional longa - sem comando de integração"]
        
        # EXCEÇÃO 1: Expressões de incerteza TÊM PRIORIDADE sobre perguntas de capacidade
        # "não tenho certeza se dá pra criar" → UNCLEAR (não MESSAGES)
        expressoes_incerteza = [
            "nao tenho certeza", "nao sei se", "nao tenho", "nao sei",
            "acho que talvez", "talvez precise", "pode ser que",
            "nao estou certo", "nao estou seguro"
        ]
        
        if any(inc in texto_normalizado for inc in expressoes_incerteza):
            # Se tem incerteza + ação → UNCLEAR (mesmo que tenha "dá pra")
            if any(v in texto_normalizado for v in ["criar", "gerar", "enviar", "deletar", "fazer", "cria", "gera", "faz"]):
                return "unclear", ["Expressão de incerteza sobre ação - falta confirmação"]
        
        # EXCEÇÃO 2: Perguntas com múltiplas opções ambíguas → UNCLEAR (não MESSAGES)
        # "antes ou depois?", "deleta ou mantém?" são ambíguas, não perguntas de capacidade
        if " ou " in texto_normalizado:
            if mensagem_original.endswith("?"):
                # É uma pergunta com opções ambíguas
                if any(v in texto_normalizado for v in ["antes", "depois", "manda", "envia", "deleta", "mantem", "cria", "edita"]):
                    return "unclear", ["Pergunta com múltiplas opções sem contexto - não há resposta clara"]
        
        perguntas_capacidade = [
            "voce pode", "voce consegue", "voce tem",
            "e possivel", "da pra", "tem como", "existe alguma forma",
            "como faco", "como fazer", "como funciona",  # NOVO: "como funciona" é pergunta
            "onde esta", "onde fica", "o que e", "qual e"
        ]
        if any(p in texto_normalizado for p in perguntas_capacidade):
            return "messages", ["Pergunta sobre capacidade (não é comando)"]

        # ===================================================================
        # PRIORIDADE 1: COMANDOS INTERNOS (SYSTEM) vs APIs EXTERNAS (USER)
        # ===================================================================
        # SYSTEM: Comandos de controle interno (sessão, cache, logs, webhooks)
        # USER: Comandos que requerem APIs externas (Google, OAuth, etc.)
        
        # Palavras-chave que indicam comando SYSTEM (interno)
        palavras_system_interno = [
            "sessao", "cache", "log", "logs", "webhook", "webhooks",
            "variaveis de ambiente", "variavel de ambiente", "depuracao", "debug",
            "modo teste", "modo de teste", "agente", "banco", "database",
            "microservico", "api interna", "infraestrutura", "backend",
            "monique", "historico de conversa", "historico"  # Referência explícita à IA
        ]
        
        # Verbos que indicam operação de sistema interno
        verbos_system = [
            "reinicia", "reiniciar", "limpa", "limpar", "atualiza",
            "verifica", "habilita", "habilitar", "ativa", "ativar",
            "desativa", "desativar", "desconecta", "desconectar", "refresh",
            "forca", "forcar", "mostra", "me mostra"
        ]
        
        # Verifica se é comando SYSTEM (interno)
        # IMPORTANTE: "verifica se" também deve ser considerado
        eh_comando_system = (
            any(p in texto_normalizado for p in palavras_system_interno) and
            (any(v in texto_normalizado for v in verbos_system) or "verifica se" in texto_normalizado)
        )
        
        if eh_comando_system:
            return "system", ["Comando de controle interno do sistema"]
        
        # Palavras-chave que indicam necessidade de API EXTERNA (USER)
        palavras_apis_externas = [
            "google calendar", "calendar", "gmail", "google drive", "drive",
            "google sheets", "sheets", "google docs", "google meet", "meet",
            "google tasks", "tasks", "google photos", "photos",
            "oauth", "autenticacao google", "conta google", "api google"
        ]
        
        # Verifica se é comando USER (API externa)
        eh_comando_api_externa = any(p in texto_normalizado for p in palavras_apis_externas)
        
        if eh_comando_api_externa:
            return "user", ["Comando que requer API externa (Google, OAuth)"]

        # Prioridade 2: É um pedido que envolve sistemas/integrações genéricas?
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
        # Analisa características sutis para decidir - ou retorna UNCLEAR se ambíguo
        
        # INDICADORES DE CONFIANÇA
        tem_multiplas_frases = (
            len([s for s in mensagem_original.split('.') if s.strip()]) +
            len([s for s in mensagem_original.split('?') if s.strip()]) +
            len([s for s in mensagem_original.split('!') if s.strip()])
        ) > 2
        
        eh_mensagem_longa = len(mensagem_original) > 150
        eh_mensagem_muito_curta = len(mensagem_original.strip()) < 10
        
        # Pronomes pessoais indicam contexto USER
        pronomes_pessoais = [" meu ", " minha ", " meus ", " minhas ", " eu ", " me ", " comigo "]
        tem_pronomes_pessoais = any(p in f" {texto_normalizado} " for p in pronomes_pessoais)
        
        # Palavras interrogativas sem outros indicadores claros
        palavras_interrogativas = ["como", "quando", "onde", "por que", "porque", "qual", "que", "quem"]
        tem_palavra_interrogativa = any(p in texto_normalizado.split() for p in palavras_interrogativas)
        
        # DECISÃO COM BASE EM INDICADORES
        
        # Se tem múltiplas frases ou é muito longa → provavelmente USER
        if tem_multiplas_frases or eh_mensagem_longa:
            return "user", ["Mensagem longa ou com múltiplas ideias - requer contexto"]
        
        # Se tem pronomes pessoais → provavelmente USER
        if tem_pronomes_pessoais:
            return "user", ["Contém contexto pessoal"]
        
        # Mensagens muito curtas sem contexto → pode ser saudação (USER) ou ambíguo
        if eh_mensagem_muito_curta:
            # Saudações comuns
            saudacoes = ["oi", "ola", "oie", "opa", "e ai", "bom dia", "boa tarde", "boa noite"]
            if any(s in texto_normalizado for s in saudacoes):
                return "user", ["Saudação conversacional"]
            
            # Muito curto e sem contexto claro → UNCLEAR
            return "unclear", ["Mensagem muito curta sem contexto claro"]
        
        # Palavras interrogativas sem "?" e sem contexto técnico → ambíguo
        if tem_palavra_interrogativa and "?" not in mensagem_original:
            palavras_tecnicas = ["git", "python", "api", "codigo", "sistema", "funciona"]
            tem_contexto_tecnico = any(p in texto_normalizado for p in palavras_tecnicas)
            
            if not tem_contexto_tecnico:
                return "unclear", ["Possível pergunta sem contexto claro"]
        
        # Mensagens curtas (10-20 chars) sem indicadores fortes
        if len(mensagem_original.strip()) < 20:
            return "unclear", ["Mensagem curta sem indicadores claros de intenção"]
        
        # Default: MESSAGES (resposta simples e direta)
        # Usado quando temos alguma confiança mas sem indicadores específicos
        return "messages", ["Mensagem genérica - classificação por eliminação"]

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
            "tem como",        # NOVO: "tem como sincronizar?"
            "existe alguma forma",
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
