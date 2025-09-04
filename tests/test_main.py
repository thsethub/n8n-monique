import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from main import app, AnalisadorDeMensagem, PALAVRAS_CHAVE_DE_SISTEMA

# Cliente de teste para FastAPI
client = TestClient(app)

class TestAnalisadorDeMensagem:
    """Testes para a classe AnalisadorDeMensagem"""
    
    def test_inicializacao_com_payload_vazio(self):
        """Testa inicialização com payload None"""
        analisador = AnalisadorDeMensagem(None)
        assert analisador.payload_original == {}
        assert analisador.contexto == {}
    
    def test_inicializacao_com_payload_valido(self):
        """Testa inicialização com payload válido"""
        payload = {"message": "teste", "ctx": {"lang": "pt"}}
        analisador = AnalisadorDeMensagem(payload)
        assert analisador.payload_original == payload
        assert analisador.contexto == {"lang": "pt"}
    
    def test_extrair_mensagem_do_payload_sucesso(self):
        """Testa extração de mensagem válida"""
        payload = {"message": "  Olá mundo  "}
        analisador = AnalisadorDeMensagem(payload)
        mensagem = analisador._extrair_mensagem_do_payload()
        assert mensagem == "Olá mundo"
    
    def test_extrair_mensagem_do_payload_vazia(self):
        """Testa extração com mensagem vazia"""
        payload = {"message": ""}
        analisador = AnalisadorDeMensagem(payload)
        mensagem = analisador._extrair_mensagem_do_payload()
        assert mensagem == ""
    
    def test_extrair_mensagem_do_payload_sem_message(self):
        """Testa extração sem campo message"""
        payload = {}
        analisador = AnalisadorDeMensagem(payload)
        mensagem = analisador._extrair_mensagem_do_payload()
        assert mensagem == ""
    
    def test_extrair_mensagem_do_payload_nao_string(self):
        """Testa extração com message não sendo string"""
        payload = {"message": 123}
        analisador = AnalisadorDeMensagem(payload)
        mensagem = analisador._extrair_mensagem_do_payload()
        assert mensagem == "123"
    
    def test_normalizar_texto(self):
        """Testa normalização de texto"""
        analisador = AnalisadorDeMensagem({})
        
        # Teste com acentos e maiúsculas
        resultado = analisador._normalizar_texto("Olá MUNDO com Acentuação!")
        assert resultado == "ola mundo com acentuacao!"
        
        # Teste com caracteres especiais
        resultado = analisador._normalizar_texto("Ção, coração")
        assert resultado == "cao, coracao"
    
    def test_determinar_categoria_system(self):
        """Testa classificação como 'system'"""
        analisador = AnalisadorDeMensagem({})
        
        # Teste com palavra-chave de sistema
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            "Preciso acessar meu documento no drive",
            "preciso acessar meu documento no drive"
        )
        assert categoria == "system"
        assert len(motivos) == 1
        assert "drive" in motivos[0]
    
    def test_determinar_categoria_messages_pergunta_direta(self):
        """Testa classificação como 'messages' para pergunta direta"""
        analisador = AnalisadorDeMensagem({})
        
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            "Que dia é hoje?",
            "que dia e hoje?"
        )
        assert categoria == "messages"
        assert "Pergunta direta/fechada detectada." in motivos
    
    def test_determinar_categoria_user_complexa(self):
        """Testa classificação como 'user' para mensagem complexa"""
        analisador = AnalisadorDeMensagem({})
        
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            "Preciso criar um plano de estudos detalhado para meu curso de programação",
            "preciso criar um plano de estudos detalhado para meu curso de programacao"
        )
        assert categoria == "user"
        assert "Mensagem com necessidade de personalização/contexto." in motivos
    
    def test_determinar_categoria_messages_curta(self):
        """Testa classificação como 'messages' para mensagem curta"""
        analisador = AnalisadorDeMensagem({})
        
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            "Oi",
            "oi"
        )
        assert categoria == "messages"
        assert "Curta e objetiva; sem necessidade clara de contexto." in motivos
    
    def test_determinar_categoria_user_longa(self):
        """Testa classificação como 'user' para mensagem longa"""
        analisador = AnalisadorDeMensagem({})
        
        mensagem_longa = "Esta é uma mensagem muito longa que não tem palavras-chave específicas mas é longa o suficiente"
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            mensagem_longa,
            mensagem_longa.lower()
        )
        assert categoria == "user"
        assert "Mensagem requer elaboração moderada." in motivos
    
    def test_e_pergunta_direta_e_objetiva(self):
        """Testa detecção de pergunta direta"""
        analisador = AnalisadorDeMensagem({})
        
        # Pergunta curta com ?
        assert analisador._e_pergunta_direta_e_objetiva("Como vai?")
        
        # Pergunta factual
        assert analisador._e_pergunta_direta_e_objetiva("Capital de França")
        
        # Não é pergunta direta
        assert not analisador._e_pergunta_direta_e_objetiva("Olá, como vai tudo por aí? Estou bem curioso sobre como você está")
    
    def test_e_mensagem_complexa_ou_pessoal(self):
        """Testa detecção de mensagem complexa"""
        analisador = AnalisadorDeMensagem({})
        
        # Mensagem longa
        mensagem_longa = "A" * 200
        assert analisador._e_mensagem_complexa_ou_pessoal(mensagem_longa)
        
        # Referência pessoal
        assert analisador._e_mensagem_complexa_ou_pessoal("Meu problema é complexo")
        
        # Pedido de plano
        assert analisador._e_mensagem_complexa_ou_pessoal("Preciso de um plano")
        
        # Múltiplas frases
        assert analisador._e_mensagem_complexa_ou_pessoal("Primeira frase. Segunda frase!")
        
        # Mensagem simples
        assert not analisador._e_mensagem_complexa_ou_pessoal("Oi")
    
    def test_determinar_idioma_portugues(self):
        """Testa detecção de idioma português"""
        analisador = AnalisadorDeMensagem({})
        
        assert analisador._determinar_idioma("Olá, como está?") == "pt"
        assert analisador._determinar_idioma("reunião hoje") == "pt"
        assert analisador._determinar_idioma("ação") == "pt"
    
    def test_determinar_idioma_ingles(self):
        """Testa detecção de idioma inglês"""
        analisador = AnalisadorDeMensagem({})
        
        assert analisador._determinar_idioma("Hello, how are you?") == "en"
        assert analisador._determinar_idioma("meeting today") == "en"
    
    def test_determinar_idioma_ambiguo(self):
        """Testa detecção com texto ambíguo (padrão português)"""
        analisador = AnalisadorDeMensagem({})
        
        assert analisador._determinar_idioma("123 test") == "pt"
    
    def test_calcular_parametros_da_ia_messages(self):
        """Testa parâmetros para categoria messages"""
        analisador = AnalisadorDeMensagem({"ctx": {"temperature": 0.5}})
        
        params = analisador._calcular_parametros_da_ia("messages")
        assert params["temperature"] == 0.2  # min(0.5, 0.2)
        assert params["max_tokens"] == 400
    
    def test_calcular_parametros_da_ia_system(self):
        """Testa parâmetros para categoria system"""
        analisador = AnalisadorDeMensagem({"ctx": {"temperature": 0.8}})
        
        params = analisador._calcular_parametros_da_ia("system")
        assert params["temperature"] == 0.3  # min(0.8, 0.3)
        assert params["max_tokens"] == 900
    
    def test_calcular_parametros_da_ia_user(self):
        """Testa parâmetros para categoria user"""
        analisador = AnalisadorDeMensagem({"ctx": {"temperature": 0.1}})
        
        params = analisador._calcular_parametros_da_ia("user")
        assert params["temperature"] == 0.3  # min(max(0.1, 0.3), 0.6)
        assert params["max_tokens"] == 900
    
    def test_calcular_parametros_da_ia_sem_temperature(self):
        """Testa parâmetros sem temperature no contexto"""
        analisador = AnalisadorDeMensagem({})
        
        params = analisador._calcular_parametros_da_ia("messages")
        assert params["temperature"] == 0.2  # min(0.3, 0.2) - 0.3 é o padrão
    
    def test_obter_historico_da_conversa_valido(self):
        """Testa obtenção de histórico válido"""
        payload = {
            "history": [
                {"role": "user", "content": "Oi"},
                {"role": "assistant", "content": "Olá!"},
                {"role": "user", "content": "Como vai?"}
            ]
        }
        analisador = AnalisadorDeMensagem(payload)
        
        historico = analisador._obter_historico_da_conversa()
        assert len(historico) == 3
        assert historico[0]["role"] == "user"
        assert historico[0]["content"] == "Oi"
    
    def test_obter_historico_da_conversa_invalido(self):
        """Testa obtenção de histórico inválido"""
        payload = {"history": "não é uma lista"}
        analisador = AnalisadorDeMensagem(payload)
        
        historico = analisador._obter_historico_da_conversa()
        assert historico == []
    
    def test_obter_historico_da_conversa_limitado(self):
        """Testa limitação do histórico a 6 mensagens"""
        payload = {
            "history": [{"role": "user", "content": f"Mensagem {i}"} for i in range(10)]
        }
        analisador = AnalisadorDeMensagem(payload)
        
        historico = analisador._obter_historico_da_conversa()
        assert len(historico) == 6
        assert historico[0]["content"] == "Mensagem 4"  # Últimas 6
    
    def test_obter_historico_da_conversa_mensagens_invalidas(self):
        """Testa filtro de mensagens inválidas no histórico"""
        payload = {
            "history": [
                {"role": "user", "content": "Válida"},
                {"role": "user"},  # Sem content
                {"content": "Sem role"},  # Sem role
                "string inválida",  # Não é dict
                {"role": "assistant", "content": "Outra válida"}
            ]
        }
        analisador = AnalisadorDeMensagem(payload)
        
        historico = analisador._obter_historico_da_conversa()
        assert len(historico) == 2
        assert historico[0]["content"] == "Válida"
        assert historico[1]["content"] == "Outra válida"
    
    def test_criar_prompts_de_sistema_portugues(self):
        """Testa criação de prompts em português"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("messages", "pt", "teste")
        
        assert len(prompts) >= 2
        assert "português do Brasil" in prompts[0]["content"]
        assert prompts[0]["role"] == "system"
        assert integracoes == []
    
    def test_criar_prompts_de_sistema_ingles(self):
        """Testa criação de prompts em inglês"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("messages", "en", "test")
        
        assert "Reply in English" in prompts[0]["content"]
        assert integracoes == []
    
    def test_criar_prompts_de_sistema_system_google(self):
        """Testa prompts para categoria system com integração Google"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("system", "pt", "google drive planilha")
        
        assert "google" in integracoes
        assert "MODO INTEGRAÇÃO ATIVO" in prompts[1]["content"]
        assert "google" in prompts[1]["content"]
    
    def test_criar_prompts_de_sistema_system_apple(self):
        """Testa prompts para categoria system com integração Apple"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("system", "pt", "apple icloud notes")
        
        assert "apple" in integracoes
    
    def test_criar_prompts_de_sistema_system_boleto(self):
        """Testa prompts para categoria system com integração boleto"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("system", "pt", "boleto fatura")
        
        assert "boleto" in integracoes
    
    def test_criar_prompts_de_sistema_user(self):
        """Testa prompts para categoria user"""
        analisador = AnalisadorDeMensagem({})
        
        prompts, integracoes = analisador._criar_prompts_de_sistema("user", "pt", "teste")
        
        assert len(prompts) == 3
        assert "complexa" in prompts[2]["content"]
    
    def test_construir_payload_de_erro_para_entrada_vazia(self):
        """Testa construção de payload de erro"""
        payload_original = {"ctx": {"model": "gpt-4"}}
        analisador = AnalisadorDeMensagem(payload_original)
        
        resultado = analisador._construir_payload_de_erro_para_entrada_vazia()
        
        assert resultado["error"] == "EMPTY_INPUT"
        assert "ctx" in resultado
        assert "openaiPayload" in resultado
        assert "Não recebi sua mensagem" in resultado["openaiPayload"]["messages"][0]["content"]
    
    def test_construir_payload_para_ia_completo(self):
        """Testa construção completa do payload para IA"""
        payload = {
            "ctx": {"lang": "pt", "model": "gpt-4", "temperature": 0.5},
            "history": [{"role": "user", "content": "Oi"}]
        }
        analisador = AnalisadorDeMensagem(payload)
        
        payload_ia, integracoes = analisador._construir_payload_para_ia(
            "messages", "Que horas são?", "que horas sao?"
        )
        
        assert payload_ia["model"] == "gpt-4"
        assert len(payload_ia["messages"]) >= 3  # prompts + histórico + mensagem atual
        assert payload_ia["messages"][-1]["content"] == "Que horas são?"
        assert "temperature" in payload_ia
        assert "max_tokens" in payload_ia
    
    def test_processar_mensagem_completo(self):
        """Testa processamento completo de mensagem"""
        payload = {
            "message": "Olá, como vai?",
            "ctx": {"lang": "pt"}
        }
        analisador = AnalisadorDeMensagem(payload)
        
        resultado = analisador.processar_mensagem()
        
        assert "mensagem_completa" in resultado
        assert "texto_normalizado" in resultado
        assert "openaiPayload" in resultado
        assert "classification" in resultado
        assert resultado["mensagem_completa"] == "Olá, como vai?"
        assert resultado["texto_normalizado"] == "ola, como vai?"
    
    def test_processar_mensagem_vazia(self):
        """Testa processamento de mensagem vazia"""
        payload = {"message": ""}
        analisador = AnalisadorDeMensagem(payload)
        
        resultado = analisador.processar_mensagem()
        
        assert resultado["error"] == "EMPTY_INPUT"


class TestEndpointAPI:
    """Testes para os endpoints da API"""
    
    def test_endpoint_preprocess_sucesso(self):
        """Testa endpoint com payload válido"""
        payload = {
            "message": "Olá, como está?",
            "ctx": {"lang": "pt"}
        }
        
        response = client.post("/preprocess", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mensagem_completa" in data
        assert "classification" in data
        assert data["mensagem_completa"] == "Olá, como está?"
    
    # def test_endpoint_preprocess_payload_vazio(self):
    #     """Testa endpoint com payload vazio"""
    #     response = client.post("/preprocess", json={})
        
    #     # Mesmo com payload vazio, deve processar (mensagem vazia)
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "error" in data
    #     assert data["error"] == "EMPTY_INPUT"
    
    def test_endpoint_preprocess_sem_payload(self):
        """Testa endpoint sem payload"""
        response = client.post("/preprocess")
        
        # FastAPI retorna 422 para corpo de requisição inválido
        assert response.status_code == 422
    
    def test_endpoint_preprocess_system_message(self):
        """Testa endpoint com mensagem de sistema"""
        payload = {
            "message": "Preciso acessar meu documento no Google Drive",
            "ctx": {"lang": "pt"}
        }
        
        response = client.post("/preprocess", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["bucket"] == "system"
        assert "google" in data["classification"]["integrations"]


class TestConstantes:
    """Testes para constantes do módulo"""
    
    def test_palavras_chave_de_sistema_e_set(self):
        """Testa se PALAVRAS_CHAVE_DE_SISTEMA é um Set"""
        assert isinstance(PALAVRAS_CHAVE_DE_SISTEMA, set)
        assert len(PALAVRAS_CHAVE_DE_SISTEMA) > 0
    
    def test_palavras_chave_contem_esperadas(self):
        """Testa se contém palavras-chave esperadas"""
        palavras_esperadas = ["documento", "google", "drive", "calendario", "boleto"]
        for palavra in palavras_esperadas:
            assert palavra in PALAVRAS_CHAVE_DE_SISTEMA


class TestCasosEspeciais:
    """Testes para casos especiais e edge cases"""
    
    def test_mensagem_apenas_espacos(self):
        """Testa mensagem com apenas espaços"""
        analisador = AnalisadorDeMensagem({"message": "   "})
        resultado = analisador.processar_mensagem()
        assert resultado["error"] == "EMPTY_INPUT"
    
    def test_mensagem_com_caracteres_especiais(self):
        """Testa mensagem com caracteres especiais"""
        payload = {"message": "Olá! @#$%^&*()"}
        analisador = AnalisadorDeMensagem(payload)
        resultado = analisador.processar_mensagem()
        
        assert "mensagem_completa" in resultado
        assert resultado["mensagem_completa"] == "Olá! @#$%^&*()"
    
    def test_contexto_com_model_customizado(self):
        """Testa contexto com modelo customizado"""
        payload = {
            "message": "Teste",
            "ctx": {"model": "gpt-3.5-turbo"}
        }
        analisador = AnalisadorDeMensagem(payload)
        resultado = analisador.processar_mensagem()
        
        assert resultado["openaiPayload"]["model"] == "gpt-3.5-turbo"
    
    def test_contexto_sem_model(self):
        """Testa contexto sem modelo (usa padrão)"""
        payload = {"message": "Teste"}
        analisador = AnalisadorDeMensagem(payload)
        resultado = analisador.processar_mensagem()
        
        assert resultado["openaiPayload"]["model"] == "gpt-4.1-mini"
    
    def test_multiplas_palavras_chave_sistema(self):
        """Testa detecção de múltiplas palavras-chave de sistema"""
        analisador = AnalisadorDeMensagem({})
        categoria, motivos = analisador._determinar_categoria_da_mensagem(
            "Preciso acessar documento no drive e calendario",
            "preciso acessar documento no drive e calendario"
        )
        
        assert categoria == "system"
        # Deve detectar pelo menos documento, drive e calendario
        assert any("documento" in motivo for motivo in motivos)


if __name__ == "__main__":
    pytest.main(["-v", "--cov=main", "--cov-report=html", "--cov-report=term"])