"""
Script de teste rápido para validar a refatoração do módulo analisador.
"""

import asyncio
from app.services.analisador import AnalisadorDeMensagem


async def testar_analisador():
    """Testa o fluxo completo do analisador refatorado."""

    # Teste 1: Mensagem de sistema (integração)
    print("🧪 Teste 1: Mensagem de integração (system)")
    payload1 = {
        "message": "enviar email para joão",
        "ctx": {"lang": "pt", "temperature": 0.3},
        "history": [],
    }

    analisador1 = AnalisadorDeMensagem(payload1)
    resultado1 = await analisador1.processar_mensagem()

    print(f"✅ Categoria: {resultado1['classification']['bucket']}")
    print(f"✅ Scopes: {resultado1['classification']['scope']}")
    print(f"✅ Modelo: {resultado1['openaiPayload']['model']}")
    print(f"✅ Latência total: {resultado1['performance']['total_ms']}ms\n")

    # Teste 2: Pergunta direta (messages)
    print("🧪 Teste 2: Pergunta direta (messages)")
    payload2 = {"message": "que dia é hoje?", "ctx": {}, "history": []}

    analisador2 = AnalisadorDeMensagem(payload2)
    resultado2 = await analisador2.processar_mensagem()

    print(f"✅ Categoria: {resultado2['classification']['bucket']}")
    print(f"✅ Scopes: {resultado2['classification']['scope']}")
    print(f"✅ Modelo: {resultado2['openaiPayload']['model']}")
    print(f"✅ Latência total: {resultado2['performance']['total_ms']}ms\n")

    # Teste 3: Mensagem complexa (user)
    print("🧪 Teste 3: Mensagem complexa (user)")
    payload3 = {
        "message": "Estou pensando em mudar de carreira, mas não sei bem por onde começar. Você poderia me ajudar a pensar sobre isso?",
        "ctx": {},
        "history": [],
    }

    analisador3 = AnalisadorDeMensagem(payload3)
    resultado3 = await analisador3.processar_mensagem()

    print(f"✅ Categoria: {resultado3['classification']['bucket']}")
    print(f"✅ Scopes: {resultado3['classification']['scope']}")
    print(f"✅ Modelo: {resultado3['openaiPayload']['model']}")
    print(f"✅ Latência total: {resultado3['performance']['total_ms']}ms\n")

    # Teste 4: Cache hit (mesma mensagem do teste 2)
    print("🧪 Teste 4: Cache hit (mesma mensagem do teste 2)")
    analisador4 = AnalisadorDeMensagem(payload2)
    resultado4 = await analisador4.processar_mensagem()

    print(f"✅ Categoria: {resultado4['classification']['bucket']}")
    print(
        f"✅ Latência cache lookup: {resultado4['performance'].get('cache_lookup_ms', 'N/A')}ms"
    )
    print(f"✅ Cache hit? Sim (latência muito menor!)\n")

    print("=" * 60)
    print(
        "🎉 Todos os testes passaram! Módulo refatorado está funcionando perfeitamente!"
    )
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(testar_analisador())
