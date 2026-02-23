"""
Test Suite - Módulo de Log de Contatos (Fase 3)

Tests all contact log endpoints for SENAI CIMATEC's enrollment system.
Covers: CRUD operations, statistics, returns management, and role-based access control.
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@senai.br"
ADMIN_PASSWORD = "admin123"
ASSISTENTE_EMAIL = "assistente@senai.br"
ASSISTENTE_PASSWORD = "assistente123"
CONSULTOR_EMAIL = "consultor@senai.br"
CONSULTOR_PASSWORD = "consultor123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_admin_login(self, api_client):
        """Test admin login returns valid token"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "senha": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "usuario" in data
        assert data["usuario"]["role"] == "admin"
        print("PASS: Admin login successful")
    
    def test_assistente_login(self, api_client):
        """Test assistente login returns valid token"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ASSISTENTE_EMAIL,
            "senha": ASSISTENTE_PASSWORD
        })
        assert response.status_code == 200, f"Assistente login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "assistente"
        print("PASS: Assistente login successful")
    
    def test_consultor_login(self, api_client):
        """Test consultor login returns valid token"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": CONSULTOR_EMAIL,
            "senha": CONSULTOR_PASSWORD
        })
        assert response.status_code == 200, f"Consultor login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "consultor"
        print("PASS: Consultor login successful")


class TestReferenceEndpoints:
    """Test reference data endpoints (tipos, resultados, motivos)"""
    
    def test_listar_tipos_contato(self, admin_client):
        """GET /api/contatos/tipos - Returns all contact types"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/tipos")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 6  # ligacao, whatsapp, email, presencial, sms, outro
        
        # Verify structure
        first_tipo = data[0]
        assert "value" in first_tipo
        assert "label" in first_tipo
        assert "color" in first_tipo
        assert "icon" in first_tipo
        
        # Verify required types exist
        values = [t["value"] for t in data]
        assert "ligacao" in values
        assert "whatsapp" in values
        assert "email" in values
        print(f"PASS: Got {len(data)} contact types")
    
    def test_listar_resultados_contato(self, admin_client):
        """GET /api/contatos/resultados - Returns all contact results"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/resultados")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 7  # sucesso, nao_atendeu, caixa_postal, numero_errado, sem_resposta, pendente, agendado
        
        # Verify structure
        first_resultado = data[0]
        assert "value" in first_resultado
        assert "label" in first_resultado
        assert "color" in first_resultado
        
        # Verify required results exist
        values = [r["value"] for r in data]
        assert "sucesso" in values
        assert "nao_atendeu" in values
        print(f"PASS: Got {len(data)} contact results")
    
    def test_listar_motivos_contato(self, admin_client):
        """GET /api/contatos/motivos - Returns all contact motives"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/motivos")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 10  # documentacao, acompanhamento, etc.
        
        # Verify structure
        first_motivo = data[0]
        assert "value" in first_motivo
        assert "label" in first_motivo
        
        # Verify required motives exist
        values = [m["value"] for m in data]
        assert "documentacao" in values
        assert "acompanhamento" in values
        print(f"PASS: Got {len(data)} contact motives")
    
    def test_reference_endpoints_require_auth(self, api_client):
        """Reference endpoints should require authentication"""
        endpoints = ["/api/contatos/tipos", "/api/contatos/resultados", "/api/contatos/motivos"]
        for endpoint in endpoints:
            response = api_client.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
        print("PASS: Reference endpoints require authentication")


class TestStatisticsEndpoints:
    """Test statistics and dashboard endpoints"""
    
    def test_obter_estatisticas(self, admin_client):
        """GET /api/contatos/stats - Returns general contact statistics"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total" in data
        assert "sucesso" in data
        assert "sem_sucesso" in data
        assert "taxa_sucesso" in data
        assert "retornos_pendentes" in data
        assert "contatos_hoje" in data
        assert "por_tipo" in data
        assert "por_resultado" in data
        
        # Verify data types
        assert isinstance(data["total"], int)
        assert isinstance(data["taxa_sucesso"], (int, float))
        assert isinstance(data["por_tipo"], dict)
        assert isinstance(data["por_resultado"], dict)
        
        print(f"PASS: Stats - total={data['total']}, sucesso={data['sucesso']}, taxa={data['taxa_sucesso']}%")
    
    def test_obter_retornos_pendentes(self, admin_client):
        """GET /api/contatos/retornos - Returns pending and overdue returns"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/retornos")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "pendentes" in data
        assert "atrasados" in data
        assert "total_pendentes" in data
        assert "total_atrasados" in data
        
        # Verify data types
        assert isinstance(data["pendentes"], list)
        assert isinstance(data["atrasados"], list)
        assert isinstance(data["total_pendentes"], int)
        assert isinstance(data["total_atrasados"], int)
        
        print(f"PASS: Retornos - pendentes={data['total_pendentes']}, atrasados={data['total_atrasados']}")
    
    def test_retornos_with_limit(self, admin_client):
        """GET /api/contatos/retornos with limit parameter"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/retornos?limite=10")
        assert response.status_code == 200
        print("PASS: Retornos endpoint accepts limite parameter")


