"""
Iteration 20 - Test all features requested in review:
- Painel de Vagas: Criar período vazio, dashboard, nova turma, duplicar período
- Apoio Cognitivo: Meu Dia (tarefas CRUD), Lembretes, Base de Conhecimento
- Reembolsos: Listar
- Pendências: Listar
- Contatos: Tipos, Resultados, Motivos
- Auth: Login
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "pedro.passos@fieb.org.br"
TEST_PASSWORD = "Pedro@2026"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD  # Portuguese field name
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "usuario" in data, "No usuario in response"
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "senha": "WrongPassword"
        })
        assert response.status_code in [401, 404], f"Expected 401/404, got {response.status_code}"
        print("✓ Invalid credentials rejected correctly")


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "senha": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPainelVagas:
    """Painel de Vagas module tests"""
    
    def test_listar_periodos(self, auth_headers):
        """Test GET /api/painel-vagas/periodos"""
        response = requests.get(f"{BASE_URL}/api/painel-vagas/periodos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "periodos" in data
        print(f"✓ Períodos listados: {len(data['periodos'])} períodos")
        return data["periodos"]
    
    def test_dashboard(self, auth_headers):
        """Test GET /api/painel-vagas/dashboard"""
        response = requests.get(f"{BASE_URL}/api/painel-vagas/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "resumo" in data
        assert "por_curso" in data
        assert "por_turno" in data
        assert "alertas" in data
        # Validate resumo structure
        resumo = data["resumo"]
        assert "total_turmas" in resumo
        assert "total_vagas" in resumo
        assert "total_ocupadas" in resumo
        assert "vagas_disponiveis" in resumo
        assert "percentual_ocupacao" in resumo
        print(f"✓ Dashboard: {resumo['total_turmas']} turmas, {resumo['total_vagas']} vagas")
        return data
    
    def test_dashboard_por_periodo(self, auth_headers):
        """Test GET /api/painel-vagas/dashboard with specific periodo"""
        # First get a period
        periodos_resp = requests.get(f"{BASE_URL}/api/painel-vagas/periodos", headers=auth_headers)
        periodos = periodos_resp.json().get("periodos", [])
        if periodos:
            response = requests.get(
                f"{BASE_URL}/api/painel-vagas/dashboard",
                params={"periodo": periodos[0]},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Dashboard para período {periodos[0]}: {data['resumo']['total_turmas']} turmas")
    
    def test_listar_turmas(self, auth_headers):
        """Test GET /api/painel-vagas/turmas"""
        response = requests.get(f"{BASE_URL}/api/painel-vagas/turmas", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "turmas" in data
        assert "total" in data
        print(f"✓ Turmas listadas: {data['total']} turmas")
    
    def test_criar_turma(self, auth_headers):
        """Test POST /api/painel-vagas/turmas - Criar Nova Turma"""
        turma_codigo = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        response = requests.post(
            f"{BASE_URL}/api/painel-vagas/turmas",
            params={
                "codigo_turma": turma_codigo,
                "nome_curso": "TEST Curso de Teste",
                "turno": "NOTURNO",
                "vagas_totais": 30,
                "vagas_ocupadas": 5,
                "periodo_letivo": "2026.1",
                "modalidade": "CHP"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["message"] in ["Turma criada", "Turma atualizada"]
        print(f"✓ Turma criada com código {turma_codigo}")
        return data["id"]
    
    def test_criar_periodo_vazio_bug_fix(self, auth_headers):
        """Test POST /api/painel-vagas/duplicar-periodo - Criar período vazio (BUG FIX)"""
        # This is the main bug fix being tested
        periodo_destino = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}.1"
        
        response = requests.post(
            f"{BASE_URL}/api/painel-vagas/duplicar-periodo",
            params={
                "periodo_destino": periodo_destino
                # Note: NO periodo_origem - this should create empty period
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"BUG FIX FAILED - Creating empty period should work: {response.text}"
        data = response.json()
        assert "message" in data
        assert data["turmas_criadas"] == 0, "Empty period should have 0 turmas"
        assert data["periodo_destino"] == periodo_destino
        
        # Verify period appears in list
        periodos_resp = requests.get(f"{BASE_URL}/api/painel-vagas/periodos", headers=auth_headers)
        periodos = periodos_resp.json().get("periodos", [])
        assert periodo_destino in periodos, f"BUG FIX FAILED - Empty period {periodo_destino} not in list"
        
        print(f"✓ BUG FIX VERIFIED: Período vazio {periodo_destino} criado e aparece na lista!")
        return periodo_destino
    
    def test_duplicar_periodo_com_turmas(self, auth_headers):
        """Test POST /api/painel-vagas/duplicar-periodo with origem"""
        # First get existing periods
        periodos_resp = requests.get(f"{BASE_URL}/api/painel-vagas/periodos", headers=auth_headers)
        periodos = periodos_resp.json().get("periodos", [])
        
        # Find a period that has turmas
        turmas_resp = requests.get(f"{BASE_URL}/api/painel-vagas/turmas", headers=auth_headers)
        turmas = turmas_resp.json().get("turmas", [])
        
        periodo_com_turmas = None
        for p in periodos:
            turmas_periodo = [t for t in turmas if t.get("periodo_letivo") == p]
            if turmas_periodo:
                periodo_com_turmas = p
                break
        
        if not periodo_com_turmas:
            pytest.skip("No period with turmas found to test duplication")
        
        periodo_destino = f"TEST_DUP_{datetime.now().strftime('%Y%m%d%H%M%S')}.2"
        
        response = requests.post(
            f"{BASE_URL}/api/painel-vagas/duplicar-periodo",
            params={
                "periodo_origem": periodo_com_turmas,
                "periodo_destino": periodo_destino
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to duplicate: {response.text}"
        data = response.json()
        assert data["turmas_criadas"] > 0, "Should have duplicated turmas"
        print(f"✓ Duplicou {data['turmas_criadas']} turmas de {periodo_com_turmas} para {periodo_destino}")
    
    def test_duplicar_periodo_conflito(self, auth_headers):
        """Test duplicating to existing period with turmas should fail"""
        turmas_resp = requests.get(f"{BASE_URL}/api/painel-vagas/turmas", headers=auth_headers)
        turmas = turmas_resp.json().get("turmas", [])
        
        if not turmas:
            pytest.skip("No turmas to test conflict")
        
        existing_periodo = turmas[0].get("periodo_letivo")
        
        response = requests.post(
            f"{BASE_URL}/api/painel-vagas/duplicar-periodo",
            params={
                "periodo_destino": existing_periodo
            },
            headers=auth_headers
        )
        
        assert response.status_code == 409, f"Expected 409 conflict, got {response.status_code}"
        print(f"✓ Corretamente rejeitou duplicação para período existente {existing_periodo}")


class TestApoioCognitivo:
    """Apoio Cognitivo - Meu Dia, Tarefas, Lembretes, Base de Conhecimento"""
    
    def test_meu_dia(self, auth_headers):
        """Test GET /api/apoio/meu-dia"""
        response = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "tarefas" in data
        assert "lembretes" in data
        assert "estatisticas" in data
        assert "saudacao" in data
        print(f"✓ Meu Dia: {len(data['tarefas'])} tarefas, {len(data['lembretes'])} lembretes, saudação: {data['saudacao']}")
    
    def test_criar_tarefa(self, auth_headers):
        """Test POST /api/apoio/tarefas"""
        tarefa_titulo = f"TEST_Tarefa_{uuid.uuid4().hex[:6]}"
        response = requests.post(
            f"{BASE_URL}/api/apoio/tarefas",
            json={
                "titulo": tarefa_titulo,
                "descricao": "Tarefa de teste",
                "categoria": "outro",
                "prioridade": 2,
                "recorrente": False,
                "data_tarefa": datetime.now().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["titulo"] == tarefa_titulo
        assert data["concluida"] == False
        assert "_id" not in data, "MongoDB _id should not be in response"
        print(f"✓ Tarefa criada: {tarefa_titulo}")
        return data["id"]
    
    def test_toggle_tarefa(self, auth_headers):
        """Test PATCH /api/apoio/tarefas/{id}/toggle - marcar como concluída"""
        # Create a task first
        tarefa_titulo = f"TEST_Toggle_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(
            f"{BASE_URL}/api/apoio/tarefas",
            json={"titulo": tarefa_titulo, "categoria": "outro"},
            headers=auth_headers
        )
        tarefa_id = create_resp.json()["id"]
        
        # Toggle to complete
        response = requests.patch(
            f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}/toggle",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["concluida"] == True
        print(f"✓ Tarefa marcada como concluída")
        
        # Toggle back to incomplete
        response2 = requests.patch(
            f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}/toggle",
            headers=auth_headers
        )
        assert response2.json()["concluida"] == False
        print(f"✓ Tarefa desmarcada")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}", headers=auth_headers)
    
    def test_deletar_tarefa(self, auth_headers):
        """Test DELETE /api/apoio/tarefas/{id}"""
        # Create
        create_resp = requests.post(
            f"{BASE_URL}/api/apoio/tarefas",
            json={"titulo": f"TEST_Delete_{uuid.uuid4().hex[:6]}", "categoria": "outro"},
            headers=auth_headers
        )
        tarefa_id = create_resp.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Tarefa deletada")
    
    def test_criar_lembrete(self, auth_headers):
        """Test POST /api/apoio/lembretes"""
        data_lembrete = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
        response = requests.post(
            f"{BASE_URL}/api/apoio/lembretes",
            json={
                "titulo": f"TEST_Lembrete_{uuid.uuid4().hex[:6]}",
                "descricao": "Lembrete de teste",
                "data_lembrete": data_lembrete,
                "tipo": "outro"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "_id" not in data, "MongoDB _id should not be in response"
        print(f"✓ Lembrete criado")
        return data["id"]
    
    def test_listar_lembretes(self, auth_headers):
        """Test GET /api/apoio/lembretes"""
        response = requests.get(f"{BASE_URL}/api/apoio/lembretes", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "lembretes" in data
        assert "total" in data
        print(f"✓ Lembretes listados: {data['total']}")
    
    def test_concluir_lembrete(self, auth_headers):
        """Test PATCH /api/apoio/lembretes/{id}/concluir"""
        # Create lembrete first
        data_lembrete = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
        create_resp = requests.post(
            f"{BASE_URL}/api/apoio/lembretes",
            json={"titulo": f"TEST_Concluir_{uuid.uuid4().hex[:6]}", "data_lembrete": data_lembrete},
            headers=auth_headers
        )
        lembrete_id = create_resp.json()["id"]
        
        # Concluir
        response = requests.patch(
            f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}/concluir",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Lembrete concluído")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/apoio/lembretes/{lembrete_id}", headers=auth_headers)


class TestBaseConhecimento:
    """Base de Conhecimento tests"""
    
    def test_listar_artigos(self, auth_headers):
        """Test GET /api/apoio/conhecimento"""
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "artigos" in data
        assert "total" in data
        assert "categorias" in data
        print(f"✓ Base de Conhecimento: {data['total']} artigos")
    
    def test_criar_artigo(self, auth_headers):
        """Test POST /api/apoio/conhecimento"""
        artigo_titulo = f"TEST_Artigo_{uuid.uuid4().hex[:6]}"
        response = requests.post(
            f"{BASE_URL}/api/apoio/conhecimento",
            json={
                "titulo": artigo_titulo,
                "conteudo": "Este é o conteúdo do artigo de teste para verificar a criação na base de conhecimento.",
                "resumo": "Resumo do artigo de teste",
                "categoria": "procedimento",
                "tags": "teste, automacao",
                "destaque": False
            },
            headers=auth_headers
        )
        assert response.status_code == 201, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["titulo"] == artigo_titulo
        assert "_id" not in data, "MongoDB _id should not be in response"
        print(f"✓ Artigo criado: {artigo_titulo}")
        return data["id"]
    
    def test_visualizar_artigo(self, auth_headers):
        """Test GET /api/apoio/conhecimento/{id}"""
        # Create an article first
        create_resp = requests.post(
            f"{BASE_URL}/api/apoio/conhecimento",
            json={
                "titulo": f"TEST_Visualizar_{uuid.uuid4().hex[:6]}",
                "conteudo": "Conteúdo para teste de visualização do artigo na base de conhecimento.",
                "categoria": "dica"
            },
            headers=auth_headers
        )
        artigo_id = create_resp.json()["id"]
        
        # Get the article
        response = requests.get(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == artigo_id
        print(f"✓ Artigo visualizado")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=auth_headers)


class TestReembolsos:
    """Reembolsos module tests"""
    
    def test_listar_reembolsos(self, auth_headers):
        """Test GET /api/reembolsos"""
        response = requests.get(f"{BASE_URL}/api/reembolsos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "reembolsos" in data
        assert "paginacao" in data
        print(f"✓ Reembolsos listados: {data['paginacao']['total_itens']} itens")
    
    def test_dashboard_reembolsos(self, auth_headers):
        """Test GET /api/reembolsos/dashboard"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "contagem_status" in data
        print(f"✓ Dashboard Reembolsos: {data['total']} total")
    
    def test_motivos_reembolso(self, auth_headers):
        """Test GET /api/reembolsos/motivos"""
        response = requests.get(f"{BASE_URL}/api/reembolsos/motivos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Motivos de reembolso: {len(data)} motivos")


