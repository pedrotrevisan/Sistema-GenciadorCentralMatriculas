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

# Store created IDs for cleanup
created_task_ids = []
created_lembrete_ids = []
created_artigo_ids = []


def get_admin_headers():
    """Get admin authentication headers"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    return None


def get_assistente_headers():
    """Get assistente authentication headers"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ASSISTENTE_CREDENTIALS)
    if response.status_code == 200:
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    return None


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


class TestMeuDia:
    """Test Meu Dia endpoint - daily summary"""
    
    def test_get_meu_dia(self):
        """GET /api/apoio/meu-dia - Returns daily summary"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=headers)
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
    
    def test_meu_dia_assistente(self):
        """Test assistente can access meu-dia"""
        headers = get_assistente_headers()
        assert headers is not None, "Failed to get assistente auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "saudacao" in data
        print("PASS: Assistente can access Meu Dia")


class TestTarefas:
    """Test Tarefas (Tasks) CRUD operations"""
    
    def test_create_tarefa(self):
        """POST /api/apoio/tarefas - Create new task"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
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
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["titulo"] == "TEST_Tarefa de teste automatizado"
        assert "mensagem" in data
        
        created_task_ids.append(data["id"])
        print(f"PASS: Tarefa created with ID: {data['id']}")
    
    def test_create_recurrent_tarefa(self):
        """POST /api/apoio/tarefas - Create recurrent task"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "titulo": "TEST_Tarefa recorrente",
            "descricao": "Tarefa que repete todos os dias",
            "categoria": "lembrete",
            "prioridade": 2,
            "recorrente": True,
            "dias_semana": "1,2,3,4,5"  # Monday to Friday
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        created_task_ids.append(data["id"])
        print(f"PASS: Recurrent tarefa created with ID: {data['id']}")
    
    def test_listar_tarefas(self):
        """GET /api/apoio/tarefas - List all tasks"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas", headers=headers)
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
    
    def test_listar_tarefas_by_date(self):
        """GET /api/apoio/tarefas?data=YYYY-MM-DD - Filter by date"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas?data={today}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Listed {len(data)} tarefas for today")
    
    def test_listar_tarefas_by_categoria(self):
        """GET /api/apoio/tarefas?categoria=rotina - Filter by category"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/tarefas?categoria=rotina", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for task in data:
            assert task["categoria"] == "rotina"
        print(f"PASS: Listed {len(data)} tarefas with categoria=rotina")
    
    def test_concluir_tarefa(self):
        """PATCH /api/apoio/tarefas/{id}/concluir - Toggle task completion"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_task_ids:
            pytest.skip("No task created to test completion")
        
        task_id = created_task_ids[0]
        
        # First toggle - mark as completed
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/{task_id}/concluir", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "concluida" in data
        assert data["concluida"] == True
        print(f"PASS: Task {task_id} marked as completed")
        
        # Second toggle - mark as not completed
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/{task_id}/concluir", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["concluida"] == False
        print(f"PASS: Task {task_id} marked as not completed (toggled)")
    
    def test_concluir_tarefa_not_found(self):
        """PATCH /api/apoio/tarefas/{id}/concluir - 404 for non-existent task"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.patch(f"{BASE_URL}/api/apoio/tarefas/non-existent-id/concluir", headers=headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent task")
    
    def test_delete_tarefa(self):
        """DELETE /api/apoio/tarefas/{id} - Remove task"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_task_ids:
            pytest.skip("No task created to test deletion")
        
        task_id = created_task_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/tarefas/{task_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Task {task_id} deleted successfully")
    
    def test_delete_tarefa_not_found(self):
        """DELETE /api/apoio/tarefas/{id} - 404 for non-existent task"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.delete(f"{BASE_URL}/api/apoio/tarefas/non-existent-id", headers=headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent task deletion")


