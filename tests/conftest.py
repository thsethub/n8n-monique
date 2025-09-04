import pytest
import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Se o main.py estiver em um diretório pai, descomente a linha abaixo:
# sys.path.insert(0, str(project_root.parent))

@pytest.fixture
def payload_basico():
    """Fixture com payload básico para testes"""
    return {
        "message": "Olá, como vai?",
        "ctx": {"lang": "pt", "model": "gpt-4"}
    }

@pytest.fixture
def payload_sistema():
    """Fixture com payload que deve ser classificado como system"""
    return {
        "message": "Preciso acessar meu documento no Google Drive",
        "ctx": {"lang": "pt"}
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
            {"role": "assistant", "content": "Olá! Como posso ajudar?"}
        ]
    }