"""
TESTE MASSIVO DE CLASSIFICAÇÃO
===============================
Valida centenas de frases em todos os tempos verbais
Garante que NUNCA classificaremos errado
"""

import sys
from pathlib import Path
from collections import defaultdict

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.services.analisador.classificador import Classificador
from app.services.analisador.normalizador import normalizar_texto
from app.utils.lematizador import (
    lematizar_texto,
    extrair_verbos_de_acao,
    obter_estatisticas,
    VERBOS_INFINITIVOS
)

# ============================================================================
# CASOS DE TESTE MASSIVOS
# ============================================================================

# SYSTEM: Comandos diretos de integração
CASOS_SYSTEM = [
    # === ENVIAR (todos os tempos verbais) ===
    "envie um email para joão",
    "envia o relatório agora",
    "enviando a planilha para maria",
    "enviado o documento ontem",
    "enviada a apresentação",
    "enviei o email ontem",
    "enviou a fatura",
    "enviaram os arquivos",
    "enviarei o backup amanhã",
    "enviaremos os dados",
    # "enviaria se pudesse",  # MOVIDO PARA MESSAGES - condicional hipotética
    "enviariam os documentos",
    
    # === CRIAR ===
    "crie uma planilha nova",
    "cria um documento",
    "criando apresentação",
    "criado o rascunho",
    "criada a agenda",
    "criei a planilha",
    "criou o documento",
    "criaram os slides",
    "criarei um backup",
    "criaremos a fatura",
    
    # === AGENDAR/MARCAR ===
    "agende uma reunião amanhã",
    "agenda o compromisso",
    "agendando a call",
    "agendado o evento",
    "agendei a reunião",
    "agendou o meeting",
    "marque uma reunião",
    "marca o compromisso",
    "marcando a call",
    "marquei a reunião às 14h",
    "marcou o evento",
    "marcaram a aula",
    
    # === CANCELAR ===
    "cancele o agendamento",
    "cancela a reunião",
    "cancelando o evento",
    "cancelado o compromisso",
    "cancelei a reunião",
    "cancelou a call",
    "cancelaram o meeting",
    "gostaria de cancelar o agendamento",
    "preciso cancelar a reunião de amanhã",
    "quero cancelar o compromisso",
    
    # === REAGENDAR ===
    "reagende a reunião",
    "reagenda o compromisso",
    "reagendando a call",
    "reagendei o meeting",
    "reagendou o evento",
    "gostaria de reagendar o agendamento",
    "preciso reagendar a reunião",
    
    # === EXCLUIR/DELETAR/REMOVER ===
    "exclua o documento",
    "exclui o arquivo",
    "excluindo a planilha",
    "excluído o backup",
    "excluí o rascunho",
    "excluiu o email",
    "delete o arquivo",
    "deleta o documento",
    "deletando a planilha",
    "deletei o rascunho",
    "deletou o backup",
    "remova o email",
    "remove o arquivo",
    "removendo a planilha",
    "removi o documento",
    "removeu o backup",
    
    # === COMPARTILHAR ===
    "compartilhe o documento com a equipe",
    "compartilha a planilha",
    "compartilhando o arquivo com maria",
    "compartilhei o drive",
    "compartilhou os slides",
    
    # === EDITAR/MODIFICAR ===
    "edite o documento",
    "edita a planilha",
    "editando o arquivo",
    "editei o rascunho",
    "editou o email",
    "modifique a fatura",
    "modifica o boleto",
    "modificando a planilha",
    
    # === BAIXAR/FAZER DOWNLOAD ===
    "baixe o relatório",
    "baixa o arquivo",
    "baixando a planilha",
    "baixei o documento",
    "baixou o backup",
    "faça download do arquivo",
    "fazer download da planilha",
    
    # === FAZER UPLOAD/SUBIR ===
    "suba o arquivo",
    "sobe o documento",
    "subindo a planilha",
    "subi o backup",
    "subiu o relatório",
    "faça upload do arquivo",
    "fazer upload da planilha",
    
    # === BUSCAR/PROCURAR ===
    "busque o email de joão",
    "busca a planilha antiga",
    "buscando o documento",
    "busquei o arquivo",
    "buscou o backup",
    "procure o email",
    "procura o documento",
    
    # === SALVAR ===
    "salve o documento",
    "salva a planilha",
    "salvando o arquivo",
    "salvei o rascunho",
    "salvou o backup",
    
    # === IMPRIMIR ===
    "imprima o boleto",
    "imprime a fatura",
    "imprimindo o documento",
    "imprimi a planilha",
    "imprimiu o relatório",
    
    # === EXPORTAR/IMPORTAR ===
    "exporte a planilha",
    "exporta o relatório",
    "exportando os dados",
    "exportei o arquivo",
    "importe a planilha",
    "importa os dados",
    
    # === COPIAR/MOVER ===
    "copie o arquivo",
    "copia o documento",
    "copiando a planilha",
    "copiei o backup",
    "mova o arquivo",
    "move o documento",
    "movendo a planilha",
    
    # === PAGAR/TRANSFERIR ===
    "pague o boleto",
    "paga a fatura",
    "paguei a cobrança",
    "pagou o pix",
    "transfira o valor",
    "transfere o pagamento",
    "transferi o dinheiro",
    
    # === GERAR/EMITIR ===
    "gere um boleto",
    "gera a fatura",
    "gerando a cobrança",
    "gerei o relatório",
    "emita a nota fiscal",
    "emite o boleto",
    
    # === CASOS COMPOSTOS ===
    "envie um email com a planilha anexada",
    "crie uma reunião e compartilhe com a equipe",
    "agende uma call e envie o convite",
    "exclua o documento antigo e crie um novo",
    "baixe o arquivo e compartilhe com joão",
]

