"""
Testes completos para o analisador de mensagens refatorado.
Usa as fixtures do conftest.py e testa tanto módulos quanto endpoints.
"""

from fastapi.testclient import TestClient

# O conftest.py adiciona o diretório raiz ao sys.path
from app.main import app  # type: ignore
from app.services.analisador.normalizador import normalizar_texto  # type: ignore
from app.services.analisador.classificador import Classificador  # type: ignore
from app.services.analisador.detector_scopes import DetectorDeScopes  # type: ignore
from app.services.analisador.constantes import PALAVRAS_CHAVE_DE_SISTEMA  # type: ignore

client = TestClient(app)


# ===========================================================================
# TESTES DE MÓDULOS INDIVIDUAIS
# ===========================================================================


class TestNormalizador:
    """Testes para normalização de texto"""

    def test_normalizar_remove_acentos(self):
        assert normalizar_texto("Olá Mundo") == "ola mundo"
        assert normalizar_texto("Você está aqui?") == "voce esta aqui?"

    def test_normalizar_converte_minusculas(self):
        assert normalizar_texto("TESTE") == "teste"
        assert normalizar_texto("CaMeLcAsE") == "camelcase"

    def test_normalizar_texto_vazio(self):
        assert normalizar_texto("") == ""


class TestClassificador:
    """Testes para classificação de mensagens"""

    def test_classifica_como_system(self):
        categoria, motivos = Classificador.determinar_categoria(
            "Enviar email para joão", "enviar email para joao"
        )
        assert categoria == "system"
        assert len(motivos) > 0

    def test_classifica_como_messages(self):
        categoria, _ = Classificador.determinar_categoria(
            "Que dia é hoje?", "que dia e hoje"
        )
        assert categoria == "messages"

    def test_classifica_como_user_mensagem_longa(self):
        mensagem = (
            "Gostaria muito de aprender mais sobre inteligência artificial. "
            "Você poderia me ajudar a entender melhor os conceitos fundamentais "
            "e como posso aplicar isso na minha vida profissional?"
        )
        categoria, _ = Classificador.determinar_categoria(
            mensagem, normalizar_texto(mensagem)
        )
        assert categoria == "user"


class TestDetectorDeScopes:
    """Testes para detecção de scopes do Google"""

    def test_detecta_gmail_scope(self):
        scopes = DetectorDeScopes.detectar_scopes("enviar email")
        assert "mail.google.com" in str(scopes)

    def test_detecta_calendar_scope(self):
        scopes = DetectorDeScopes.detectar_scopes("agendar reuniao")
        assert "calendar" in str(scopes)

    def test_sem_scopes(self):
        scopes = DetectorDeScopes.detectar_scopes("oi tudo bem")
        assert scopes == []


class TestConstantes:
    """Testes para constantes"""

    def test_palavras_chave_contem_esperadas(self):
        assert "email" in PALAVRAS_CHAVE_DE_SISTEMA
        assert "drive" in PALAVRAS_CHAVE_DE_SISTEMA


# ===========================================================================
# TESTES DE ENDPOINTS DA API
# ===========================================================================


class TestAPIEndpoints:
    """Testes para endpoints FastAPI"""

    def test_health_check(self):
        """Deve responder ao health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_metrics_endpoint(self):
        """Deve retornar métricas do sistema"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        # Métricas reais retornadas pela API
        assert "cache_hits" in data or "total_requests" in data

    def test_webhook_endpoint_basico(self):
        """Deve processar webhook com mensagem básica"""
        payload = {"from": "5511999999999", "message": "Olá, como vai?"}
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        assert "bucket" in data["classification"]
        assert data["classification"]["bucket"] in ["system", "messages", "user"]

    def test_webhook_endpoint_sistema(self):
        """Deve processar webhook com mensagem de sistema"""
        payload = {"from": "5511999999999", "message": "enviar email"}
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["bucket"] == "system"
        assert len(data["classification"]["scope"]) > 0

    def test_preprocess_endpoint(self, payload_basico):
        """Deve processar endpoint /preprocess"""
        response = client.post("/preprocess", json=payload_basico)
        assert response.status_code == 200
        data = response.json()
        # O endpoint /preprocess retorna formato diferente
        assert "categoria" in data or "classification" in data

    def test_preprocess_com_sistema(self, payload_sistema):
        """Deve processar mensagem de sistema em /preprocess"""
        response = client.post("/preprocess", json=payload_sistema)
        assert response.status_code == 200
        data = response.json()
        # Aceita ambos os formatos
        categoria = data.get("categoria") or data.get("classification", {}).get(
            "bucket"
        )
        assert categoria == "system"

    def test_preprocess_com_vazio(self, payload_vazio):
        """Deve lidar com payload vazio"""
        response = client.post("/preprocess", json=payload_vazio)
        # Pode retornar 200 (processa) ou 400 (rejeita)
        assert response.status_code in [200, 400]


# ===========================================================================
# TESTES DE INTEGRAÇÃO (sem async)
# ===========================================================================


class TestIntegracao:
    """Testes de integração end-to-end"""

    def test_fluxo_webhook_completo(self):
        """Testa fluxo completo de webhook"""
        payload = {
            "from": "5511999999999",
            "message": "Agendar reunião com o time amanhã",
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "classification" in data
        assert data["classification"]["bucket"] == "system"
        assert "calendar" in str(data["classification"]["scope"])

    def test_fluxo_preprocess_basico(self, payload_basico):
        """Testa fluxo completo de preprocessamento"""
        response = client.post("/preprocess", json=payload_basico)
        assert response.status_code == 200

        data = response.json()
        assert "categoria" in data or "classification" in data

    def test_multiplas_requisicoes(self):
        """Testa múltiplas requisições sequenciais"""
        payloads = [
            {"from": "5511111111111", "message": "oi"},
            {"from": "5511111111111", "message": "enviar email"},
            {"from": "5511111111111", "message": "agendar reuniao"},
        ]

        for payload in payloads:
            response = client.post("/webhook", json=payload)
            assert response.status_code == 200
