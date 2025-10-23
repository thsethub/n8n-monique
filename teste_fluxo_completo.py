"""
Teste de Fluxo Completo - Mensagem Complexa Real
Testa todo o pipeline: Normalizador → Lematizador → Classificador
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.services.analisador.classificador import Classificador
from app.services.analisador.normalizador import normalizar_texto
from app.utils.lematizador import obter_estatisticas, lematizar_texto, extrair_verbos_de_acao

print("=" * 80)
print("🧪 TESTE DE FLUXO COMPLETO - MENSAGENS COMPLEXAS E REAIS")
print("=" * 80)
print()

# ============================================================================
# CASOS DE TESTE REAIS E COMPLEXOS
# ============================================================================

casos_teste = [
    {
        "mensagem": "Oi! Tudo bem? Preciso que você envie um email urgente para joão@empresa.com com a planilha de vendas do mês passado anexada. É muito importante!",
        "esperado": "system",
        "descricao": "Saudação + comando de integração urgente com múltiplas informações"
    },
    {
        "mensagem": "Você viu que a Maria deletou aquele arquivo importante ontem sem querer? Ela ficou desesperada tentando recuperar. No fim, o João conseguiu restaurar do backup que ele tinha feito na semana passada.",
        "esperado": "user",
        "descricao": "Narrativa complexa sobre terceiros com múltiplos eventos"
    },
    {
        "mensagem": "Preciso urgentemente agendar uma reunião com o time de desenvolvimento para amanhã às 14h, criar uma apresentação no Google Slides sobre os resultados do trimestre, e depois enviar o convite por email para todos os participantes com a pauta anexada.",
        "esperado": "system",
        "descricao": "Múltiplos comandos de integração encadeados em uma frase longa"
    },
    {
        "mensagem": "Estou me sentindo completamente sobrecarregado com a quantidade de tarefas que tenho. Preciso aprender a gerenciar melhor meu tempo e organizar meus projetos de uma forma mais eficiente. Você tem alguma dica ou metodologia que poderia me ajudar a melhorar minha produtividade?",
        "esperado": "user",
        "descricao": "Pedido de ajuda pessoal complexo com contexto emocional"
    },
    {
        "mensagem": "Como funciona o sistema de versionamento Git? Quero entender os conceitos de branch, merge e pull request.",
        "esperado": "messages",
        "descricao": "Pergunta técnica direta sem contexto pessoal"
    },
    {
        "mensagem": "Boa tarde! Você consegue me explicar passo a passo como faço para integrar o n8n com o Gmail? Nunca usei antes.",
        "esperado": "messages",
        "descricao": "Saudação + pergunta sobre capacidade/tutorial"
    },
    {
        "mensagem": "Crie uma planilha nova chamada 'Controle Financeiro 2025', adicione as colunas Data, Descrição, Valor Entrada, Valor Saída e Saldo, e compartilhe com ana@contabilidade.com com permissão de edição.",
        "esperado": "system",
        "descricao": "Comando complexo com múltiplas etapas e detalhes específicos"
    },
    {
        "mensagem": "Ontem a equipe de TI criou um sistema incrível de automação. O Pedro programou a integração principal, a Carla configurou os webhooks, e o time de QA testou tudo durante a tarde. Ficou sensacional!",
        "esperado": "user",
        "descricao": "Narrativa detalhada sobre trabalho em equipe no passado"
    },
    {
        "mensagem": "Bom dia! :)",
        "esperado": "user",
        "descricao": "Saudação simples e amigável"
    },
    {
        "mensagem": "Cancele minha reunião das 15h de hoje e reagende para segunda-feira no mesmo horário. Depois me lembre disso amanhã de manhã às 9h.",
        "esperado": "system",
        "descricao": "Cancelamento + reagendamento + lembrete (múltiplas integrações)"
    },
    {
        "mensagem": "O que é inteligência artificial? E machine learning? São a mesma coisa?",
        "esperado": "messages",
        "descricao": "Múltiplas perguntas factuais relacionadas"
    },
    {
        "mensagem": "Preciso criar uma estratégia completa de crescimento profissional para os próximos 5 anos, incluindo certificações que devo buscar, habilidades para desenvolver, networking estratégico e planejamento financeiro para investir em minha educação continuada.",
        "esperado": "user",
        "descricao": "Planejamento pessoal abstrato de longo prazo"
    },
    {
        "mensagem": "Enviaria o relatório se pudesse, mas não tenho acesso ao sistema agora.",
        "esperado": "messages",
        "descricao": "Condicional hipotética com justificativa"
    },
    {
        "mensagem": "Baixe o backup completo do servidor, exporte todos os dados em formato CSV, suba tudo para o Google Drive na pasta 'Backups 2025', e me envie o link de compartilhamento por email.",
        "esperado": "system",
        "descricao": "Sequência complexa de 4 comandos de integração"
    },
    {
        "mensagem": "Me ajude a entender como funcionam as automações no n8n. Nunca trabalhei com workflow antes.",
        "esperado": "messages",
        "descricao": "Pedido de ajuda/tutorial genérico"
    },
]

# ============================================================================
# EXECUÇÃO DOS TESTES
# ============================================================================

resultados = []
total_corretos = 0
total_casos = len(casos_teste)

print(f"Testando {total_casos} mensagens complexas reais...\n")
print("=" * 80)

for i, caso in enumerate(casos_teste, 1):
    print(f"\n📝 CASO {i}/{total_casos}")
    print(f"━" * 80)
    print(f"Mensagem: \"{caso['mensagem']}\"")
    print(f"Descrição: {caso['descricao']}")
    print(f"Esperado: {caso['esperado'].upper()}")
    
    # Analisa a mensagem (pipeline completo)
    texto_normalizado = normalizar_texto(caso['mensagem'])
    categoria, motivos = Classificador.determinar_categoria(caso['mensagem'], texto_normalizado)
    
    # Extrai informações adicionais
    texto_lematizado = lematizar_texto(texto_normalizado)
    verbos_encontrados = extrair_verbos_de_acao(texto_normalizado)
    
    resultado = {
        'categoria': categoria,
        'motivos': motivos,
        'detalhes': {
            'texto_normalizado': texto_normalizado[:100] + "..." if len(texto_normalizado) > 100 else texto_normalizado,
            'texto_lematizado': texto_lematizado[:100] + "..." if len(texto_lematizado) > 100 else texto_lematizado,
            'verbos_encontrados': list(verbos_encontrados) if verbos_encontrados else []
        }
    }
    
    print(f"\n🔍 Resultado da Análise:")
    print(f"   Categoria: {resultado['categoria'].upper()}")
    print(f"   Motivos: {', '.join(resultado['motivos'])}")
    
    if 'detalhes' in resultado and resultado['detalhes']:
        print(f"   Detalhes:")
        for chave, valor in resultado['detalhes'].items():
            if isinstance(valor, list):
                print(f"      • {chave}: {', '.join(str(v) for v in valor)}")
            else:
                print(f"      • {chave}: {valor}")
    
    # Verifica se está correto
    correto = resultado['categoria'] == caso['esperado']
    total_corretos += correto
    
    if correto:
        print(f"\n✅ CORRETO!")
    else:
        print(f"\n❌ ERRO! Esperado: {caso['esperado'].upper()}, Obtido: {resultado['categoria'].upper()}")
    
    resultados.append({
        'caso': i,
        'esperado': caso['esperado'],
        'obtido': resultado['categoria'],
        'correto': correto,
        'descricao': caso['descricao']
    })

# ============================================================================
# RELATÓRIO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("📊 RELATÓRIO FINAL DO TESTE DE FLUXO COMPLETO")
print("=" * 80)

acuracia = (total_corretos / total_casos) * 100

print(f"\n✅ Total de acertos: {total_corretos}/{total_casos}")
print(f"📈 Taxa de acurácia: {acuracia:.2f}%")

if total_corretos < total_casos:
    print(f"\n❌ Erros encontrados ({total_casos - total_corretos}):")
    for r in resultados:
        if not r['correto']:
            print(f"   • Caso {r['caso']}: {r['descricao']}")
            print(f"     Esperado: {r['esperado'].upper()}, Obtido: {r['obtido'].upper()}")

# Estatísticas do sistema
print("\n" + "=" * 80)
print("📊 ESTATÍSTICAS DO SISTEMA DE LEMATIZAÇÃO")
print("=" * 80)
stats = obter_estatisticas()
print(f"\n📚 Dicionário Estático:")
print(f"   • Conjugações: {stats['dicionario_estatico']['total_conjugacoes']}")
print(f"   • Verbos únicos: {stats['dicionario_estatico']['verbos_unicos_infinitivo']}")
print(f"   • Cobertura média: {stats['dicionario_estatico']['cobertura_media_por_verbo']:.1f} conjugações/verbo")

print(f"\n🧠 Dicionário Aprendido:")
print(f"   • Palavras aprendidas: {stats['dicionario_aprendido']['total_palavras_aprendidas']}")
print(f"   • Pendentes de salvar: {stats['dicionario_aprendido']['palavras_desde_ultimo_save']}")

print(f"\n⚡ Cache:")
print(f"   • Taxa de acerto: {stats['cache']['taxa_acerto_pct']:.1f}%")
print(f"   • Tamanho: {stats['cache']['tamanho_atual']}/{stats['cache']['tamanho_maximo']}")
print(f"   • Hits: {stats['cache']['hits']} | Misses: {stats['cache']['misses']}")

print(f"\n🤖 spaCy:")
print(f"   • Disponível: {'✅ Sim' if stats['spacy']['disponivel'] else '❌ Não'}")
print(f"   • Carregado: {'✅ Sim' if stats['spacy']['carregado'] else '❌ Não'}")

print(f"\n📊 TOTAL:")
print(f"   • Palavras conhecidas: {stats['total_palavras_conhecidas']}")
print(f"   • Verbos de integração: 46")

print("\n" + "=" * 80)

if acuracia == 100:
    print("🎉 PERFEITO! Sistema funcionando com 100% de acurácia!")
elif acuracia >= 90:
    print("✅ EXCELENTE! Sistema com alta confiabilidade!")
elif acuracia >= 80:
    print("✅ BOM! Sistema funcional, mas pode melhorar.")
else:
    print("⚠️  ATENÇÃO! Sistema precisa de ajustes.")

print("=" * 80)