# MESSAGES: Perguntas diretas/objetivas
CASOS_MESSAGES = [
    # Perguntas curtas e factuais
    "o que é python?",
    "qual a capital da frança?",
    "quem foi einstein?",
    "como funciona o git?",
    "quando foi a segunda guerra?",
    "onde fica são paulo?",
    "por que o céu é azul?",
    
    # Perguntas sobre funcionalidades
    "o que você pode fazer?",
    "quais suas funcionalidades?",
    "você consegue enviar email?",
    "como posso usar você?",
    "me ajude com algo",
    
    # Perguntas sobre uso (não comandos)
    "como faço para cancelar?",
    "como usar a agenda?",
    "tutorial de email",
    "dicas de organização",
    
    # Frases condicionais/hipotéticas (sem comando direto)
    "enviaria se pudesse",
]

# USER: Mensagens complexas/pessoais/narrativas/conversacionais
CASOS_USER = [
    # Saudações e interações conversacionais
    "oi",
    "olá",
    "tudo bem?",
    "bom dia",
    "boa tarde",
    
    # Confirmações curtas
    "sim",
    "não",
    "ok",
    "entendi",
    "obrigado",
    
    # Narrativas (não comandos)
    "você viu que hackers baixaram dados da amazon?",
    "ele deletou o arquivo ontem sem querer",
    "maria enviou o email na sexta passada",
    "a equipe criou uma planilha incrível",
    "joão compartilhou o documento comigo",
    "eles agendaram uma reunião surpresa",
    "alguém cancelou meu compromisso",
    
    # Contextos pessoais/complexos
    "estou me sentindo sobrecarregado com trabalho",
    "preciso de conselhos sobre minha carreira",
    "gostaria de aprender programação",
    "estou com dificuldade em organizar meu tempo",
    "quero desenvolver minhas habilidades",
    "preciso repensar minha estratégia profissional",
    "gostaria de melhorar minha comunicação no trabalho",
    
    # Contextos abstratos (não integração)
    "melhorar meu email profissional",
    "organizar meus documentos mentalmente",
    "criar uma estratégia de estudo",
    "planejar minha carreira",
    
    # Perguntas complexas
    "como posso melhorar minha produtividade e organização pessoal ao mesmo tempo que desenvolvo novas habilidades?",
    "me explique detalhadamente como funciona o processo de aprendizado de máquina",
    "quais são as melhores práticas para gestão de projetos em equipes remotas?",
]

