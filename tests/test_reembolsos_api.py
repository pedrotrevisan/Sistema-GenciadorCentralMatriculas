"""
Test Suite for Reembolsos (Refund) Module API
Tests all CRUD operations and business logic for the refund management system
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://enrollment-central.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@senai.br"
ADMIN_PASSWORD = "admin123"
ASSISTENTE_EMAIL = "assistente@senai.br"
ASSISTENTE_PASSWORD = "assistente123"


class TestReembolsosAPI:
    """Test suite for Reembolsos API endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "senha": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def assistente_token(self):
        """Get assistente authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ASSISTENTE_EMAIL,
            "senha": ASSISTENTE_PASSWORD
        })
        assert response.status_code == 200, f"Assistente login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Headers with admin auth"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture
    def assistente_headers(self, assistente_token):
        """Headers with assistente auth"""
        return {"Authorization": f"Bearer {assistente_token}", "Content-Type": "application/json"}
    
    # ==================== AUTH TESTS ====================
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "senha": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "admin"
        print("✓ Admin login successful")
    
    def test_assistente_login(self):
        """Test assistente login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ASSISTENTE_EMAIL,
            "senha": ASSISTENTE_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "assistente"
        print("✓ Assistente login successful")
    
    # ==================== MOTIVOS TESTS ====================
    
    def test_get_motivos_reembolso(self, admin_headers):
        """Test GET /api/reembolsos/motivos - List all refund reasons"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/motivos", headers=admin_headers)
        assert response.status_code == 200
        motivos = response.json()
        
        # Verify expected motivos exist
        motivo_values = [m["value"] for m in motivos]
        expected_motivos = ["sem_escolaridade", "sem_vaga", "passou_bolsista", "nao_tem_vaga", "desistencia", "outros"]
        for expected in expected_motivos:
            assert expected in motivo_values, f"Missing motivo: {expected}"
        
        # Verify desistencia has reter_taxa = True
        desistencia = next((m for m in motivos if m["value"] == "desistencia"), None)
        assert desistencia is not None
        assert desistencia["reter_taxa"] == True, "Desistencia should have reter_taxa=True"
        
        # Verify other motivos have reter_taxa = False
        for m in motivos:
            if m["value"] != "desistencia":
                assert m["reter_taxa"] == False, f"{m['value']} should have reter_taxa=False"
        
        print(f"✓ GET /api/reembolsos/motivos - {len(motivos)} motivos returned")
    
    # ==================== STATUS TESTS ====================
    
    def test_get_status_reembolso(self, admin_headers):
        """Test GET /api/reembolsos/status - List all refund statuses"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/status", headers=admin_headers)
        assert response.status_code == 200
        status_list = response.json()
        
        # Verify expected statuses exist
        status_values = [s["value"] for s in status_list]
        expected_statuses = ["aberto", "aguardando_dados_bancarios", "enviado_financeiro", "pago", "cancelado"]
        for expected in expected_statuses:
            assert expected in status_values, f"Missing status: {expected}"
        
        print(f"✓ GET /api/reembolsos/status - {len(status_list)} statuses returned")
    
    # ==================== DASHBOARD TESTS ====================
    
    def test_get_dashboard(self, admin_headers):
        """Test GET /api/reembolsos/dashboard - Dashboard data"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/dashboard", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "contagem_status" in data
        assert "total" in data
        assert "total_aberto" in data
        assert "total_aguardando" in data
        assert "total_enviado" in data
        assert "total_pago" in data
        
        print(f"✓ GET /api/reembolsos/dashboard - Total: {data['total']}, Abertos: {data['total_aberto']}")
    
    # ==================== CRUD TESTS ====================
    
    def test_create_reembolso_sem_escolaridade(self, admin_headers):
        """Test POST /api/reembolsos - Create refund with sem_escolaridade motivo"""
        payload = {
            "aluno_nome": "TEST_Aluno Sem Escolaridade",
            "aluno_cpf": "111.222.333-44",
            "curso": "Técnico em Mecatrônica",
            "turma": "T1-2026",
            "motivo": "sem_escolaridade",
            "numero_chamado_sgc": "SGC-001",
            "observacoes": "Teste automatizado - sem escolaridade"
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "aberto"
        assert data["reter_taxa"] == False, "sem_escolaridade should NOT retain 10%"
        
        print(f"✓ POST /api/reembolsos - Created reembolso ID: {data['id']}")
        return data["id"]
    
    def test_create_reembolso_desistencia(self, admin_headers):
        """Test POST /api/reembolsos - Create refund with desistencia motivo (should retain 10%)"""
        payload = {
            "aluno_nome": "TEST_Aluno Desistencia",
            "aluno_cpf": "555.666.777-88",
            "curso": "Técnico em Automação",
            "turma": "T2-2026",
            "motivo": "desistencia",
            "numero_chamado_sgc": "SGC-002",
            "observacoes": "Teste automatizado - desistência"
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "aberto"
        assert data["reter_taxa"] == True, "desistencia SHOULD retain 10%"
        
        print(f"✓ POST /api/reembolsos (desistencia) - Created with reter_taxa=True, ID: {data['id']}")
        return data["id"]
    
    def test_create_reembolso_invalid_motivo(self, admin_headers):
        """Test POST /api/reembolsos - Invalid motivo should return 400"""
        payload = {
            "aluno_nome": "TEST_Invalid Motivo",
            "curso": "Técnico em Teste",
            "motivo": "motivo_invalido"
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ POST /api/reembolsos - Invalid motivo returns 400")
    
    def test_list_reembolsos(self, admin_headers):
        """Test GET /api/reembolsos - List all refunds"""
        response = requests.get(f"{BASE_URL}/api/reembolsos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "reembolsos" in data
        assert "paginacao" in data
        assert "pagina_atual" in data["paginacao"]
        assert "total_itens" in data["paginacao"]
        
        # Verify reembolso structure
        if len(data["reembolsos"]) > 0:
            r = data["reembolsos"][0]
            assert "id" in r
            assert "aluno_nome" in r
            assert "curso" in r
            assert "motivo" in r
            assert "motivo_label" in r
            assert "status" in r
            assert "reter_taxa" in r
            assert "data_abertura" in r
        
        print(f"✓ GET /api/reembolsos - {len(data['reembolsos'])} reembolsos, total: {data['paginacao']['total_itens']}")
    
    def test_list_reembolsos_filter_by_status(self, admin_headers):
        """Test GET /api/reembolsos?status=aberto - Filter by status"""
        response = requests.get(f"{BASE_URL}/api/reembolsos?status=aberto", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned should have status=aberto
        for r in data["reembolsos"]:
            assert r["status"] == "aberto", f"Expected status=aberto, got {r['status']}"
        
        print(f"✓ GET /api/reembolsos?status=aberto - {len(data['reembolsos'])} reembolsos")
    
    def test_list_reembolsos_filter_by_motivo(self, admin_headers):
        """Test GET /api/reembolsos?motivo=desistencia - Filter by motivo"""
        response = requests.get(f"{BASE_URL}/api/reembolsos?motivo=desistencia", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned should have motivo=desistencia
        for r in data["reembolsos"]:
            assert r["motivo"] == "desistencia", f"Expected motivo=desistencia, got {r['motivo']}"
            assert r["reter_taxa"] == True, "desistencia should have reter_taxa=True"
        
        print(f"✓ GET /api/reembolsos?motivo=desistencia - {len(data['reembolsos'])} reembolsos")
    
    def test_get_reembolso_details(self, admin_headers):
        """Test GET /api/reembolsos/{id} - Get refund details"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Detalhes Aluno",
            "aluno_cpf": "999.888.777-66",
            "curso": "Técnico em Redes",
            "turma": "T3-2026",
            "motivo": "sem_vaga",
            "numero_chamado_sgc": "SGC-003",
            "observacoes": "Teste de detalhes"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Get details
        response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields
        assert data["id"] == reembolso_id
        assert data["aluno_nome"] == "TEST_Detalhes Aluno"
        assert data["aluno_cpf"] == "999.888.777-66"
        assert data["curso"] == "Técnico em Redes"
        assert data["turma"] == "T3-2026"
        assert data["motivo"] == "sem_vaga"
        assert data["motivo_label"] == "Sem Vaga 2026.1"
        assert data["numero_chamado_sgc"] == "SGC-003"
        assert data["status"] == "aberto"
        assert data["reter_taxa"] == False
        assert "data_abertura" in data
        assert "criado_por_nome" in data
        
        print(f"✓ GET /api/reembolsos/{reembolso_id} - Details retrieved successfully")
    
    def test_get_reembolso_not_found(self, admin_headers):
        """Test GET /api/reembolsos/{id} - Not found returns 404"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/invalid-id-12345", headers=admin_headers)
        assert response.status_code == 404
        print("✓ GET /api/reembolsos/invalid-id - Returns 404")
    
    def test_update_reembolso_status(self, admin_headers):
        """Test PUT /api/reembolsos/{id} - Update status"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Update Status",
            "curso": "Técnico em Eletrotécnica",
            "motivo": "passou_bolsista"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Update status to aguardando_dados_bancarios
        update_payload = {
            "status": "aguardando_dados_bancarios",
            "observacoes": "Aguardando dados bancários do aluno"
        }
        response = requests.put(f"{BASE_URL}/api/reembolsos/{reembolso_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "aguardando_dados_bancarios"
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert get_response.json()["status"] == "aguardando_dados_bancarios"
        
        print(f"✓ PUT /api/reembolsos/{reembolso_id} - Status updated to aguardando_dados_bancarios")
    
    def test_update_reembolso_dates(self, admin_headers):
        """Test PUT /api/reembolsos/{id} - Update dates"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Update Dates",
            "curso": "Técnico em Segurança",
            "motivo": "nao_tem_vaga"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Update dates
        update_payload = {
            "status": "enviado_financeiro",
            "data_retorno_financeiro": "2026-01-15",
            "data_provisao_pagamento": "2026-01-20",
            "numero_chamado_sgc": "SGC-UPDATED"
        }
        response = requests.put(f"{BASE_URL}/api/reembolsos/{reembolso_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        data = get_response.json()
        assert data["status"] == "enviado_financeiro"
        assert "2026-01-15" in data["data_retorno_financeiro"]
        assert "2026-01-20" in data["data_provisao_pagamento"]
        assert data["numero_chamado_sgc"] == "SGC-UPDATED"
        
        print(f"✓ PUT /api/reembolsos/{reembolso_id} - Dates updated successfully")
    
    def test_update_reembolso_invalid_status(self, admin_headers):
        """Test PUT /api/reembolsos/{id} - Invalid status returns 400"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Invalid Status",
            "curso": "Técnico em Teste",
            "motivo": "outros"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Try invalid status
        update_payload = {"status": "status_invalido"}
        response = requests.put(f"{BASE_URL}/api/reembolsos/{reembolso_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 400
        
        print("✓ PUT /api/reembolsos - Invalid status returns 400")
    
    def test_update_to_pago_sets_data_pagamento(self, admin_headers):
        """Test PUT /api/reembolsos/{id} - Setting status to 'pago' auto-sets data_pagamento"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Auto Data Pagamento",
            "curso": "Técnico em Automação",
            "motivo": "sem_escolaridade"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Update to pago
        update_payload = {"status": "pago"}
        response = requests.put(f"{BASE_URL}/api/reembolsos/{reembolso_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        
        # Verify data_pagamento was set
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        data = get_response.json()
        assert data["status"] == "pago"
        assert data["data_pagamento"] is not None, "data_pagamento should be auto-set when status=pago"
        
        print(f"✓ PUT /api/reembolsos - Status 'pago' auto-sets data_pagamento")
    
    # ==================== PERMISSION TESTS ====================
    
    def test_assistente_can_access_reembolsos(self, assistente_headers):
        """Test that assistente role can access reembolsos"""
        # Dashboard
        response = requests.get(f"{BASE_URL}/api/reembolsos/dashboard", headers=assistente_headers)
        assert response.status_code == 200
        
        # List
        response = requests.get(f"{BASE_URL}/api/reembolsos", headers=assistente_headers)
        assert response.status_code == 200
        
        # Motivos
        response = requests.get(f"{BASE_URL}/api/reembolsos/motivos", headers=assistente_headers)
        assert response.status_code == 200
        
        # Create
        payload = {
            "aluno_nome": "TEST_Assistente Create",
            "curso": "Técnico em Redes",
            "motivo": "sem_vaga"
        }
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=assistente_headers)
        assert response.status_code == 200
        
        print("✓ Assistente has full access to reembolsos module")
    
    def test_unauthorized_access(self):
        """Test that unauthenticated requests are rejected"""
        response = requests.get(f"{BASE_URL}/api/reembolsos")
        assert response.status_code == 401
        
        response = requests.get(f"{BASE_URL}/api/reembolsos/dashboard")
        assert response.status_code == 401
        
        response = requests.get(f"{BASE_URL}/api/reembolsos/motivos")
        assert response.status_code == 401
        
        print("✓ Unauthorized access returns 401")
    
    # ==================== DELETE TESTS ====================
    
    def test_delete_reembolso_admin_only(self, admin_headers, assistente_headers):
        """Test DELETE /api/reembolsos/{id} - Only admin can delete"""
        # Create a reembolso
        payload = {
            "aluno_nome": "TEST_Delete Test",
            "curso": "Técnico em Teste",
            "motivo": "outros"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Assistente should NOT be able to delete
        response = requests.delete(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=assistente_headers)
        assert response.status_code == 403, f"Expected 403 for assistente, got {response.status_code}"
        
        # Admin CAN delete
        response = requests.delete(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert response.status_code == 200
        
        # Verify deleted
        response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert response.status_code == 404
        
        print("✓ DELETE /api/reembolsos - Only admin can delete")
    
    # ==================== NEW FEATURES TESTS ====================
    
    def test_get_templates_email(self, admin_headers):
        """Test GET /api/reembolsos/templates-email - Get email templates"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/templates-email", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all templates exist
        assert "solicitacao_dados_bancarios" in data
        assert "confirmacao_recebimento" in data
        assert "confirmacao_pagamento" in data
        
        # Verify template structure
        for template_key in ["solicitacao_dados_bancarios", "confirmacao_recebimento", "confirmacao_pagamento"]:
            template = data[template_key]
            assert "assunto" in template, f"Missing 'assunto' in {template_key}"
            assert "corpo" in template, f"Missing 'corpo' in {template_key}"
            assert len(template["assunto"]) > 0, f"Empty 'assunto' in {template_key}"
            assert len(template["corpo"]) > 0, f"Empty 'corpo' in {template_key}"
        
        # Verify placeholders in templates
        solicitacao = data["solicitacao_dados_bancarios"]["corpo"]
        assert "[NOME_DO_CURSO]" in solicitacao
        assert "[MOTIVO]" in solicitacao
        assert "[NOME_ATENDENTE]" in solicitacao
        
        print("✓ GET /api/reembolsos/templates-email - All templates returned correctly")
    
    def test_create_reembolso_with_aluno_menor_idade(self, admin_headers):
        """Test POST /api/reembolsos - Create refund with aluno_menor_idade=True"""
        payload = {
            "aluno_nome": "TEST_Aluno Menor Idade",
            "aluno_cpf": "222.333.444-55",
            "aluno_email": "menor@teste.com",
            "aluno_telefone": "(71) 98888-7777",
            "aluno_menor_idade": True,
            "curso": "Técnico em Informática",
            "turma": "T1-2026",
            "motivo": "sem_escolaridade"
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        reembolso_id = data["id"]
        
        # Verify aluno_menor_idade was saved
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert get_response.status_code == 200
        details = get_response.json()
        
        assert details["aluno_menor_idade"] == True, "aluno_menor_idade should be True"
        assert details["aluno_email"] == "menor@teste.com", "aluno_email should be saved"
        assert details["aluno_telefone"] == "(71) 98888-7777", "aluno_telefone should be saved"
        
        print(f"✓ POST /api/reembolsos - Created with aluno_menor_idade=True, ID: {reembolso_id}")
    
    def test_create_reembolso_with_aluno_email(self, admin_headers):
        """Test POST /api/reembolsos - Create refund with aluno_email field"""
        payload = {
            "aluno_nome": "TEST_Aluno Com Email",
            "aluno_cpf": "333.444.555-66",
            "aluno_email": "aluno.email@teste.com",
            "curso": "Técnico em Redes",
            "motivo": "sem_vaga"
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        reembolso_id = response.json()["id"]
        
        # Verify email was saved
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert get_response.status_code == 200
        details = get_response.json()
        
        assert details["aluno_email"] == "aluno.email@teste.com", "aluno_email should be saved"
        
        print(f"✓ POST /api/reembolsos - Created with aluno_email, ID: {reembolso_id}")
    
    def test_register_dados_bancarios(self, admin_headers):
        """Test POST /api/reembolsos/{id}/dados-bancarios - Register bank data"""
        # First create a reembolso
        payload = {
            "aluno_nome": "TEST_Dados Bancarios",
            "aluno_cpf": "444.555.666-77",
            "curso": "Técnico em Mecânica",
            "motivo": "passou_bolsista"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Register bank data
        bank_data = {
            "banco_titular_nome": "João da Silva",
            "banco_titular_cpf": "123.456.789-00",
            "banco_nome": "Banco do Brasil",
            "banco_agencia": "1234-5",
            "banco_operacao": "",
            "banco_conta": "12345-6",
            "banco_tipo_conta": "corrente",
            "banco_responsavel_financeiro": False
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos/{reembolso_id}/dados-bancarios", 
                                json=bank_data, headers=admin_headers)
        assert response.status_code == 200, f"Register bank data failed: {response.text}"
        
        # Verify bank data was saved
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert get_response.status_code == 200
        details = get_response.json()
        
        assert details["banco_titular_nome"] == "João da Silva"
        assert details["banco_titular_cpf"] == "123.456.789-00"
        assert details["banco_nome"] == "Banco do Brasil"
        assert details["banco_agencia"] == "1234-5"
        assert details["banco_conta"] == "12345-6"
        assert details["banco_tipo_conta"] == "corrente"
        assert details["banco_responsavel_financeiro"] == False
        assert details["dados_bancarios_recebidos_em"] is not None
        
        print(f"✓ POST /api/reembolsos/{reembolso_id}/dados-bancarios - Bank data registered")
    
    def test_register_dados_bancarios_responsavel(self, admin_headers):
        """Test POST /api/reembolsos/{id}/dados-bancarios - Register bank data for minor (responsavel)"""
        # First create a reembolso for minor
        payload = {
            "aluno_nome": "TEST_Menor Responsavel",
            "aluno_cpf": "555.666.777-88",
            "aluno_menor_idade": True,
            "curso": "Técnico em Eletrônica",
            "motivo": "nao_tem_vaga"
        }
        create_response = requests.post(f"{BASE_URL}/api/reembolsos", json=payload, headers=admin_headers)
        assert create_response.status_code == 200
        reembolso_id = create_response.json()["id"]
        
        # Register bank data for responsavel
        bank_data = {
            "banco_titular_nome": "Maria Responsável",
            "banco_titular_cpf": "987.654.321-00",
            "banco_nome": "Caixa Econômica Federal",
            "banco_agencia": "5678",
            "banco_operacao": "013",
            "banco_conta": "98765-4",
            "banco_tipo_conta": "poupanca",
            "banco_responsavel_financeiro": True
        }
        
        response = requests.post(f"{BASE_URL}/api/reembolsos/{reembolso_id}/dados-bancarios", 
                                json=bank_data, headers=admin_headers)
        assert response.status_code == 200
        
        # Verify
        get_response = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        details = get_response.json()
        
        assert details["aluno_menor_idade"] == True
        assert details["banco_responsavel_financeiro"] == True
        assert details["banco_titular_nome"] == "Maria Responsável"
        assert details["banco_operacao"] == "013"
        assert details["banco_tipo_conta"] == "poupanca"
        
        print(f"✓ POST /api/reembolsos/{reembolso_id}/dados-bancarios - Bank data for responsavel registered")
    
    def test_list_reembolsos_shows_tem_dados_bancarios(self, admin_headers):
        """Test GET /api/reembolsos - List shows tem_dados_bancarios field"""
        response = requests.get(f"{BASE_URL}/api/reembolsos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that tem_dados_bancarios field exists in response
        if len(data["reembolsos"]) > 0:
            r = data["reembolsos"][0]
            assert "tem_dados_bancarios" in r, "tem_dados_bancarios field should be in list response"
        
        print("✓ GET /api/reembolsos - tem_dados_bancarios field present in list")
    
    def test_list_reembolsos_shows_aluno_menor_idade(self, admin_headers):
        """Test GET /api/reembolsos - List shows aluno_menor_idade field"""
        response = requests.get(f"{BASE_URL}/api/reembolsos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that aluno_menor_idade field exists in response
        if len(data["reembolsos"]) > 0:
            r = data["reembolsos"][0]
            assert "aluno_menor_idade" in r, "aluno_menor_idade field should be in list response"
        
        print("✓ GET /api/reembolsos - aluno_menor_idade field present in list")


# Cleanup function to remove test data
def cleanup_test_data():
    """Remove all TEST_ prefixed reembolsos"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "senha": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        return
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all reembolsos
    response = requests.get(f"{BASE_URL}/api/reembolsos?por_pagina=100", headers=headers)
    if response.status_code == 200:
        reembolsos = response.json()["reembolsos"]
        for r in reembolsos:
            if r["aluno_nome"].startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/reembolsos/{r['id']}", headers=headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
