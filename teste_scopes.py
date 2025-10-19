"""Script de teste para validar os scopes duplos"""

from app.services.analisador.detector_scopes import DetectorDeScopes

print("=" * 70)
print("TESTE DE SCOPES - SHEETS E DOCS DEVEM RETORNAR 2 URLS")
print("=" * 70)
print()

testes = [
    ("criar planilha", 2, "SHEETS"),
    ("abrir planilha de vendas", 2, "SHEETS"),
    ("editar tabela do projeto", 2, "SHEETS"),
    ("criar documento", 2, "DOCS"),
    ("abrir documento importante", 2, "DOCS"),
    ("enviar email", 1, "GMAIL"),
    ("agendar reuniao", 1, "CALENDAR"),
    ("compartilhar arquivo", 1, "DRIVE"),
]

for mensagem, esperado, tipo in testes:
    scopes = DetectorDeScopes.detectar_scopes(mensagem)
    status = "✅" if len(scopes) == esperado else "❌"

    print(f'{status} [{tipo}] "{mensagem}"')
    print(f"   Esperado: {esperado} scope(s)")
    print(f"   Retornado: {len(scopes)} scope(s)")
    for scope in scopes:
        print(f"   - {scope}")
    print()

print("=" * 70)