# CASOS AMBÍGUOS (precisam de contexto para classificar corretamente)
CASOS_ESPECIAIS = {
    # Devem ser MESSAGES (perguntas, não comandos)
    "messages": [
        "você pode enviar email?",  # pergunta sobre capacidade
        "é possível agendar reunião?",  # pergunta sobre funcionalidade
        "como faço para criar planilha?",  # pergunta sobre como usar
        "onde está meu documento?",  # pergunta de localização
    ],
    
    # Devem ser SYSTEM (comandos implícitos)
    "system": [
        "preciso enviar um email urgente para joão",  # necessidade = comando
        "quero criar uma planilha nova",  # desejo = comando
        "vou agendar uma reunião amanhã",  # futuro próximo = comando
    ],
}


# ============================================================================
# FUNÇÕES DE TESTE
# ============================================================================

def test_categoria(casos: list, categoria_esperada: str, nome_categoria: str):
    """Testa uma categoria específica"""
    print(f"\n{'='*70}")
    print(f"🧪 TESTANDO: {nome_categoria.upper()} ({len(casos)} casos)")
    print(f"{'='*70}\n")
    
    acertos = 0
    erros = []
    
    for i, caso in enumerate(casos, 1):
        texto_norm = normalizar_texto(caso)
        categoria, motivos = Classificador.determinar_categoria(caso, texto_norm)
        
        correto = categoria == categoria_esperada
        status = "✅" if correto else "❌"
        
        if correto:
            acertos += 1
        else:
            erros.append({
                'caso': caso,
                'esperado': categoria_esperada,
                'obtido': categoria,
                'motivos': motivos
            })
        
        # Mostra apenas erros e amostra de acertos
        if not correto or i <= 5 or i % 20 == 0:
            print(f"{status} [{i:3d}] {caso[:60]:60s} → {categoria.upper()}")
            if not correto:
                print(f"      Esperado: {categoria_esperada.upper()}, Motivos: {motivos}")
    
    # Resumo
    taxa_acerto = (acertos / len(casos)) * 100
    print(f"\n📊 Resumo: {acertos}/{len(casos)} acertos ({taxa_acerto:.1f}%)")
    
    if erros:
        print(f"\n❌ {len(erros)} ERROS DETECTADOS:")
        for erro in erros[:10]:  # Mostra até 10 erros
            print(f"\n   Caso: '{erro['caso']}'")
            print(f"   Esperado: {erro['esperado'].upper()}")
            print(f"   Obtido: {erro['obtido'].upper()}")
            print(f"   Motivos: {erro['motivos']}")
    
    return acertos, len(casos), erros


def test_casos_especiais():
    """Testa casos ambíguos que precisam de contexto"""
    print(f"\n{'='*70}")
    print(f"🎯 TESTANDO: CASOS ESPECIAIS (Ambíguos)")
    print(f"{'='*70}\n")
    
    total_acertos = 0
    total_casos = 0
    
    for categoria_esperada, casos in CASOS_ESPECIAIS.items():
        print(f"\n  → Deve ser {categoria_esperada.upper()}:")
        for caso in casos:
            texto_norm = normalizar_texto(caso)
            categoria, motivos = Classificador.determinar_categoria(caso, texto_norm)
            
            correto = categoria == categoria_esperada
            status = "✅" if correto else "❌"
            total_casos += 1
            
            if correto:
                total_acertos += 1
            
            print(f"     {status} '{caso}' → {categoria.upper()}")
            if not correto:
                print(f"         Esperado: {categoria_esperada.upper()}, Motivos: {motivos}")
    
    taxa = (total_acertos / total_casos) * 100
    print(f"\n  📊 Casos especiais: {total_acertos}/{total_casos} ({taxa:.1f}%)")
    
    return total_acertos, total_casos


