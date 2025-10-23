"""
Teste de detecção de perguntas com spaCy (sem "?")
"""

from app.services.analisador.classificador import Classificador
from app.services.analisador.normalizador import normalizar_texto

# Casos de teste: perguntas SEM "?"
casos_teste = [
    "Me explica como funciona o Git",
    "Quero entender os conceitos de programação orientada a objetos",
    "Pode me dizer qual a diferença entre Git e GitHub",
    "Gostaria de saber como funciona a sincronização",
    "Me fale sobre Python",
    "Como faço para criar um branch",
    "Quero aprender sobre APIs REST"
]

print("=" * 80)
print("TESTE DE DETECÇÃO DE PERGUNTAS COM spaCy (sem '?')")
print("=" * 80)

acertos = 0
total = len(casos_teste)

for i, msg in enumerate(casos_teste, 1):
    norm = normalizar_texto(msg)
    cat, mot = Classificador.determinar_categoria(msg, norm)
    
    esperado = "messages"
    status = "✅" if cat == esperado else "❌"
    if cat == esperado:
        acertos += 1
    
    print(f"\n{status} Caso {i}: \"{msg}\"")
    print(f"   Categoria: {cat} (esperado: {esperado})")
    print(f"   Motivos: {mot}")

print("\n" + "=" * 80)
print(f"RESULTADO: {acertos}/{total} acertos ({acertos/total*100:.1f}%)")
print("=" * 80)