class TestPendencias:
    """Pendências module tests"""
    
    def test_listar_pendencias(self, auth_headers):
        """Test GET /api/pendencias"""
        response = requests.get(f"{BASE_URL}/api/pendencias", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "pendencias" in data
        assert "total" in data
        assert "paginacao" in data
        print(f"✓ Pendências listadas: {data['total']} itens")
    
    def test_dashboard_pendencias(self, auth_headers):
        """Test GET /api/pendencias/dashboard"""
        response = requests.get(f"{BASE_URL}/api/pendencias/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "por_status" in data
        print(f"✓ Dashboard Pendências: {data['total']} total")


class TestContatos:
    """Contatos module tests"""
    
    def test_tipos_contato(self, auth_headers):
        """Test GET /api/contatos/tipos"""
        response = requests.get(f"{BASE_URL}/api/contatos/tipos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Tipos de contato: {len(data)} tipos")
    
    def test_resultados_contato(self, auth_headers):
        """Test GET /api/contatos/resultados"""
        response = requests.get(f"{BASE_URL}/api/contatos/resultados", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Resultados de contato: {len(data)} opções")
    
    def test_motivos_contato(self, auth_headers):
        """Test GET /api/contatos/motivos"""
        response = requests.get(f"{BASE_URL}/api/contatos/motivos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Motivos de contato: {len(data)} opções")


class TestDashboardPrincipal:
    """Dashboard principal tests"""
    
    def test_resumo_pedidos(self, auth_headers):
        """Test if pedidos endpoint exists and returns data"""
        response = requests.get(f"{BASE_URL}/api/pedidos/dashboard", headers=auth_headers)
        if response.status_code == 404:
            # Try alternative endpoint
            response = requests.get(f"{BASE_URL}/api/pedidos", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Dashboard principal acessível")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
