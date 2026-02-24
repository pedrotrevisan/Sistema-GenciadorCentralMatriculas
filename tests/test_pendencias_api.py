"""
Test Suite for Central de Pendências Documentais API
Tests all CRUD operations and business logic for pendências management
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://enrollment-sync.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@senai.br"
ADMIN_PASSWORD = "admin123"
ASSISTENTE_EMAIL = "assistente@senai.br"
ASSISTENTE_PASSWORD = "assistente123"


class TestPendenciasAPI:
    """Test suite for Pendências API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self, email, password):
        """Helper to get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "senha": password
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def get_admin_token(self):
        """Get admin token"""
        return self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    def get_assistente_token(self):
        """Get assistente token"""
        return self.get_auth_token(ASSISTENTE_EMAIL, ASSISTENTE_PASSWORD)

    # ==================== AUTH TESTS ====================
    
    def test_01_login_admin(self):
        """Test admin login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "senha": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "usuario" in data
        assert data["usuario"]["role"] == "admin"
        print(f"✓ Admin login successful")
    
    def test_02_login_assistente(self):
        """Test assistente login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ASSISTENTE_EMAIL,
            "senha": ASSISTENTE_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "assistente"
        print(f"✓ Assistente login successful")

    # ==================== TIPOS DOCUMENTO TESTS ====================
    
    def test_03_get_tipos_documento(self):
        """Test GET /api/pendencias/tipos-documento"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/tipos-documento",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list), "Response should be a list"
        
        # Verify expected document types exist
        codigos = [t["codigo"] for t in data]
        assert "94" in codigos, "Comprovante de Residência (94) should exist"
        assert "131" in codigos, "RG-Frente (131) should exist"
        assert "132" in codigos, "RG-Verso (132) should exist"
        
        # Verify structure
        if len(data) > 0:
            tipo = data[0]
            assert "id" in tipo
            assert "codigo" in tipo
            assert "nome" in tipo
            assert "obrigatorio" in tipo
        
        print(f"✓ GET tipos-documento returned {len(data)} document types")

    # ==================== DASHBOARD TESTS ====================
    
    def test_04_get_pendencias_dashboard(self):
        """Test GET /api/pendencias/dashboard"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify dashboard structure
        assert "contagem_status" in data, "Should have contagem_status"
        assert "por_documento" in data, "Should have por_documento"
        assert "total_abertas" in data, "Should have total_abertas"
        assert "total_criticas" in data, "Should have total_criticas"
        assert "total_pendente" in data, "Should have total_pendente"
        assert "total_aguardando" in data, "Should have total_aguardando"
        assert "total_em_analise" in data, "Should have total_em_analise"
        assert "total_aprovado" in data, "Should have total_aprovado"
        assert "total_rejeitado" in data, "Should have total_rejeitado"
        assert "total_reenvio" in data, "Should have total_reenvio"
        
        print(f"✓ Dashboard loaded - Total abertas: {data['total_abertas']}, Pendentes: {data['total_pendente']}")

    # ==================== LIST PENDENCIAS TESTS ====================
    
    def test_05_list_pendencias(self):
        """Test GET /api/pendencias - List all pendências"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "pendencias" in data, "Should have pendencias list"
        assert "paginacao" in data, "Should have paginacao"
        
        # Verify pagination structure
        pag = data["paginacao"]
        assert "pagina_atual" in pag
        assert "por_pagina" in pag
        assert "total_itens" in pag
        assert "total_paginas" in pag
        
        print(f"✓ List pendências returned {len(data['pendencias'])} items, total: {pag['total_itens']}")
        
        # Verify pendencia structure if any exist
        if len(data["pendencias"]) > 0:
            p = data["pendencias"][0]
            assert "id" in p
            assert "aluno_nome" in p
            assert "documento_codigo" in p
            assert "documento_nome" in p
            assert "status" in p
            assert "total_contatos" in p
            print(f"  First pendência: {p['aluno_nome']} - {p['documento_nome']} ({p['status']})")
    
    def test_06_list_pendencias_with_status_filter(self):
        """Test GET /api/pendencias with status filter"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Test filtering by status
        for status in ["pendente", "aguardando_aluno", "em_analise"]:
            response = self.session.get(
                f"{BASE_URL}/api/pendencias?status={status}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, f"Failed for status {status}: {response.text}"
            data = response.json()
            
            # Verify all returned items have the correct status
            for p in data["pendencias"]:
                assert p["status"] == status, f"Expected status {status}, got {p['status']}"
            
            print(f"✓ Filter by status '{status}' returned {len(data['pendencias'])} items")
    
    def test_07_list_pendencias_with_pagination(self):
        """Test GET /api/pendencias with pagination"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/pendencias?pagina=1&por_pagina=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert len(data["pendencias"]) <= 5, "Should return at most 5 items"
        assert data["paginacao"]["por_pagina"] == 5
        print(f"✓ Pagination working - returned {len(data['pendencias'])} items with por_pagina=5")

    # ==================== GET SINGLE PENDENCIA TESTS ====================
    
    def test_08_get_pendencia_details(self):
        """Test GET /api/pendencias/{id} - Get single pendência details"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # First get list to find a pendência ID
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["pendencias"]) == 0:
            pytest.skip("No pendências available to test")
        
        pendencia_id = data["pendencias"][0]["id"]
        
        # Get details
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/{pendencia_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        detail = response.json()
        
        # Verify detailed structure
        assert "id" in detail
        assert "aluno" in detail
        assert "pedido" in detail
        assert "documento_codigo" in detail
        assert "documento_nome" in detail
        assert "status" in detail
        assert "historico_contatos" in detail
        
        # Verify aluno structure
        assert "nome" in detail["aluno"]
        assert "cpf" in detail["aluno"]
        assert "email" in detail["aluno"]
        assert "telefone" in detail["aluno"]
        
        # Verify pedido structure
        assert "protocolo" in detail["pedido"]
        assert "curso" in detail["pedido"]
        
        print(f"✓ Get pendência details - Aluno: {detail['aluno']['nome']}, Doc: {detail['documento_nome']}")
    
    def test_09_get_pendencia_not_found(self):
        """Test GET /api/pendencias/{id} with invalid ID"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/invalid-id-12345",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Get non-existent pendência returns 404")

    # ==================== CREATE PENDENCIA TESTS ====================
    
    def test_10_create_pendencia_requires_valid_aluno(self):
        """Test POST /api/pendencias - Requires valid aluno_id"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "aluno_id": "invalid-aluno-id",
                "pedido_id": "invalid-pedido-id",
                "documento_codigo": "94"
            }
        )
        assert response.status_code == 404, f"Expected 404 for invalid aluno, got {response.status_code}"
        print(f"✓ Create pendência with invalid aluno returns 404")

    # ==================== UPDATE STATUS TESTS ====================
    
    def test_11_update_pendencia_status(self):
        """Test PUT /api/pendencias/{id} - Update status"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Get a pendência to update
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["pendencias"]) == 0:
            pytest.skip("No pendências available to test")
        
        pendencia = data["pendencias"][0]
        pendencia_id = pendencia["id"]
        original_status = pendencia["status"]
        
        # Update to em_analise
        new_status = "em_analise" if original_status != "em_analise" else "aguardando_aluno"
        
        response = self.session.put(
            f"{BASE_URL}/api/pendencias/{pendencia_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": new_status,
                "observacoes": "Teste de atualização de status"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert result["status"] == new_status
        assert "mensagem" in result
        
        print(f"✓ Update status from '{original_status}' to '{new_status}'")
        
        # Restore original status
        self.session.put(
            f"{BASE_URL}/api/pendencias/{pendencia_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": original_status}
        )
    
    def test_12_update_pendencia_invalid_status(self):
        """Test PUT /api/pendencias/{id} with invalid status"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Get a pendência
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        
        if len(data["pendencias"]) == 0:
            pytest.skip("No pendências available to test")
        
        pendencia_id = data["pendencias"][0]["id"]
        
        response = self.session.put(
            f"{BASE_URL}/api/pendencias/{pendencia_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid status, got {response.status_code}"
        print(f"✓ Update with invalid status returns 400")

    # ==================== REGISTER CONTACT TESTS ====================
    
    def test_13_register_contact(self):
        """Test POST /api/pendencias/{id}/contatos - Register contact"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Get a pendência
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        
        if len(data["pendencias"]) == 0:
            pytest.skip("No pendências available to test")
        
        pendencia_id = data["pendencias"][0]["id"]
        
        # Register contact
        response = self.session.post(
            f"{BASE_URL}/api/pendencias/{pendencia_id}/contatos",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "tipo_contato": "telefone",
                "descricao": "Teste de registro de contato via API",
                "resultado": "atendeu"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert "id" in result
        assert "mensagem" in result
        assert "novo_status" in result
        
        print(f"✓ Contact registered successfully - ID: {result['id']}")
    
    def test_14_register_contact_invalid_type(self):
        """Test POST /api/pendencias/{id}/contatos with invalid tipo_contato"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Get a pendência
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        
        if len(data["pendencias"]) == 0:
            pytest.skip("No pendências available to test")
        
        pendencia_id = data["pendencias"][0]["id"]
        
        response = self.session.post(
            f"{BASE_URL}/api/pendencias/{pendencia_id}/contatos",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "tipo_contato": "invalid_type",
                "descricao": "Test"
            }
        )
        assert response.status_code == 400, f"Expected 400 for invalid tipo_contato, got {response.status_code}"
        print(f"✓ Register contact with invalid type returns 400")

    # ==================== ASSISTENTE ACCESS TESTS ====================
    
    def test_15_assistente_can_access_pendencias(self):
        """Test that assistente role can access pendências"""
        token = self.get_assistente_token()
        assert token, "Failed to get assistente token"
        
        # Dashboard
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Assistente should access dashboard: {response.text}"
        
        # List
        response = self.session.get(
            f"{BASE_URL}/api/pendencias",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Assistente should access list: {response.text}"
        
        # Tipos documento
        response = self.session.get(
            f"{BASE_URL}/api/pendencias/tipos-documento",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Assistente should access tipos-documento: {response.text}"
        
        print(f"✓ Assistente can access all pendências endpoints")

    # ==================== UNAUTHORIZED ACCESS TESTS ====================
    
    def test_16_unauthorized_access(self):
        """Test that unauthenticated requests are rejected"""
        endpoints = [
            "/api/pendencias/dashboard",
            "/api/pendencias",
            "/api/pendencias/tipos-documento"
        ]
        
        for endpoint in endpoints:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"Expected 401 for {endpoint}, got {response.status_code}"
        
        print(f"✓ All endpoints require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
