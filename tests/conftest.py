import pytest
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao path (onde está o diretório 'app')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def payload_basico():
    """Fixture com payload básico para testes"""
    return {"message": "Olá, como vai?", "ctx": {"lang": "pt", "model": "gpt-4"}}


@pytest.fixture
def payload_sistema():
    """Fixture com payload que deve ser classificado como system"""
    return {
        "message": "Preciso acessar meu documento no Google Drive",
        "ctx": {"lang": "pt"},
    }


@pytest.fixture
def payload_vazio():
    """Fixture com payload vazio"""
    return {"message": ""}


@pytest.fixture
def payload_complexo():
    """Fixture com payload de mensagem complexa"""
    return {
        "message": "Preciso criar um plano de estudos detalhado para meu curso. Tenho algumas dúvidas sobre como organizar o tempo.",
        "ctx": {"lang": "pt"},
        "history": [
            {"role": "user", "content": "Oi"},
            {"role": "assistant", "content": "Olá! Como posso ajudar?"},
        ],
    }
