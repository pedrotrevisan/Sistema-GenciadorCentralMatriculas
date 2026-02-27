"""
Test Suite for Atividades (Activity Log) API - Log de Atividades na página Minha Conta
Tests for:
- GET /api/auth/me/atividades - Lista atividades do usuário
- Activity registration on login
- Activity registration on password change
- Activity registration on profile update
- Activity type filtering
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://senai-cimatec.preview.emergentagent.com').rstrip('/')


class TestAtividadesAPI:
    """Test Activity Log functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login and get tokens"""
        # Admin login
        admin_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@senai.br", "senha": "admin123"}
        )
        assert admin_response.status_code == 200, f"Admin login failed: {admin_response.text}"
        self.admin_token = admin_response.json()["token"]
        self.admin_user = admin_response.json()["usuario"]
        
        # Assistente login
        assistente_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "assistente123"}
        )
        assert assistente_response.status_code == 200, f"Assistente login failed: {assistente_response.text}"
        self.assistente_token = assistente_response.json()["token"]
        self.assistente_user = assistente_response.json()["usuario"]
        
        yield
    
    # ==================== GET /api/auth/me/atividades ====================
    
    def test_get_atividades_authenticated(self):
        """Test GET /api/auth/me/atividades - Returns activities for authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "atividades" in data, "Response should contain 'atividades' key"
        assert "auditorias" in data, "Response should contain 'auditorias' key (legacy)"
        assert "pedidos_recentes" in data, "Response should contain 'pedidos_recentes' key"
        assert "tipos_disponiveis" in data, "Response should contain 'tipos_disponiveis' key"
        
        # Verify atividades is a list
        assert isinstance(data["atividades"], list)
        
        # If there are activities, verify structure
        if len(data["atividades"]) > 0:
            atividade = data["atividades"][0]
            assert "id" in atividade
            assert "tipo" in atividade
            assert "tipo_icone" in atividade
            assert "tipo_cor" in atividade
            assert "descricao" in atividade
            assert "created_at" in atividade
    
    def test_get_atividades_unauthenticated(self):
        """Test GET /api/auth/me/atividades without token - Returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me/atividades")
        assert response.status_code == 401
    
    def test_get_atividades_with_tipo_filter(self):
        """Test GET /api/auth/me/atividades?tipo=login - Filter by activity type"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=login",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All activities should be login type
        for atividade in data["atividades"]:
            assert atividade["tipo"] == "login", f"Expected tipo=login, got {atividade['tipo']}"
    
    def test_get_atividades_with_limite(self):
        """Test GET /api/auth/me/atividades?limite=5 - Limit number of results"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?limite=5",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at most 5 activities
        assert len(data["atividades"]) <= 5
    
    def test_get_atividades_tipos_disponiveis(self):
        """Test that tipos_disponiveis contains expected activity types"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        tipos_disponiveis = data["tipos_disponiveis"]
        assert isinstance(tipos_disponiveis, list)
        
        # Expected types
        expected_types = ["login", "alterar_senha", "alterar_perfil"]
        tipo_names = [t["tipo"] for t in tipos_disponiveis]
        
        for expected in expected_types:
            assert expected in tipo_names, f"Expected type '{expected}' not found in tipos_disponiveis"
        
        # Each tipo should have icone, descricao, cor
        for tipo in tipos_disponiveis:
            assert "tipo" in tipo
            assert "icone" in tipo
            assert "descricao" in tipo
            assert "cor" in tipo
    
    # ==================== LOGIN Activity Logging ====================
    
    def test_login_registers_activity(self):
        """Test that login creates an activity entry"""
        # Login fresh
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@senai.br", "senha": "admin123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Check activities
        time.sleep(0.5)  # Small delay to ensure activity is recorded
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=login&limite=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least one login activity
        assert len(data["atividades"]) >= 1
        latest_activity = data["atividades"][0]
        assert latest_activity["tipo"] == "login"
        assert "Fez login no sistema" in latest_activity["descricao"]
    
    # ==================== PASSWORD CHANGE Activity Logging ====================
    
    def test_password_change_registers_activity(self):
        """Test that password change creates an activity entry"""
        # Login with assistente
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "assistente123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Change password
        change_response = requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "senha_atual": "assistente123",
                "nova_senha": "newpassword456",
                "confirmar_senha": "newpassword456"
            }
        )
        assert change_response.status_code == 200
        assert change_response.json()["message"] == "Senha alterada com sucesso"
        
        # Check activities
        time.sleep(0.5)
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=alterar_senha&limite=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have password change activity
        assert len(data["atividades"]) >= 1
        latest_activity = data["atividades"][0]
        assert latest_activity["tipo"] == "alterar_senha"
        assert "senha" in latest_activity["descricao"].lower()
        
        # Restore password
        new_login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "newpassword456"}
        )
        new_token = new_login.json()["token"]
        
        requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {new_token}"},
            json={
                "senha_atual": "newpassword456",
                "nova_senha": "assistente123",
                "confirmar_senha": "assistente123"
            }
        )
    
    # ==================== PROFILE UPDATE Activity Logging ====================
    
    def test_profile_update_registers_activity(self):
        """Test that profile update creates an activity entry"""
        # Login with assistente
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "assistente123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        original_name = login_response.json()["usuario"]["nome"]
        
        # Update profile
        update_response = requests.put(
            f"{BASE_URL}/api/auth/me/perfil",
            headers={"Authorization": f"Bearer {token}"},
            json={"nome": "TEST_Assistente Atualizado"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["nome"] == "TEST_Assistente Atualizado"
        
        # Check activities
        time.sleep(0.5)
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=alterar_perfil&limite=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have profile update activity
        assert len(data["atividades"]) >= 1
        latest_activity = data["atividades"][0]
        assert latest_activity["tipo"] == "alterar_perfil"
        assert "perfil" in latest_activity["descricao"].lower()
        
        # Verify detalhes contains campos_alterados
        if latest_activity["detalhes"]:
            assert "campos_alterados" in latest_activity["detalhes"]
            assert "nome" in latest_activity["detalhes"]["campos_alterados"]
        
        # Restore original name
        requests.put(
            f"{BASE_URL}/api/auth/me/perfil",
            headers={"Authorization": f"Bearer {token}"},
            json={"nome": original_name}
        )
    
    # ==================== Auditorias (Legacy) ====================
    
    def test_auditorias_retrocompatibility(self):
        """Test that legacy auditorias are returned in response"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Auditorias key should exist
        assert "auditorias" in data
        assert isinstance(data["auditorias"], list)
        
        # If there are auditorias, verify structure
        if len(data["auditorias"]) > 0:
            auditoria = data["auditorias"][0]
            assert "id" in auditoria
            assert "tipo" in auditoria
            assert "descricao" in auditoria
            assert "created_at" in auditoria
    
    # ==================== Pedidos Recentes ====================
    
    def test_pedidos_recentes_structure(self):
        """Test that pedidos_recentes are returned correctly"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pedidos_recentes" in data
        assert isinstance(data["pedidos_recentes"], list)
        
        # If there are pedidos, verify structure
        if len(data["pedidos_recentes"]) > 0:
            pedido = data["pedidos_recentes"][0]
            assert "id" in pedido
            assert "protocolo" in pedido
            assert "curso" in pedido
            assert "status" in pedido
            assert "created_at" in pedido


class TestAtividadesValidation:
    """Test validation rules for Atividades API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@senai.br", "senha": "admin123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        yield
    
    def test_invalid_tipo_filter_returns_empty(self):
        """Test that invalid tipo filter returns empty list"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=invalid_type",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty atividades list (no matching activities)
        assert len(data["atividades"]) == 0
    
    def test_limite_boundary_min(self):
        """Test limite parameter minimum value (1)"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?limite=1",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["atividades"]) <= 1
    
    def test_limite_boundary_max(self):
        """Test limite parameter maximum value (100)"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?limite=100",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["atividades"]) <= 100
    
    def test_limite_exceeds_max(self):
        """Test limite exceeds maximum - should return validation error"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?limite=200",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        # FastAPI should return 422 for validation error
        assert response.status_code == 422


class TestPasswordChangeValidation:
    """Test password change validation and activity logging"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login with assistente"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "assistente123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        yield
    
    def test_password_change_wrong_current_password(self):
        """Test password change with wrong current password - Returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "senha_atual": "wrongpassword",
                "nova_senha": "newpassword123",
                "confirmar_senha": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        assert "Senha atual incorreta" in response.json().get("detail", "")
    
    def test_password_change_mismatch_confirmation(self):
        """Test password change with mismatched confirmation - Returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "senha_atual": "assistente123",
                "nova_senha": "newpassword123",
                "confirmar_senha": "differentpassword"
            }
        )
        
        assert response.status_code == 400
        assert "não conferem" in response.json().get("detail", "").lower()
    
    def test_password_change_same_as_current(self):
        """Test password change with same password - Returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "senha_atual": "assistente123",
                "nova_senha": "assistente123",
                "confirmar_senha": "assistente123"
            }
        )
        
        assert response.status_code == 400
        assert "diferente da atual" in response.json().get("detail", "").lower()
    
    def test_password_change_too_short(self):
        """Test password change with short password - Returns 422"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/senha",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "senha_atual": "assistente123",
                "nova_senha": "12345",
                "confirmar_senha": "12345"
            }
        )
        
        assert response.status_code == 422


