"""
Test suite for Chamados SGC Plus API - BMP Enrollment Tickets
Tests CRUD operations for SGC Plus tickets with all new fields
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "pedro.passos@fieb.org.br"
TEST_SENHA = "Pedro@2026"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "senha": TEST_SENHA
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestChamadosSGCDashboard:
    """Tests for Chamados SGC Dashboard endpoint"""

    def test_dashboard_returns_metrics(self, api_client):
        """GET /api/chamados-sgc/dashboard returns dashboard metrics"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_abertos" in data
        assert "criticos" in data
        assert "sla_critico" in data
        assert "fechados_hoje" in data
        assert "por_status" in data
        assert isinstance(data["total_abertos"], int)


class TestChamadosSGCList:
    """Tests for Chamados SGC List endpoint"""

    def test_list_chamados(self, api_client):
        """GET /api/chamados-sgc returns list with pagination"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc")
        assert response.status_code == 200
        
        data = response.json()
        assert "chamados" in data
        assert "paginacao" in data
        assert "pagina" in data["paginacao"]
        assert "total_itens" in data["paginacao"]
        
    def test_list_chamados_with_status_filter(self, api_client):
        """GET /api/chamados-sgc?status=backlog filters by status"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc?status=backlog")
        assert response.status_code == 200
        
        data = response.json()
        assert "chamados" in data
        for chamado in data["chamados"]:
            assert chamado["status"] == "backlog"

    def test_list_chamados_with_search(self, api_client):
        """GET /api/chamados-sgc?busca=XXX filters by search term"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc?busca=CACCM")
        assert response.status_code == 200
        
        data = response.json()
        assert "chamados" in data


class TestChamadosSGCCRUD:
    """Tests for Chamados SGC CRUD operations"""
    
    created_chamado_id = None
    
    def test_create_chamado_with_sgc_fields(self, api_client):
        """POST /api/chamados-sgc creates a new chamado with all SGC Plus fields"""
        chamado_data = {
            "numero_ticket": f"TEST_CACCM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "titulo": "TEST - Matrícula BMP Automação Industrial",
            "descricao": "Chamado de teste para validação do módulo SGC Plus",
            "data_abertura": datetime.now().isoformat(),
            "prioridade": 1,
            "critico": False,
            "sla_horas": 32.0,
            "solicitante_nome": "Teste Automatizado",
            "solicitante_unidade": "SENAI - CIMATEC",
            "classificacao": "Matrícula",
            "produto": "MATRÍCULA BMP",
            # New SGC Plus fields
            "codigo_curso": "AUT001",
            "nome_curso": "Automação Industrial",
            "turno": "Manhã",
            "periodo_letivo": "2026.1",
            "quantidade_vagas": 25,
            "modalidade": "CAP",
            "forma_pagamento": "Empresa",
            "cont": "CONT-12345",
            "requisito_acesso": "Ensino Médio Completo",
            "empresa_nome": "Empresa Teste LTDA",
            "empresa_contato": "João Silva",
            "empresa_email": "joao@empresa.com",
            "empresa_telefone": "(71) 99999-9999",
            "data_inicio_curso": "2026-04-01T00:00:00",
            "data_fim_curso": "2026-06-30T00:00:00",
            "documentos_obrigatorios": "RG, CPF, Comprovante de Escolaridade"
        }
        
        response = api_client.post(f"{BASE_URL}/api/chamados-sgc", json=chamado_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["message"] == "Chamado criado com sucesso"
        
        TestChamadosSGCCRUD.created_chamado_id = data["id"]
    
    def test_get_chamado_details(self, api_client):
        """GET /api/chamados-sgc/{id} returns chamado with andamentos and interacoes"""
        if not TestChamadosSGCCRUD.created_chamado_id:
            pytest.skip("No chamado created")
        
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "chamado" in data
        assert "andamentos" in data
        assert "interacoes" in data
        assert "esforco" in data
        
        chamado = data["chamado"]
        assert chamado["id"] == TestChamadosSGCCRUD.created_chamado_id
        assert chamado["status"] == "backlog"  # Default status
        
    def test_update_chamado_status(self, api_client):
        """PUT /api/chamados-sgc/{id} updates chamado status"""
        if not TestChamadosSGCCRUD.created_chamado_id:
            pytest.skip("No chamado created")
        
        response = api_client.put(
            f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}",
            json={"status": "em_atendimento"}
        )
        assert response.status_code == 200
        
        # Verify status changed
        get_response = api_client.get(f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}")
        assert get_response.status_code == 200
        assert get_response.json()["chamado"]["status"] == "em_atendimento"

    def test_add_interacao(self, api_client):
        """POST /api/chamados-sgc/{id}/interacao adds communication to chamado"""
        if not TestChamadosSGCCRUD.created_chamado_id:
            pytest.skip("No chamado created")
        
        response = api_client.post(
            f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}/interacao",
            json={
                "tipo": "comunicacao",
                "mensagem": "Teste de interação automatizada"
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Interação adicionada com sucesso"
        
        # Verify interacao was added
        get_response = api_client.get(f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}")
        assert get_response.status_code == 200
        interacoes = get_response.json()["interacoes"]
        assert len(interacoes) > 0
        assert interacoes[0]["mensagem"] == "Teste de interação automatizada"

    def test_add_esforco(self, api_client):
        """POST /api/chamados-sgc/{id}/esforco registers effort hours"""
        if not TestChamadosSGCCRUD.created_chamado_id:
            pytest.skip("No chamado created")
        
        response = api_client.post(
            f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}/esforco",
            json={
                "horas": 2.5,
                "data": datetime.now().strftime("%Y-%m-%d"),
                "descricao": "Análise do chamado"
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Esforço registrado com sucesso"
        
        # Verify esforco was added
        get_response = api_client.get(f"{BASE_URL}/api/chamados-sgc/{TestChamadosSGCCRUD.created_chamado_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["total_horas"] == 2.5
        assert len(data["esforco"]) > 0


class TestChamadosSGCEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_get_nonexistent_chamado(self, api_client):
        """GET /api/chamados-sgc/{invalid_id} returns 404"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc/invalid-uuid-123")
        assert response.status_code == 404
        
    def test_create_chamado_without_ticket_number(self, api_client):
        """POST /api/chamados-sgc without numero_ticket fails validation"""
        response = api_client.post(f"{BASE_URL}/api/chamados-sgc", json={
            "titulo": "Test without ticket",
            "data_abertura": datetime.now().isoformat()
        })
        # Should fail validation - numero_ticket is required
        assert response.status_code == 422


class TestChamadosSGCValidation:
    """Tests for data validation in Chamados SGC"""
    
    def test_chamado_has_expected_fields(self, api_client):
        """Verify chamado response has all expected fields"""
        response = api_client.get(f"{BASE_URL}/api/chamados-sgc")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["chamados"]) > 0:
            chamado = data["chamados"][0]
            expected_fields = [
                "id", "numero_ticket", "titulo", "descricao", "data_abertura",
                "status", "prioridade", "critico", "sla_horas", "sla_consumido",
                "solicitante_nome", "solicitante_unidade", "classificacao", "produto"
            ]
            for field in expected_fields:
                assert field in chamado, f"Missing field: {field}"
