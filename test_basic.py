"""
Testes básicos para validar funcionalidade do microsserviço de pré-processamento.

Execute com: python test_basic.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuração
BASE_URL = "http://localhost:8181"
ENDPOINT = f"{BASE_URL}/preprocess"

def test_api_request(payload: Dict[str, Any], expected_bucket: str = None) -> Dict[str, Any]:
    """
    Faz uma requisição para a API e valida a resposta.
    
    Args:
        payload: Dados para enviar
        expected_bucket: Bucket esperado (opcional)
        
    Returns:
        Resposta da API
    """
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # Validações básicas
        assert "classification" in result, "Resposta deve conter 'classification'"
        assert "bucket" in result["classification"], "Classification deve conter 'bucket'"
        assert "openaiPayload" in result, "Resposta deve conter 'openaiPayload'"
        
        # Valida bucket esperado se fornecido
        if expected_bucket:
            actual_bucket = result["classification"]["bucket"]
            assert actual_bucket == expected_bucket, f"Esperado bucket '{expected_bucket}', obtido '{actual_bucket}'"
        
        print(f"✅ Teste passou - Bucket: {result['classification']['bucket']}")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        raise
    except AssertionError as e:
        print(f"❌ Erro de validação: {e}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        raise

def test_empty_payload():
    """Testa payload vazio - deve retornar erro 400"""
    print("\n🧪 Testando payload vazio...")
    
    try:
        response = requests.post(ENDPOINT, json={}, timeout=10)
        assert response.status_code == 400, f"Esperado status 400, obtido {response.status_code}"
        print("✅ Payload vazio retornou erro 400 como esperado")
    except Exception as e:
        print(f"❌ Erro ao testar payload vazio: {e}")
        raise

def test_message_classification():
    """Testa classificação de diferentes tipos de mensagem"""
    
    test_cases = [
        # Perguntas diretas -> messages
        {
            "name": "Pergunta direta simples",
            "payload": {"message": "Qual é a capital do Brasil?"},
            "expected_bucket": "messages"
        },
        {
            "name": "Pergunta factual",
            "payload": {"message": "Quanto é 2 + 2?"},
            "expected_bucket": "messages"
        },
        
        # Integrações -> system
        {
            "name": "Integração Google Calendar",
            "payload": {"message": "Agende uma reunião no google calendar"},
            "expected_bucket": "system"
        },
        {
            "name": "Integração Google Drive",
            "payload": {"message": "Crie um documento no drive"},
            "expected_bucket": "system"
        },
        
        # Mensagens complexas -> user
        {
            "name": "Pedido de plano",
            "payload": {"message": "Preciso de um plano de estudos personalizado para aprender Python"},
            "expected_bucket": "user"
        },
        {
            "name": "Mensagem com referência pessoal",
            "payload": {"message": "Preciso organizar melhor a minha rotina de trabalho para ser mais produtivo"},
            "expected_bucket": "user"
        },
        
        # Teste com contexto
        {
            "name": "Com contexto português",
            "payload": {"message": "How are you?", "ctx": {"lang": "pt"}},
            "expected_bucket": "messages"
        }
    ]
    
    print("\n🧪 Testando classificação de mensagens...")
    
    for test_case in test_cases:
        print(f"\nTestando: {test_case['name']}")
        print(f"Mensagem: {test_case['payload']['message']}")
        
        result = test_api_request(test_case["payload"], test_case["expected_bucket"])
        
        # Mostra motivos da classificação
        reasons = result["classification"].get("reasons", [])
        if reasons:
            print(f"   Motivos: {', '.join(reasons)}")
        
        # Mostra integrações detectadas
        integrations = result["classification"].get("integrations", [])
        if integrations:
            print(f"   Integrações: {', '.join(integrations)}")

def test_integration_detection():
    """Testa detecção específica de integrações"""
    
    integration_tests = [
        {
            "message": "Organize my files in google drive",
            "expected_integrations": ["google"]
        },
        {
            "message": "Save this to my icloud notes",
            "expected_integrations": ["apple"]
        },
        {
            "message": "Pay this boleto",
            "expected_integrations": ["boleto"]
        },
        {
            "message": "Just a simple question",
            "expected_integrations": []
        }
    ]
    
    print("\n🧪 Testando detecção de integrações...")
    
    for test in integration_tests:
        print(f"\nTestando: {test['message']}")
        result = test_api_request({"message": test["message"]})
        
        actual_integrations = result["classification"]["integrations"]
        expected_integrations = test["expected_integrations"]
        
        assert actual_integrations == expected_integrations, \
            f"Esperado {expected_integrations}, obtido {actual_integrations}"
        
        print(f"   Integrações detectadas: {actual_integrations}")

def test_language_detection():
    """Testa detecção automática de idioma"""
    
    language_tests = [
        {"message": "Como está o tempo hoje?", "expected_lang": "pt"},
        {"message": "What's the weather like?", "expected_lang": "en"},
        {"message": "Reunião às 15h", "expected_lang": "pt"},
        {"message": "Meeting at 3pm", "expected_lang": "en"}
    ]
    
    print("\n🧪 Testando detecção de idioma...")
    
    for test in language_tests:
        print(f"\nTestando: {test['message']}")
        result = test_api_request({"message": test["message"]})
        
        # Verifica se o prompt de idioma está correto
        messages = result["openaiPayload"]["messages"]
        language_prompt = messages[0]["content"]
        
        if test["expected_lang"] == "pt":
            assert "português" in language_prompt.lower(), f"Esperado prompt em português, obtido: {language_prompt}"
        else:
            assert "english" in language_prompt.lower(), f"Esperado prompt em inglês, obtido: {language_prompt}"
        
        print(f"   Idioma detectado corretamente: {test['expected_lang']}")

def test_parameter_calculation():
    """Testa cálculo de parâmetros dinâmicos"""
    
    print("\n🧪 Testando cálculo de parâmetros...")
    
    # Teste messages (baixa temperature)
    result = test_api_request({"message": "Qual a capital do Brasil?"})
    temp = result["openaiPayload"]["temperature"]
    max_tokens = result["openaiPayload"]["max_tokens"]
    assert temp <= 0.2, f"Temperature para 'messages' deve ser ≤ 0.2, obtido {temp}"
    assert max_tokens == 400, f"Max tokens para 'messages' deve ser 400, obtido {max_tokens}"
    print(f"   Messages: temp={temp}, tokens={max_tokens} ✅")
    
    # Teste system (temperature moderada)
    result = test_api_request({"message": "Agende reunião no google calendar"})
    temp = result["openaiPayload"]["temperature"]
    max_tokens = result["openaiPayload"]["max_tokens"]
    assert temp <= 0.3, f"Temperature para 'system' deve ser ≤ 0.3, obtido {temp}"
    assert max_tokens == 900, f"Max tokens para 'system' deve ser 900, obtido {max_tokens}"
    print(f"   System: temp={temp}, tokens={max_tokens} ✅")
    
    # Teste user (temperature mais alta)
    result = test_api_request({"message": "Preciso de um plano detalhado para organizar minha vida"})
    temp = result["openaiPayload"]["temperature"]
    max_tokens = result["openaiPayload"]["max_tokens"]
    assert 0.3 <= temp <= 0.6, f"Temperature para 'user' deve estar entre 0.3-0.6, obtido {temp}"
    assert max_tokens == 900, f"Max tokens para 'user' deve ser 900, obtido {max_tokens}"
    print(f"   User: temp={temp}, tokens={max_tokens} ✅")

def test_history_handling():
    """Testa tratamento do histórico de conversa"""
    
    print("\n🧪 Testando histórico de conversa...")
    
    history = [
        {"role": "user", "content": "Como aprender Python?"},
        {"role": "assistant", "content": "Comece com o básico..."},
        {"role": "user", "content": "Que recursos usar?"}
    ]
    
    result = test_api_request({
        "message": "E quanto tempo leva?",
        "history": history
    })
    
    messages = result["openaiPayload"]["messages"]
    
    # Deve ter: prompts de sistema + histórico + mensagem atual
    assert len(messages) >= 4, f"Deve ter pelo menos 4 mensagens, obtido {len(messages)}"
    
    # Últimas mensagens devem incluir o histórico
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    assert len(user_messages) >= 2, f"Deve ter pelo menos 2 mensagens de usuário, obtido {len(user_messages)}"
    
    print(f"   Histórico preservado: {len(user_messages)} mensagens de usuário ✅")

def run_all_tests():
    """Executa todos os testes"""
    
    print("🚀 Iniciando testes do microsserviço de pré-processamento...")
    print(f"URL base: {BASE_URL}")
    
    try:
        # Verifica se o servidor está rodando
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print("✅ Servidor está respondendo")
    except requests.exceptions.RequestException:
        print("❌ Servidor não está acessível. Certifique-se que está rodando na porta 8181")
        return False
    
    try:
        test_empty_payload()
        test_message_classification()
        test_integration_detection()
        test_language_detection()
        test_parameter_calculation()
        test_history_handling()
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n💥 Falha nos testes: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)