class TestProfileUpdateValidation:
    """Test profile update validation and activity logging"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login with assistente"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "assistente@senai.br", "senha": "assistente123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        yield
    
    def test_profile_update_name_too_short(self):
        """Test profile update with name too short - Returns 422"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/perfil",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"nome": "AB"}
        )
        
        assert response.status_code == 422
    
    def test_profile_update_email_already_exists(self):
        """Test profile update with email that already exists - Returns 409"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me/perfil",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"email": "admin@senai.br"}
        )
        
        assert response.status_code == 409
        assert "já está em uso" in response.json().get("detail", "").lower()
    
    def test_profile_update_no_changes_no_activity(self):
        """Test profile update with no changes - Should not create activity"""
        # Get current activities count
        before = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=alterar_perfil",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        before_count = len(before.json()["atividades"])
        
        # Update with empty/null values (no actual changes)
        response = requests.put(
            f"{BASE_URL}/api/auth/me/perfil",
            headers={"Authorization": f"Bearer {self.token}"},
            json={}
        )
        
        assert response.status_code == 200
        
        # Check activities count - should be same (no new activity)
        after = requests.get(
            f"{BASE_URL}/api/auth/me/atividades?tipo=alterar_perfil",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        after_count = len(after.json()["atividades"])
        
        assert after_count == before_count, "Empty update should not create activity"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