class TestLembretes:
    """Test Lembretes (Reminders) CRUD operations"""
    
    def test_create_lembrete(self):
        """POST /api/apoio/lembretes - Create new reminder"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        # Set reminder for 1 hour from now
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        payload = {
            "titulo": "TEST_Lembrete de teste",
            "descricao": "Descrição do lembrete de teste",
            "data_lembrete": future_time,
            "tipo": "contato"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "mensagem" in data
        
        created_lembrete_ids.append(data["id"])
        print(f"PASS: Lembrete created with ID: {data['id']}")
    
    def test_create_lembrete_with_reference(self):
        """POST /api/apoio/lembretes - Create reminder with reference"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        future_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        payload = {
            "titulo": "TEST_Lembrete com referência",
            "descricao": "Seguimento de pedido",
            "data_lembrete": future_time,
            "tipo": "prazo",
            "referencia_id": "some-pedido-id",
            "referencia_tipo": "pedido"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        created_lembrete_ids.append(data["id"])
        print(f"PASS: Lembrete with reference created with ID: {data['id']}")
    
    def test_listar_lembretes(self):
        """GET /api/apoio/lembretes - List reminders"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/lembretes", headers=headers)
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
    
    def test_listar_lembretes_pendentes(self):
        """GET /api/apoio/lembretes?pendentes=true - List pending reminders"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/lembretes?pendentes=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        for lembrete in data:
            assert lembrete["concluido"] == False
        
        print(f"PASS: Listed {len(data)} pending lembretes")
    
    def test_concluir_lembrete(self):
        """PATCH /api/apoio/lembretes/{id}/concluir - Mark reminder as completed"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_lembrete_ids:
            pytest.skip("No reminder created to test completion")
        
        lembrete_id = created_lembrete_ids[0]
        
        response = requests.patch(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}/concluir", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Lembrete {lembrete_id} marked as completed")
    
    def test_concluir_lembrete_not_found(self):
        """PATCH /api/apoio/lembretes/{id}/concluir - 404 for non-existent reminder"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.patch(f"{BASE_URL}/api/apoio/lembretes/non-existent-id/concluir", headers=headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent lembrete")
    
    def test_delete_lembrete(self):
        """DELETE /api/apoio/lembretes/{id} - Remove reminder"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_lembrete_ids:
            pytest.skip("No reminder created to test deletion")
        
        lembrete_id = created_lembrete_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Lembrete {lembrete_id} deleted successfully")


class TestBaseConhecimento:
    """Test Base de Conhecimento (Knowledge Base) CRUD operations"""
    
    def test_get_categorias(self):
        """GET /api/apoio/conhecimento/categorias - List categories"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/categorias", headers=headers)
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
    
    def test_create_artigo_admin(self):
        """POST /api/apoio/conhecimento - Admin can create article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "titulo": "TEST_Procedimento de Matrícula",
            "conteudo": "## Passo a Passo\n\n1. Acesse o sistema\n2. Clique em Nova Matrícula\n3. Preencha os dados\n\nPara mais informações, consulte o manual.",
            "resumo": "Guia completo de como realizar matrícula",
            "categoria": "procedimento",
            "tags": "matrícula,guia,passo-a-passo",
            "destaque": True
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["titulo"] == "TEST_Procedimento de Matrícula"
        assert "mensagem" in data
        
        created_artigo_ids.append(data["id"])
        print(f"PASS: Artigo created with ID: {data['id']}")
    
    def test_create_artigo_assistente_forbidden(self):
        """POST /api/apoio/conhecimento - Assistente cannot create article"""
        headers = get_assistente_headers()
        assert headers is not None, "Failed to get assistente auth token"
        
        payload = {
            "titulo": "TEST_Artigo não autorizado",
            "conteudo": "Conteúdo de teste que não deve ser criado",
            "categoria": "dica"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from creating articles (403)")
    
    def test_listar_artigos(self):
        """GET /api/apoio/conhecimento - List articles"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento", headers=headers)
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
    
    def test_listar_artigos_by_categoria(self):
        """GET /api/apoio/conhecimento?categoria=procedimento - Filter by category"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?categoria=procedimento", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        for artigo in data:
            assert artigo["categoria"] == "procedimento"
        
        print(f"PASS: Listed {len(data)} artigos with categoria=procedimento")
    
    def test_listar_artigos_busca(self):
        """GET /api/apoio/conhecimento?busca=matrícula - Search articles"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?busca=matrícula", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        print(f"PASS: Search returned {len(data)} artigos for 'matrícula'")
    
    def test_listar_artigos_destaque(self):
        """GET /api/apoio/conhecimento?destaque=true - List featured articles"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento?destaque=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        for artigo in data:
            assert artigo["destaque"] == True
        
        print(f"PASS: Listed {len(data)} featured artigos")
    
    def test_buscar_artigo(self):
        """GET /api/apoio/conhecimento/{id} - Get specific article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids[0]
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
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
    
    def test_buscar_artigo_not_found(self):
        """GET /api/apoio/conhecimento/{id} - 404 for non-existent article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/non-existent-id", headers=headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent artigo")
    
    def test_assistente_can_view_artigo(self):
        """GET /api/apoio/conhecimento/{id} - Assistente can view articles"""
        headers = get_assistente_headers()
        assert headers is not None, "Failed to get assistente auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids[0]
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
        assert response.status_code == 200
        print("PASS: Assistente can view artigos")
    
    def test_update_artigo_admin(self):
        """PUT /api/apoio/conhecimento/{id} - Admin can update article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids[0]
        payload = {
            "titulo": "TEST_Procedimento de Matrícula Atualizado",
            "conteudo": "## Passo a Passo Atualizado\n\n1. Acesse o sistema\n2. Clique em Nova Matrícula\n3. Preencha os dados do aluno\n4. Confirme a matrícula\n\nAtualizado!",
            "resumo": "Guia atualizado de matrícula",
            "categoria": "procedimento",
            "tags": "matrícula,guia,passo-a-passo,atualizado",
            "destaque": True
        }
        
        response = requests.put(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        
        # Verify update
        get_response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
        updated = get_response.json()
        assert "Atualizado" in updated["titulo"]
        
        print(f"PASS: Artigo {artigo_id} updated successfully")
    
    def test_update_artigo_assistente_forbidden(self):
        """PUT /api/apoio/conhecimento/{id} - Assistente cannot update article"""
        headers = get_assistente_headers()
        assert headers is not None, "Failed to get assistente auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids[0]
        payload = {
            "titulo": "TEST_Tentativa de atualização",
            "conteudo": "Conteúdo não autorizado",
            "categoria": "procedimento"
        }
        
        response = requests.put(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", json=payload, headers=headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from updating articles (403)")
    
    def test_delete_artigo_assistente_forbidden(self):
        """DELETE /api/apoio/conhecimento/{id} - Assistente cannot delete article"""
        headers = get_assistente_headers()
        assert headers is not None, "Failed to get assistente auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids[0]
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
        assert response.status_code == 403
        print("PASS: Assistente forbidden from deleting articles (403)")
    
    def test_delete_artigo_admin(self):
        """DELETE /api/apoio/conhecimento/{id} - Admin can delete article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        if not created_artigo_ids:
            pytest.skip("No article created to test")
        
        artigo_id = created_artigo_ids.pop()
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "mensagem" in data
        print(f"PASS: Artigo {artigo_id} deleted by admin")
    
    def test_delete_artigo_not_found(self):
        """DELETE /api/apoio/conhecimento/{id} - 404 for non-existent article"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        response = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/non-existent-id", headers=headers)
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent artigo deletion")


