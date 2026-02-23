"""
Test Suite for Apoio Cognitivo Module - Meu Dia & Base de Conhecimento
Tests all CRUD operations for Tarefas, Lembretes, and Artigos (knowledge base)
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@senai.br", "senha": "admin123"}
ASSISTENTE_CREDENTIALS = {"email": "assistente@senai.br", "senha": "assistente123"}


class TestAuthentication:
    """Test authentication for accessing apoio cognitivo endpoints"""
    
    def test_admin_login(self):
        """Test admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "admin"
        print("PASS: Admin login successful")
    
    def test_assistente_login(self):
        """Test assistente login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ASSISTENTE_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "assistente"
        print("PASS: Assistente login successful")
    
    def test_unauthenticated_meu_dia(self):
        """Test unauthenticated access to meu-dia returns 401"""
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia")
        assert response.status_code == 401
        print("PASS: Unauthenticated access returns 401")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def assistente_token():
    """Get assistente authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ASSISTENTE_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Assistente authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    """Get headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def assistente_headers(assistente_token):
    """Get headers with assistente auth token"""
    return {
        "Authorization": f"Bearer {assistente_token}",
        "Content-Type": "application/json"
    }


class TestMeuDia:
    """Test Meu Dia endpoint - daily summary"""
    
    def test_get_meu_dia(self, admin_headers):
        """GET /api/apoio/meu-dia - Returns daily summary"""
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "data" in data
        assert "dia_semana" in data
        assert "saudacao" in data
        assert "tarefas" in data
        assert "lembretes" in data
        assert "resumo" in data
        
        # Validate resumo structure
        resumo = data["resumo"]
        assert "tarefas_total" in resumo
        assert "tarefas_concluidas" in resumo
        assert "pendencias_abertas" in resumo
        assert "pedidos_andamento" in resumo
        assert "lembretes_hoje" in resumo
        
        print(f"PASS: Meu Dia returned - {data['saudacao']}, {data['dia_semana']}")
    
    def test_meu_dia_assistente(self, assistente_headers):
        """Test assistente can access meu-dia"""
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=assistente_headers)
        assert response.status_code == 200
        data = response.json()
        assert "saudacao" in data
        print("PASS: Assistente can access Meu Dia")


class TestTarefas:
    """Test Tarefas (Tasks) CRUD operations"""
    
    created_task_ids = []
    
    def test_create_tarefa(self, admin_headers):
        """POST /api/apoio/tarefas - Create new task"""
        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "titulo": "TEST_Tarefa de teste automatizado",
            "descricao": "Descrição da tarefa de teste",
            "categoria": "rotina",
            "prioridade": 1,
            "recorrente": False,
            "horario_sugerido": "09:00",
            "data_tarefa": today
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["titulo"] == "TEST_Tarefa de teste automatizado"
        assert "mensagem" in data
        
        self.created_task_ids.append(data["id"])
        print(f"PASS: Tarefa created with ID: {data['id']}")
    
    def test_create_recurrent_tarefa(self, admin_headers):
        """POST /api/apoio/tarefas - Create recurrent task"""
        payload = {
            "titulo": "TEST_Tarefa recorrente",
            "descricao": "Tarefa que repete todos os dias",
            "categoria": "lembrete",
            "prioridade": 2,
            "recorrente": True,
            "dias_semana": "1,2,3,4,5"  # Monday to Friday
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        self.created_task_ids.append(data["id"])
        print(f"PASS: Recurrent tarefa created with ID: {data['id']}")
    
    def test_listar_tarefas(self, admin_headers):
        """GET /api/apoio/tarefas - List all tasks"""
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            task = data[0]
            assert "id" in task
            assert "titulo" in task
            assert "categoria" in task
            assert "concluida" in task
        
        print(f"PASS: Listed {len(data)} tarefas")
    
    def test_listar_tarefas_by_date(self, admin_headers):
        """GET /api/apoio/tarefas?data=YYYY-MM-DD - Filter by date"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas?data={today}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Listed {len(data)} tarefas for today")
    
    def test_listar_tarefas_by_categoria(self, admin_headers):
        """GET /api/apoio/tarefas?categoria=rotina - Filter by category"""
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas?categoria=rotina", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for task in data:
            assert task["categoria"] == "rotina"
        print(f"PASS: Listed {len(data)} tarefas with categoria=rotina")
    
    def test_concluir_tarefa(self, admin_headers):
        """PATCH /api/apoio/tarefas/{id}/concluir - Toggle task completion"""
        if not self.created_task_ids:
            pytest.skip("No task created to test completion")
        
        task_id = self.created_task_ids[0]
        
        # First toggle - mark as completed
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/{task_id}/concluir", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "concluida" in data
        assert data["concluida"] == True
        print(f"PASS: Task {task_id} marked as completed")
        
        # Second toggle - mark as not completed
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/{task_id}/concluir", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["concluida"] == False
        print(f"PASS: Task {task_id} marked as not completed (toggled)")
    
    def test_concluir_tarefa_not_found(self, admin_headers):
        """PATCH /api/apoio/tarefas/{id}/concluir - 404 for non-existent task"""
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/non-existent-id/concluir", headers=admin_headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent task")
    
    def test_delete_tarefa(self, admin_headers):
        """DELETE /api/apoio/tarefas/{id} - Remove task"""
        if not self.created_task_ids:
            pytest.skip("No task created to test deletion")
        
        task_id = self.created_task_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/tarefas/{task_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Task {task_id} deleted successfully")
    
    def test_delete_tarefa_not_found(self, admin_headers):
        """DELETE /api/apoio/tarefas/{id} - 404 for non-existent task"""
        response = requests.delete(f"{BASE_URL}/api/apoio/tarefas/non-existent-id", headers=admin_headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent task deletion")
    
    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, admin_headers):
        """Cleanup test tasks after all tests"""
        yield
        for task_id in self.created_task_ids:
            requests.delete(f"{BASE_URL}/api/apoio/tarefas/{task_id}", headers=admin_headers)


class TestLembretes:
    """Test Lembretes (Reminders) CRUD operations"""
    
    created_lembrete_ids = []
    
    def test_create_lembrete(self, admin_headers):
        """POST /api/apoio/lembretes - Create new reminder"""
        # Set reminder for 1 hour from now
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        payload = {
            "titulo": "TEST_Lembrete de teste",
            "descricao": "Descrição do lembrete de teste",
            "data_lembrete": future_time,
            "tipo": "contato"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "mensagem" in data
        
        self.created_lembrete_ids.append(data["id"])
        print(f"PASS: Lembrete created with ID: {data['id']}")
    
    def test_create_lembrete_with_reference(self, admin_headers):
        """POST /api/apoio/lembretes - Create reminder with reference"""
        future_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        payload = {
            "titulo": "TEST_Lembrete com referência",
            "descricao": "Seguimento de pedido",
            "data_lembrete": future_time,
            "tipo": "prazo",
            "referencia_id": "some-pedido-id",
            "referencia_tipo": "pedido"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        self.created_lembrete_ids.append(data["id"])
        print(f"PASS: Lembrete with reference created with ID: {data['id']}")
    
    def test_listar_lembretes(self, admin_headers):
        """GET /api/apoio/lembretes - List reminders"""
        response = requests.get(f"{BASE_URL}/api/apoio/lembretes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            lembrete = data[0]
            assert "id" in lembrete
            assert "titulo" in lembrete
            assert "data_lembrete" in lembrete
            assert "concluido" in lembrete
        
        print(f"PASS: Listed {len(data)} lembretes")
    
    def test_listar_lembretes_pendentes(self, admin_headers):
        """GET /api/apoio/lembretes?pendentes=true - List pending reminders"""
        response = requests.get(f"{BASE_URL}/api/apoio/lembretes?pendentes=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for lembrete in data:
            assert lembrete["concluido"] == False
        
        print(f"PASS: Listed {len(data)} pending lembretes")
    
    def test_concluir_lembrete(self, admin_headers):
        """PATCH /api/apoio/lembretes/{id}/concluir - Mark reminder as completed"""
        if not self.created_lembrete_ids:
            pytest.skip("No reminder created to test completion")
        
        lembrete_id = self.created_lembrete_ids[0]
        
        response = requests.patch(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}/concluir", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Lembrete {lembrete_id} marked as completed")
    
    def test_concluir_lembrete_not_found(self, admin_headers):
        """PATCH /api/apoio/lembretes/{id}/concluir - 404 for non-existent reminder"""
        response = requests.patch(f"{BASE_URL}/api/apoio/lembretes/non-existent-id/concluir", headers=admin_headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent lembrete")
    
    def test_delete_lembrete(self, admin_headers):
        """DELETE /api/apoio/lembretes/{id} - Remove reminder"""
        if not self.created_lembrete_ids:
            pytest.skip("No reminder created to test deletion")
        
        lembrete_id = self.created_lembrete_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Lembrete {lembrete_id} deleted successfully")
    
    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, admin_headers):
        """Cleanup test lembretes after all tests"""
        yield
        for lembrete_id in self.created_lembrete_ids:
            requests.delete(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}", headers=admin_headers)


class TestBaseConhecimento:
    """Test Base de Conhecimento (Knowledge Base) CRUD operations"""
    
    created_artigo_ids = []
    
    def test_get_categorias(self, admin_headers):
        """GET /api/apoio/conhecimento/categorias - List categories"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/categorias", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Validate category structure
        for cat in data:
            assert "value" in cat
            assert "label" in cat
            assert "icone" in cat
        
        categories = [c["value"] for c in data]
        assert "procedimento" in categories
        assert "faq" in categories
        assert "documento" in categories
        assert "dica" in categories
        assert "contato" in categories
        
        print(f"PASS: Listed {len(data)} knowledge base categories")
    
    def test_create_artigo_admin(self, admin_headers):
        """POST /api/apoio/conhecimento - Admin can create article"""
        payload = {
            "titulo": "TEST_Procedimento de Matrícula",
            "conteudo": "## Passo a Passo\n\n1. Acesse o sistema\n2. Clique em Nova Matrícula\n3. Preencha os dados\n\nPara mais informações, consulte o manual.",
            "resumo": "Guia completo de como realizar matrícula",
            "categoria": "procedimento",
            "tags": "matrícula,guia,passo-a-passo",
            "destaque": True
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["titulo"] == "TEST_Procedimento de Matrícula"
        assert "mensagem" in data
        
        self.created_artigo_ids.append(data["id"])
        print(f"PASS: Artigo created with ID: {data['id']}")
    
    def test_create_artigo_assistente_forbidden(self, assistente_headers):
        """POST /api/apoio/conhecimento - Assistente cannot create article"""
        payload = {
            "titulo": "TEST_Artigo não autorizado",
            "conteudo": "Conteúdo de teste que não deve ser criado",
            "categoria": "dica"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=assistente_headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from creating articles (403)")
    
    def test_listar_artigos(self, admin_headers):
        """GET /api/apoio/conhecimento - List articles"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            artigo = data[0]
            assert "id" in artigo
            assert "titulo" in artigo
            assert "categoria" in artigo
            assert "visualizacoes" in artigo
        
        print(f"PASS: Listed {len(data)} artigos")
    
    def test_listar_artigos_by_categoria(self, admin_headers):
        """GET /api/apoio/conhecimento?categoria=procedimento - Filter by category"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?categoria=procedimento", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for artigo in data:
            assert artigo["categoria"] == "procedimento"
        
        print(f"PASS: Listed {len(data)} artigos with categoria=procedimento")
    
    def test_listar_artigos_busca(self, admin_headers):
        """GET /api/apoio/conhecimento?busca=matrícula - Search articles"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?busca=matrícula", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        print(f"PASS: Search returned {len(data)} artigos for 'matrícula'")
    
    def test_listar_artigos_destaque(self, admin_headers):
        """GET /api/apoio/conhecimento?destaque=true - List featured articles"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?destaque=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for artigo in data:
            assert artigo["destaque"] == True
        
        print(f"PASS: Listed {len(data)} featured artigos")
    
    def test_buscar_artigo(self, admin_headers):
        """GET /api/apoio/conhecimento/{id} - Get specific article"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids[0]
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == artigo_id
        assert "titulo" in data
        assert "conteudo" in data
        assert "resumo" in data
        assert "categoria" in data
        assert "tags" in data
        assert "visualizacoes" in data
        assert "created_at" in data
        
        print(f"PASS: Retrieved artigo {artigo_id} with {data['visualizacoes']} views")
    
    def test_buscar_artigo_not_found(self, admin_headers):
        """GET /api/apoio/conhecimento/{id} - 404 for non-existent article"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/non-existent-id", headers=admin_headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent artigo")
    
    def test_assistente_can_view_artigo(self, assistente_headers):
        """GET /api/apoio/conhecimento/{id} - Assistente can view articles"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids[0]
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=assistente_headers)
        assert response.status_code == 200
        print("PASS: Assistente can view artigos")
    
    def test_update_artigo_admin(self, admin_headers):
        """PUT /api/apoio/conhecimento/{id} - Admin can update article"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids[0]
        payload = {
            "titulo": "TEST_Procedimento de Matrícula Atualizado",
            "conteudo": "## Passo a Passo Atualizado\n\n1. Acesse o sistema\n2. Clique em Nova Matrícula\n3. Preencha os dados do aluno\n4. Confirme a matrícula\n\nAtualizado!",
            "resumo": "Guia atualizado de matrícula",
            "categoria": "procedimento",
            "tags": "matrícula,guia,passo-a-passo,atualizado",
            "destaque": True
        }
        
        response = requests.put(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        
        # Verify update
        get_response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=admin_headers)
        updated = get_response.json()
        assert "Atualizado" in updated["titulo"]
        
        print(f"PASS: Artigo {artigo_id} updated successfully")
    
    def test_update_artigo_assistente_forbidden(self, assistente_headers):
        """PUT /api/apoio/conhecimento/{id} - Assistente cannot update article"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids[0]
        payload = {
            "titulo": "TEST_Tentativa de atualização",
            "conteudo": "Conteúdo não autorizado",
            "categoria": "procedimento"
        }
        
        response = requests.put(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", json=payload, headers=assistente_headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from updating articles (403)")
    
    def test_delete_artigo_assistente_forbidden(self, assistente_headers):
        """DELETE /api/apoio/conhecimento/{id} - Assistente cannot delete article"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids[0]
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=assistente_headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from deleting articles (403)")
    
    def test_delete_artigo_admin(self, admin_headers):
        """DELETE /api/apoio/conhecimento/{id} - Admin can delete article"""
        if not self.created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = self.created_artigo_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Artigo {artigo_id} deleted by admin")
    
    def test_delete_artigo_not_found(self, admin_headers):
        """DELETE /api/apoio/conhecimento/{id} - 404 for non-existent article"""
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/non-existent-id", headers=admin_headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent artigo deletion")
    
    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, admin_headers):
        """Cleanup test artigos after all tests"""
        yield
        for artigo_id in self.created_artigo_ids:
            requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=admin_headers)


class TestValidation:
    """Test input validation for apoio cognitivo endpoints"""
    
    def test_tarefa_titulo_required(self, admin_headers):
        """POST /api/apoio/tarefas - Titulo is required"""
        payload = {
            "descricao": "Descrição sem título",
            "categoria": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=admin_headers)
        assert response.status_code == 422  # Validation error
        print("PASS: Tarefa requires titulo field")
    
    def test_tarefa_titulo_min_length(self, admin_headers):
        """POST /api/apoio/tarefas - Titulo min length = 2"""
        payload = {
            "titulo": "A",  # Too short
            "categoria": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=admin_headers)
        assert response.status_code == 422
        print("PASS: Tarefa titulo must be at least 2 characters")
    
    def test_artigo_conteudo_min_length(self, admin_headers):
        """POST /api/apoio/conhecimento - Conteudo min length = 10"""
        payload = {
            "titulo": "TEST_Titulo válido",
            "conteudo": "Curto",  # Too short (less than 10)
            "categoria": "dica"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=admin_headers)
        assert response.status_code == 422
        print("PASS: Artigo conteudo must be at least 10 characters")
    
    def test_lembrete_data_required(self, admin_headers):
        """POST /api/apoio/lembretes - data_lembrete is required"""
        payload = {
            "titulo": "TEST_Lembrete sem data",
            "tipo": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=admin_headers)
        assert response.status_code == 422
        print("PASS: Lembrete requires data_lembrete field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