class TestContatoCRUD:
    """Test CRUD operations for contacts"""
    
    def test_registrar_contato_success(self, admin_client, test_pedido_id):
        """POST /api/contatos - Create a new contact successfully"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "ligacao",
            "resultado": "sucesso",
            "motivo": "acompanhamento",
            "descricao": "TEST_Contato de teste criado via pytest - acompanhamento geral do aluno",
            "contato_nome": "TEST_Maria Silva",
            "contato_telefone": "(71) 99999-8888"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 200, f"Failed to create contact: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "mensagem" in data
        assert "contato" in data
        assert data["mensagem"] == "Contato registrado com sucesso"
        
        contato = data["contato"]
        assert contato["tipo"] == "ligacao"
        assert contato["resultado"] == "sucesso"
        assert contato["motivo"] == "acompanhamento"
        assert contato["contato_nome"] == "TEST_Maria Silva"
        
        print(f"PASS: Created contact with ID: {data['id']}")
        return data["id"]
    
    def test_registrar_contato_with_retorno(self, admin_client, test_pedido_id):
        """POST /api/contatos - Create contact with return date scheduled"""
        retorno_date = (datetime.now() + timedelta(days=3)).isoformat()
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "whatsapp",
            "resultado": "agendado",
            "motivo": "documentacao",
            "descricao": "TEST_Contato via WhatsApp - aluno solicitou prazo para enviar documentos",
            "data_retorno": retorno_date
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        contato = data["contato"]
        assert contato["data_retorno"] is not None
        assert contato["retorno_realizado"] == False
        assert contato["precisa_retorno"] == True
        
        print(f"PASS: Created contact with scheduled return: {data['id']}")
        return data["id"]
    
    def test_registrar_contato_invalid_tipo(self, admin_client, test_pedido_id):
        """POST /api/contatos - Should fail with invalid tipo"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "invalid_tipo",
            "resultado": "sucesso",
            "motivo": "acompanhamento",
            "descricao": "TEST_Teste com tipo inválido"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 400
        print("PASS: Invalid tipo returns 400")
    
    def test_registrar_contato_invalid_resultado(self, admin_client, test_pedido_id):
        """POST /api/contatos - Should fail with invalid resultado"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "ligacao",
            "resultado": "invalid_resultado",
            "motivo": "acompanhamento",
            "descricao": "TEST_Teste com resultado inválido"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 400
        print("PASS: Invalid resultado returns 400")
    
    def test_registrar_contato_invalid_motivo(self, admin_client, test_pedido_id):
        """POST /api/contatos - Should fail with invalid motivo"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "ligacao",
            "resultado": "sucesso",
            "motivo": "invalid_motivo",
            "descricao": "TEST_Teste com motivo inválido"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 400
        print("PASS: Invalid motivo returns 400")
    
    def test_registrar_contato_descricao_too_short(self, admin_client, test_pedido_id):
        """POST /api/contatos - Should fail with descricao too short"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "ligacao",
            "resultado": "sucesso",
            "motivo": "acompanhamento",
            "descricao": "abc"  # min 5 chars
        }
        
        response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 422  # Pydantic validation error
        print("PASS: Short descricao returns 422")
    
    def test_listar_contatos_pedido(self, admin_client, test_pedido_id):
        """GET /api/contatos/pedido/{pedido_id} - List contacts for a pedido"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/pedido/{test_pedido_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "resumo" in data
        assert "contatos" in data
        
        resumo = data["resumo"]
        assert "pedido_id" in resumo
        assert "total_contatos" in resumo
        assert "contatos_sucesso" in resumo
        assert "contatos_sem_sucesso" in resumo
        assert "taxa_sucesso" in resumo
        
        assert isinstance(data["contatos"], list)
        print(f"PASS: Listed {len(data['contatos'])} contacts for pedido, total={resumo['total_contatos']}")
    
    def test_listar_contatos_pedido_with_filters(self, admin_client, test_pedido_id):
        """GET /api/contatos/pedido/{pedido_id} with tipo filter"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/pedido/{test_pedido_id}?tipo=ligacao")
        assert response.status_code == 200
        
        response2 = admin_client.get(f"{BASE_URL}/api/contatos/pedido/{test_pedido_id}?resultado=sucesso")
        assert response2.status_code == 200
        print("PASS: Filter parameters work correctly")
    
    def test_buscar_contato_por_id(self, admin_client, test_contato_id):
        """GET /api/contatos/{contato_id} - Get single contact by ID"""
        response = admin_client.get(f"{BASE_URL}/api/contatos/{test_contato_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_contato_id
        assert "tipo" in data
        assert "resultado" in data
        assert "motivo" in data
        assert "descricao" in data
        assert "tipo_label" in data  # Human-readable labels
        assert "resultado_label" in data
        assert "motivo_label" in data
        print(f"PASS: Retrieved contact {test_contato_id}")
    
    def test_buscar_contato_not_found(self, admin_client):
        """GET /api/contatos/{contato_id} - Returns 404 for non-existent"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = admin_client.get(f"{BASE_URL}/api/contatos/{fake_id}")
        assert response.status_code == 404
        print("PASS: Non-existent contact returns 404")
    
    def test_atualizar_contato(self, admin_client, test_contato_id):
        """PUT /api/contatos/{contato_id} - Update contact"""
        update_data = {
            "descricao": "TEST_Descrição atualizada via pytest - informações adicionais"
        }
        
        response = admin_client.put(f"{BASE_URL}/api/contatos/{test_contato_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "mensagem" in data
        assert "contato" in data
        assert data["contato"]["descricao"] == update_data["descricao"]
        
        # Verify with GET
        get_response = admin_client.get(f"{BASE_URL}/api/contatos/{test_contato_id}")
        assert get_response.json()["descricao"] == update_data["descricao"]
        print("PASS: Contact updated and verified")
    
    def test_atualizar_contato_resultado(self, admin_client, test_contato_id):
        """PUT /api/contatos/{contato_id} - Update resultado"""
        update_data = {
            "resultado": "pendente"
        }
        
        response = admin_client.put(f"{BASE_URL}/api/contatos/{test_contato_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["contato"]["resultado"] == "pendente"
        print("PASS: Contact resultado updated")
    
    def test_atualizar_contato_not_found(self, admin_client):
        """PUT /api/contatos/{contato_id} - Returns 404 for non-existent"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = admin_client.put(f"{BASE_URL}/api/contatos/{fake_id}", json={"descricao": "teste"})
        assert response.status_code == 404
        print("PASS: Update non-existent contact returns 404")


class TestRetornoWorkflow:
    """Test return scheduling workflow"""
    
    def test_marcar_retorno_realizado(self, admin_client, contato_with_retorno):
        """POST /api/contatos/{contato_id}/marcar-retorno - Mark return as done"""
        response = admin_client.post(f"{BASE_URL}/api/contatos/{contato_with_retorno}/marcar-retorno")
        assert response.status_code == 200
        data = response.json()
        
        assert data["mensagem"] == "Retorno marcado como realizado"
        assert data["contato"]["retorno_realizado"] == True
        
        # Verify with GET
        get_response = admin_client.get(f"{BASE_URL}/api/contatos/{contato_with_retorno}")
        assert get_response.json()["retorno_realizado"] == True
        print("PASS: Return marked as done and verified")
    
    def test_marcar_retorno_sem_agendamento(self, admin_client, test_contato_id):
        """POST /api/contatos/{contato_id}/marcar-retorno - Should fail if no return scheduled"""
        # First update to remove return date
        update_response = admin_client.put(f"{BASE_URL}/api/contatos/{test_contato_id}", json={
            "descricao": "TEST_Contato sem retorno agendado atualizado"
        })
        
        # Create a new contact without return
        contato_data = {
            "pedido_id": get_test_pedido_id(admin_client),
            "tipo": "email",
            "resultado": "sucesso",
            "motivo": "informacao",
            "descricao": "TEST_Contato sem retorno para testar erro"
        }
        create_response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        contato_sem_retorno_id = create_response.json()["id"]
        
        # Try to mark return as done
        response = admin_client.post(f"{BASE_URL}/api/contatos/{contato_sem_retorno_id}/marcar-retorno")
        assert response.status_code == 400
        print("PASS: Cannot mark return for contact without scheduled return")


class TestDeletePermissions:
    """Test delete endpoint and role-based access control"""
    
    def test_admin_can_delete(self, admin_client, test_pedido_id):
        """DELETE /api/contatos/{contato_id} - Admin can delete"""
        # Create a contact to delete
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "sms",
            "resultado": "sem_resposta",
            "motivo": "lembrete",
            "descricao": "TEST_Contato para ser excluído pelo admin"
        }
        create_response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        contato_id = create_response.json()["id"]
        
        # Delete as admin
        delete_response = admin_client.delete(f"{BASE_URL}/api/contatos/{contato_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["mensagem"] == "Contato excluído com sucesso"
        
        # Verify it's gone
        get_response = admin_client.get(f"{BASE_URL}/api/contatos/{contato_id}")
        assert get_response.status_code == 404
        print("PASS: Admin can delete contacts")
    
    def test_assistente_cannot_delete(self, assistente_client, admin_client, test_pedido_id):
        """DELETE /api/contatos/{contato_id} - Assistente cannot delete (403)"""
        # Create a contact as admin
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "presencial",
            "resultado": "sucesso",
            "motivo": "confirmacao",
            "descricao": "TEST_Contato que assistente não pode excluir"
        }
        create_response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        contato_id = create_response.json()["id"]
        
        # Try to delete as assistente
        delete_response = assistente_client.delete(f"{BASE_URL}/api/contatos/{contato_id}")
        assert delete_response.status_code == 403, f"Expected 403, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify contact still exists
        get_response = admin_client.get(f"{BASE_URL}/api/contatos/{contato_id}")
        assert get_response.status_code == 200
        print("PASS: Assistente cannot delete contacts (403)")
    
    def test_consultor_cannot_delete(self, consultor_client, admin_client, test_pedido_id):
        """DELETE /api/contatos/{contato_id} - Consultor cannot delete (403)"""
        # Create a contact as admin
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "outro",
            "resultado": "sucesso",
            "motivo": "outro",
            "descricao": "TEST_Contato que consultor não pode excluir"
        }
        create_response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        contato_id = create_response.json()["id"]
        
        # Try to delete as consultor
        delete_response = consultor_client.delete(f"{BASE_URL}/api/contatos/{contato_id}")
        assert delete_response.status_code == 403
        print("PASS: Consultor cannot delete contacts (403)")
    
    def test_delete_not_found(self, admin_client):
        """DELETE /api/contatos/{contato_id} - Returns 404 for non-existent"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = admin_client.delete(f"{BASE_URL}/api/contatos/{fake_id}")
        assert response.status_code == 404
        print("PASS: Delete non-existent contact returns 404")


class TestAssistenteAccess:
    """Test that assistente can access all read operations"""
    
    def test_assistente_can_list_tipos(self, assistente_client):
        """Assistente can list contact types"""
        response = assistente_client.get(f"{BASE_URL}/api/contatos/tipos")
        assert response.status_code == 200
        print("PASS: Assistente can list tipos")
    
    def test_assistente_can_get_stats(self, assistente_client):
        """Assistente can get statistics"""
        response = assistente_client.get(f"{BASE_URL}/api/contatos/stats")
        assert response.status_code == 200
        print("PASS: Assistente can get stats")
    
    def test_assistente_can_create_contato(self, assistente_client, test_pedido_id):
        """Assistente can create contacts"""
        contato_data = {
            "pedido_id": test_pedido_id,
            "tipo": "email",
            "resultado": "sem_resposta",
            "motivo": "documentacao",
            "descricao": "TEST_Contato criado pelo assistente"
        }
        response = assistente_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
        assert response.status_code == 200
        print("PASS: Assistente can create contacts")


# ==================== FIXTURES ====================

def get_test_pedido_id(client):
    """Helper to get a valid pedido_id"""
    response = client.get(f"{BASE_URL}/api/pedidos?limit=1")
    if response.status_code == 200 and response.json().get("pedidos"):
        return response.json()["pedidos"][0]["id"]
    return None


@pytest.fixture(scope="session")
def api_client():
    """Basic requests session without auth"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def admin_client(api_client):
    """Authenticated session as admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "senha": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    
    token = response.json()["token"]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    return session


@pytest.fixture(scope="session")
def assistente_client(api_client):
    """Authenticated session as assistente"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ASSISTENTE_EMAIL,
        "senha": ASSISTENTE_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Assistente login failed: {response.text}")
    
    token = response.json()["token"]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    return session


@pytest.fixture(scope="session")
def consultor_client(api_client):
    """Authenticated session as consultor"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": CONSULTOR_EMAIL,
        "senha": CONSULTOR_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Consultor login failed: {response.text}")
    
    token = response.json()["token"]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    return session


@pytest.fixture(scope="session")
def test_pedido_id(admin_client):
    """Get a valid pedido ID for testing"""
    response = admin_client.get(f"{BASE_URL}/api/pedidos?limit=1")
    if response.status_code == 200 and response.json().get("pedidos"):
        return response.json()["pedidos"][0]["id"]
    pytest.skip("No pedidos available for testing")


@pytest.fixture(scope="function")
def test_contato_id(admin_client, test_pedido_id):
    """Create a test contact and return its ID"""
    contato_data = {
        "pedido_id": test_pedido_id,
        "tipo": "ligacao",
        "resultado": "sucesso",
        "motivo": "acompanhamento",
        "descricao": "TEST_Contato criado para testes unitários"
    }
    response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
    if response.status_code != 200:
        pytest.skip(f"Failed to create test contact: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def contato_with_retorno(admin_client, test_pedido_id):
    """Create a contact with scheduled return"""
    retorno_date = (datetime.now() + timedelta(days=2)).isoformat()
    contato_data = {
        "pedido_id": test_pedido_id,
        "tipo": "whatsapp",
        "resultado": "agendado",
        "motivo": "documentacao",
        "descricao": "TEST_Contato com retorno agendado para testes",
        "data_retorno": retorno_date
    }
    response = admin_client.post(f"{BASE_URL}/api/contatos", json=contato_data)
    if response.status_code != 200:
        pytest.skip(f"Failed to create contact with return: {response.text}")
    return response.json()["id"]