class TestValidation:
    """Test input validation for apoio cognitivo endpoints"""
    
    def test_tarefa_titulo_required(self):
        """POST /api/apoio/tarefas - Titulo is required"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "descricao": "Descrição sem título",
            "categoria": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=headers)
        assert response.status_code == 422  # Validation error
        print("PASS: Tarefa requires titulo field")
    
    def test_tarefa_titulo_min_length(self):
        """POST /api/apoio/tarefas - Titulo min length = 2"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "titulo": "A",  # Too short
            "categoria": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/tarefas", json=payload, headers=headers)
        assert response.status_code == 422
        print("PASS: Tarefa titulo must be at least 2 characters")
    
    def test_artigo_conteudo_min_length(self):
        """POST /api/apoio/conhecimento - Conteudo min length = 10"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "titulo": "TEST_Titulo válido",
            "conteudo": "Curto",  # Too short (less than 10)
            "categoria": "dica"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/conhecimento", json=payload, headers=headers)
        assert response.status_code == 422
        print("PASS: Artigo conteudo must be at least 10 characters")
    
    def test_lembrete_data_required(self):
        """POST /api/apoio/lembretes - data_lembrete is required"""
        headers = get_admin_headers()
        assert headers is not None, "Failed to get admin auth token"
        
        payload = {
            "titulo": "TEST_Lembrete sem data",
            "tipo": "outro"
        }
        
        response = requests.post(f"{BASE_URL}/api/apoio/lembretes", json=payload, headers=headers)
        assert response.status_code == 422
        print("PASS: Lembrete requires data_lembrete field")


def test_cleanup():
    """Cleanup test data after all tests"""
    headers = get_admin_headers()
    if not headers:
        return
    
    # Cleanup remaining tasks
    for task_id in created_task_ids:
        try:
            requests.delete(f"{BASE_URL}/api/apoio/tarefas/{task_id}", headers=headers)
        except:
            pass
    
    # Cleanup remaining lembretes
    for lembrete_id in created_lembrete_ids:
        try:
            requests.delete(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}", headers=headers)
        except:
            pass
    
    # Cleanup remaining artigos
    for artigo_id in created_artigo_ids:
        try:
            requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=headers)
        except:
            pass
    
    print("PASS: Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
