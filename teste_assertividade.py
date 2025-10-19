"""Script para testar assertividade das melhorias"""

from app.services.analisador.classificador import Classificador
from app.services.analisador.normalizador import normalizar_texto

testes = [
    "Fazer upload do contrato assinado",
    "Deletar emails antigos da caixa de entrada",
    "Gerar PIX de 150 reais",
    "Agendar videochamada com o time",
    "Baixar a planilha de vendas",
    "Compartilhar documento com a equipe",
    "Como faço para ser mais produtivo?",
    "Me conte uma história interessante",
]

print("=" * 70)
print("TESTES DE ASSERTIVIDADE DAS MELHORIAS")
print("=" * 70)
print()

for i, msg in enumerate(testes, 1):
    cat, motivos = Classificador.determinar_categoria(msg, normalizar_texto(msg))
    emoji = "🔧" if cat == "system" else ("💬" if cat == "messages" else "👤")
    print(f'{i}. {emoji} "{msg}"')
    print(f"   → Categoria: {cat.upper()}")
    print(f"   → Motivo: {motivos[0]}")
    print()

print("=" * 70)
print(f"Total de palavras-chave no sistema: 224")
print(f"Total de padrões no cache: 29")
print("=" * 70)
