"""
Verifica quais verbos estão disponíveis no lematizador
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.utils.lematizador import VERBOS_INFINITIVOS, MAPEAMENTO_VERBOS

print("\n" + "="*70)
print("📊 VERBOS DISPONÍVEIS NO LEMATIZADOR")
print("="*70)

print(f"\n✅ Total de verbos infinitivos: {len(VERBOS_INFINITIVOS)}")
print(f"✅ Total de conjugações mapeadas: {len(MAPEAMENTO_VERBOS)}")

print("\n📝 Lista de verbos (infinitivo):")
print("="*70)

verbos_ordenados = sorted(VERBOS_INFINITIVOS)
for i, verbo in enumerate(verbos_ordenados, 1):
    # Conta quantas conjugações tem cada verbo
    conjugacoes = [k for k, v in MAPEAMENTO_VERBOS.items() if v == verbo]
    print(f"{i:2d}. {verbo:20s} ({len(conjugacoes)} conjugações)")

print("\n" + "="*70)

# Verifica se os verbos que o classificador precisa estão presentes
verbos_necessarios = {
    "enviar", "mandar", "disparar", "encaminhar",
    "agendar", "marcar", "reservar",
    "criar", "gerar", "produzir",
    "compartilhar",
    "fazer upload", "subir",
    "responder",
    "editar", "modificar",
    "fazer download", "baixar",
    "sincronizar",
    "fazer",
    "excluir", "deletar", "remover",
    "cancelar", "reagendar",
}

faltando = verbos_necessarios - VERBOS_INFINITIVOS

if faltando:
    print("⚠️  VERBOS FALTANDO NO LEMATIZADOR:")
    for verbo in sorted(faltando):
        print(f"   ❌ {verbo}")
else:
    print("✅ TODOS OS VERBOS NECESSÁRIOS ESTÃO PRESENTES!")

print("="*70 + "\n")