def verificar_aprendizado():
    """Verifica o sistema de aprendizado de verbos"""
    print(f"\n{'='*70}")
    print(f"🧠 SISTEMA DE APRENDIZADO")
    print(f"{'='*70}\n")
    
    stats = obter_estatisticas()
    
    print(f"📚 Dicionário Estático:")
    print(f"   • Conjugações: {stats['dicionario_estatico']['total_conjugacoes']}")
    print(f"   • Verbos únicos: {stats['dicionario_estatico']['verbos_unicos_infinitivo']}")
    
    print(f"\n🧠 Dicionário Aprendido:")
    print(f"   • Palavras aprendidas: {stats['dicionario_aprendido']['total_palavras_aprendidas']}")
    print(f"   • Pendentes de salvar: {stats['dicionario_aprendido']['palavras_desde_ultimo_save']}")
    
    print(f"\n⚡ Cache:")
    print(f"   • Taxa de acerto: {stats['cache']['taxa_acerto_pct']:.1f}%")
    print(f"   • Tamanho: {stats['cache']['tamanho_atual']}/{stats['cache']['tamanho_maximo']}")
    
    print(f"\n🤖 spaCy:")
    print(f"   • Disponível: {'✅ Sim' if stats['spacy']['disponivel'] else '❌ Não'}")
    print(f"   • Carregado: {'✅ Sim' if stats['spacy']['carregado'] else '❌ Não'}")
    
    print(f"\n📊 TOTAL:")
    print(f"   • Palavras conhecidas: {stats['total_palavras_conhecidas']}")
    print(f"   • Verbos de integração: {len(VERBOS_INFINITIVOS)}")


def main():
    print("\n" + "="*70)
    print("🚀 TESTE MASSIVO DE CLASSIFICAÇÃO - VALIDAÇÃO COMPLETA")
    print("="*70)
    
    # Estatísticas gerais
    resultados = {
        'total_acertos': 0,
        'total_casos': 0,
        'erros_por_categoria': defaultdict(list)
    }
    
    # Testa SYSTEM
    acertos, total, erros = test_categoria(CASOS_SYSTEM, "system", "SYSTEM (Comandos de Integração)")
    resultados['total_acertos'] += acertos
    resultados['total_casos'] += total
    resultados['erros_por_categoria']['system'] = erros
    
    # Testa MESSAGES
    acertos, total, erros = test_categoria(CASOS_MESSAGES, "messages", "MESSAGES (Perguntas Diretas)")
    resultados['total_acertos'] += acertos
    resultados['total_casos'] += total
    resultados['erros_por_categoria']['messages'] = erros
    
    # Testa USER
    acertos, total, erros = test_categoria(CASOS_USER, "user", "USER (Complexas/Pessoais)")
    resultados['total_acertos'] += acertos
    resultados['total_casos'] += total
    resultados['erros_por_categoria']['user'] = erros
    
    # Testa casos especiais
    acertos, total = test_casos_especiais()
    resultados['total_acertos'] += acertos
    resultados['total_casos'] += total
    
    # Verifica aprendizado
    verificar_aprendizado()
    
    # RELATÓRIO FINAL
    print(f"\n{'='*70}")
    print("📊 RELATÓRIO FINAL")
    print(f"{'='*70}\n")
    
    taxa_geral = (resultados['total_acertos'] / resultados['total_casos']) * 100
    
    print(f"✅ Total de acertos: {resultados['total_acertos']}/{resultados['total_casos']}")
    print(f"📈 Taxa de acerto geral: {taxa_geral:.2f}%")
    
    # Análise por categoria
    print(f"\n📋 Erros por categoria:")
    for cat, erros in resultados['erros_por_categoria'].items():
        if erros:
            print(f"   • {cat.upper()}: {len(erros)} erros")
    
    # Veredito
    print(f"\n{'='*70}")
    if taxa_geral >= 95:
        print("🎉 EXCELENTE! Sistema com alta confiabilidade (≥95%)")
    elif taxa_geral >= 90:
        print("✅ BOM! Sistema funcional (≥90%)")
    elif taxa_geral >= 80:
        print("⚠️  ATENÇÃO! Sistema precisa melhorar (≥80%)")
    else:
        print("❌ CRÍTICO! Sistema precisa revisão urgente (<80%)")
    
    print(f"{'='*70}\n")
    
    return taxa_geral >= 90


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
