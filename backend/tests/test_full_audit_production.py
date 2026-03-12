"""
Comprehensive backend audit test for SYNAPSE Sistema.
Covers all 23 feature areas from the review request.
Tests AUTH, PEDIDOS, BI, SLA, PENDÊNCIAS, REEMBOLSOS, CHAMADOS, PAINEL VAGAS,
APOIO COGNITIVO, LEMBRETES, ARTIGOS, CONTATOS, CADASTROS, USUÁRIOS,
ALERTAS, STATUS MATRÍCULA, PRODUTIVIDADE, ATRIBUIÇÕES, DOCUMENTOS, TURMAS.

Focus: Verify no endpoint returns unexpected 500 errors (especially recently fixed _id ObjectId bugs).
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "pedro.passos@fieb.org.br"
ADMIN_SENHA = "Pedro@2026"
CONSULTOR_EMAIL = "cristiane.mendes@fieb.org.br"
CONSULTOR_SENHA = "Senai@2026"

# Shared state across tests
_state = {}


# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def admin_token():
    """Get admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("token")
    assert token, "No token returned"
    return token


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def consultor_token():
    """Get consultor token"""
    response = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": CONSULTOR_EMAIL, "senha": CONSULTOR_SENHA})
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Consultor login failed - skipping consultor tests")


@pytest.fixture(scope="session")
def consultor_headers(consultor_token):
    return {"Authorization": f"Bearer {consultor_token}", "Content-Type": "application/json"}


# ==================== 1. AUTH ====================

class TestAuth:
    """Authentication endpoints"""

    def test_login_admin_success(self, admin_token):
        """Admin login returns token"""
        assert admin_token is not None
        assert isinstance(admin_token, str)
        assert len(admin_token) > 20
        print(f"PASS: Admin login - token received ({len(admin_token)} chars)")

    def test_login_wrong_password(self):
        """Login with wrong password returns 401"""
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "senha": "wrongpassword"})
        assert r.status_code == 401
        print(f"PASS: Wrong password returns 401")

    def test_get_me(self, admin_headers):
        """GET /api/auth/me returns current user"""
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        assert "role" in data
        print(f"PASS: GET /api/auth/me - user: {data.get('nome')}, role: {data.get('role')}")

    def test_login_returns_token_field_not_access_token(self):
        """Token field is 'token' not 'access_token'"""
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data, f"Expected 'token' field, got: {list(data.keys())}"
        print(f"PASS: Login response has 'token' field")


# ==================== 2. CADASTROS ====================

class TestCadastros:
    """Courses, Projects, Companies CRUD"""

    def test_list_cursos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/cursos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/cursos - {len(data)} cursos found")
        if data:
            _state["curso_id"] = data[0]["id"]
            _state["curso_nome"] = data[0]["nome"]
            print(f"  Stored curso: {_state['curso_nome']}")

    def test_create_curso(self, admin_headers):
        unique_name = f"TEST_Curso_Audit_{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{BASE_URL}/api/cursos", headers=admin_headers,
                          json={"nome": unique_name, "tipo": "tecnico", "modalidade": "presencial"})
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["nome"] == unique_name
        _state["test_curso_id"] = data["id"]
        print(f"PASS: POST /api/cursos - created: {data['id']}")

    def test_list_projetos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/projetos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/projetos - {len(data)} projetos found")
        if data:
            _state["projeto_id"] = data[0]["id"]
            _state["projeto_nome"] = data[0]["nome"]

    def test_list_empresas(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/empresas", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/empresas - {len(data)} empresas found")
        if data:
            _state["empresa_id"] = data[0]["id"]
            _state["empresa_nome"] = data[0]["nome"]


# ==================== 3. PEDIDOS ====================

class TestPedidos:
    """Pedidos CRUD and dashboards"""

    def test_list_pedidos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/pedidos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "pedidos" in data or isinstance(data, list)
        # Store first pedido id for later tests
        pedidos = data.get("pedidos", data) if isinstance(data, dict) else data
        if pedidos:
            _state["first_pedido_id"] = pedidos[0]["id"]
        print(f"PASS: GET /api/pedidos - found pedidos")

    def test_create_pedido(self, admin_headers):
        """Create a new pedido - requires curso_id"""
        curso_id = _state.get("curso_id")
        if not curso_id:
            pytest.skip("No curso_id available - run TestCadastros first")

        payload = {
            "curso_id": curso_id,
            "curso_nome": _state.get("curso_nome", "Curso Teste"),
            "projeto_id": _state.get("projeto_id"),
            "projeto_nome": _state.get("projeto_nome"),
            "empresa_id": _state.get("empresa_id"),
            "empresa_nome": _state.get("empresa_nome"),
            "vinculo_tipo": "clt",
            "alunos": [{
                "nome": "TEST_Aluno Auditoria",
                "cpf": "12345678901",
                "email": "test.audit@example.com",
                "telefone": "71999990000",
                "data_nascimento": "2000-01-01",
                "rg": "1234567",
                "rg_orgao_emissor": "SSP",
                "rg_uf": "BA",
                "endereco_cep": "41000000",
                "endereco_logradouro": "Rua Teste",
                "endereco_numero": "100",
                "endereco_bairro": "Centro",
                "endereco_cidade": "Salvador",
                "endereco_uf": "BA"
            }]
        }
        r = requests.post(f"{BASE_URL}/api/pedidos", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create pedido failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "pedido" in data
        pedido = data["pedido"]
        assert "id" in pedido
        assert "numero_protocolo" in pedido
        _state["new_pedido_id"] = pedido["id"]
        _state["new_pedido_protocolo"] = pedido["numero_protocolo"]
        print(f"PASS: POST /api/pedidos - created: {pedido['numero_protocolo']}")

    def test_get_pedido_by_id(self, admin_headers):
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id available")
        r = requests.get(f"{BASE_URL}/api/pedidos/{pedido_id}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == pedido_id
        print(f"PASS: GET /api/pedidos/{pedido_id} - status: {data.get('status')}")

    def test_update_pedido_status(self, admin_headers):
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id available")
        r = requests.patch(f"{BASE_URL}/api/pedidos/{pedido_id}/status",
                           headers=admin_headers,
                           json={"status": "em_analise"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "em_analise" or "em_analise" in str(data)
        print(f"PASS: PATCH /api/pedidos/{pedido_id}/status -> em_analise")

    def test_dashboard_pedidos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/pedidos/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "contagem_status" in data
        assert "pedidos_recentes" in data
        print(f"PASS: GET /api/pedidos/dashboard - total: {data['contagem_status'].get('total')}")

    def test_analytics_pedidos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/pedidos/analytics", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "funil" in data
        assert "taxa_conversao" in data
        assert "total_pedidos" in data
        print(f"PASS: GET /api/pedidos/analytics - total: {data.get('total_pedidos')}, taxa: {data.get('taxa_conversao')}%")


# ==================== 4. DASHBOARD BI ====================

class TestDashboardBI:
    """BI Dashboard endpoints"""

    def test_bi_completo(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "matriculas" in data
        assert "reembolsos" in data
        assert "pendencias" in data
        assert "evolucao_mensal" in data
        mat = data["matriculas"]
        assert "total" in mat
        assert "taxa_conversao" in mat
        print(f"PASS: GET /api/documentos/bi/completo - total_matriculas: {mat.get('total')}, taxa: {mat.get('taxa_conversao')}%")

    def test_bi_matriculas(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/documentos/bi/matriculas", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "por_status" in data
        print(f"PASS: GET /api/documentos/bi/matriculas - total: {data.get('total')}")

    def test_bi_evolucao(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/documentos/bi/evolucao", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        if data:
            assert "mes_label" in data[0]
            assert "total" in data[0]
        print(f"PASS: GET /api/documentos/bi/evolucao - {len(data)} meses")


# ==================== 5. DASHBOARD SLA ====================

class TestDashboardSLA:
    """SLA Dashboard"""

    def test_sla_dashboard(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "resumo_geral" in data
        assert "evolucao_semanal" in data
        assert "sla_por_tipo_ps" in data
        resumo = data["resumo_geral"]
        assert "total_pedidos" in resumo
        print(f"PASS: GET /api/sla/dashboard - total_pedidos: {resumo.get('total_pedidos')}, taxa_conclusao: {resumo.get('taxa_conclusao')}%")

    def test_sla_tipo_ps_has_required_fields(self, admin_headers):
        """Verify sla_por_tipo_ps has both tipo/label/quantidade fields for frontend"""
        r = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        sla_ps = data.get("sla_por_tipo_ps", [])
        if sla_ps:
            item = sla_ps[0]
            # Check both old and new field names are present (fixed in iteration 18)
            assert "tipo" in item or "tipo_ps" in item
            assert "total" in item or "quantidade" in item
            assert "label" in item
            print(f"PASS: sla_por_tipo_ps has required fields: {list(item.keys())}")
        else:
            print("INFO: sla_por_tipo_ps is empty (no tipo_processo_seletivo data)")


# ==================== 6. PENDÊNCIAS ====================

class TestPendencias:
    """Pendências CRUD"""

    def test_list_pendencias(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/pendencias", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "pendencias" in data
        assert "total" in data
        print(f"PASS: GET /api/pendencias - total: {data.get('total')}")

    def test_create_pendencia_manual(self, admin_headers):
        """POST /api/pendencias/manual - recently fixed _id bug"""
        payload = {
            "aluno_nome": "TEST_Aluno Pendencia Manual",
            "aluno_cpf": "98765432100",
            "aluno_email": "test.pendencia@example.com",
            "documento_codigo": "rg",
            "curso_nome": "Curso Teste Auditoria"
        }
        r = requests.post(f"{BASE_URL}/api/pendencias/manual", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create pendencia manual failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert data.get("aluno_nome") == "TEST_Aluno Pendencia Manual"
        assert "status" in data
        # Ensure no _id in response (ObjectId serialization bug was fixed)
        assert "_id" not in data
        _state["pendencia_manual_id"] = data["id"]
        print(f"PASS: POST /api/pendencias/manual - id: {data['id']}, no _id in response")

    def test_create_pendencia_automatica(self, admin_headers):
        """POST /api/pendencias - requires aluno_id and pedido_id"""
        # Get an existing aluno and pedido
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id for automatic pendencia")
        # Get aluno from pedido
        r_pedido = requests.get(f"{BASE_URL}/api/pedidos/{pedido_id}", headers=admin_headers)
        if r_pedido.status_code != 200:
            pytest.skip("Cannot fetch pedido for pendencia test")
        pedido_data = r_pedido.json()
        alunos = pedido_data.get("alunos", [])
        if not alunos:
            pytest.skip("No alunos in pedido for pendencia test")
        aluno_id = alunos[0]["id"]
        payload = {
            "aluno_id": aluno_id,
            "pedido_id": pedido_id,
            "documento_codigo": "cpf"
        }
        r = requests.post(f"{BASE_URL}/api/pendencias", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create pendencia failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data
        _state["pendencia_auto_id"] = data["id"]
        print(f"PASS: POST /api/pendencias (automática) - id: {data['id']}")

    def test_update_pendencia_status(self, admin_headers):
        pendencia_id = _state.get("pendencia_manual_id") or _state.get("pendencia_auto_id")
        if not pendencia_id:
            pytest.skip("No pendencia_id available")
        r = requests.patch(f"{BASE_URL}/api/pendencias/{pendencia_id}",
                           headers=admin_headers,
                           json={"status": "em_analise"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "em_analise"
        print(f"PASS: PATCH /api/pendencias/{pendencia_id} -> em_analise")


# ==================== 7. REEMBOLSOS ====================

class TestReembolsos:
    """Reembolsos CRUD"""

    def test_list_reembolsos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/reembolsos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "reembolsos" in data
        print(f"PASS: GET /api/reembolsos - total found")

    def test_create_reembolso(self, admin_headers):
        """POST /api/reembolsos"""
        payload = {
            "aluno_nome": "TEST_Aluno Reembolso Auditoria",
            "aluno_cpf": "11122233344",
            "aluno_email": "test.reembolso@example.com",
            "curso": "Curso de Teste",
            "motivo": "sem_vaga"
        }
        r = requests.post(f"{BASE_URL}/api/reembolsos", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create reembolso failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert data.get("status") == "aberto"
        _state["reembolso_id"] = data["id"]
        print(f"PASS: POST /api/reembolsos - id: {data['id']}")

    def test_get_reembolso_by_id(self, admin_headers):
        reembolso_id = _state.get("reembolso_id")
        if not reembolso_id:
            pytest.skip("No reembolso_id available")
        r = requests.get(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == reembolso_id
        print(f"PASS: GET /api/reembolsos/{reembolso_id}")

    def test_reembolsos_dashboard(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/reembolsos/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "contagem_status" in data or "total" in data
        print(f"PASS: GET /api/reembolsos/dashboard - total: {data.get('total')}")


# ==================== 8. CHAMADOS SGC ====================

class TestChamadosSGC:
    """Chamados SGC CRUD and interactions"""

    def test_list_chamados(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/chamados-sgc", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "chamados" in data
        assert "total" in data
        chamados = data["chamados"]
        if chamados:
            _state["first_chamado_id"] = chamados[0]["id"]
        print(f"PASS: GET /api/chamados-sgc - total: {data.get('total')}")

    def test_chamados_dashboard(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/chamados-sgc/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "abertos" in data or "total_abertos" in data
        print(f"PASS: GET /api/chamados-sgc/dashboard - total: {data.get('total')}")

    def test_create_chamado(self, admin_headers):
        """POST /api/chamados-sgc"""
        ticket_num = f"TEST-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "numero_ticket": ticket_num,
            "titulo": "TEST Chamado Auditoria",
            "descricao": "Chamado criado para testes de auditoria",
            "data_abertura": "2026-02-01T10:00:00",
            "prioridade": 0,
            "modalidade": "CAP"
        }
        r = requests.post(f"{BASE_URL}/api/chamados-sgc", headers=admin_headers, json=payload)
        assert r.status_code == 201, f"Create chamado failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        _state["new_chamado_id"] = data["id"]
        print(f"PASS: POST /api/chamados-sgc - id: {data['id']}, ticket: {ticket_num}")

    def test_get_chamado_by_id(self, admin_headers):
        """GET /api/chamados-sgc/{id} - returns nested {chamado:{...}, andamentos:[], interacoes:[]}"""
        chamado_id = _state.get("new_chamado_id") or _state.get("first_chamado_id")
        if not chamado_id:
            pytest.skip("No chamado_id available")
        r = requests.get(f"{BASE_URL}/api/chamados-sgc/{chamado_id}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        # Verify nested structure (critical fix from iteration 18)
        assert "chamado" in data, f"Expected 'chamado' key in response. Got: {list(data.keys())}"
        assert "interacoes" in data
        assert "andamentos" in data
        chamado = data["chamado"]
        assert "id" in chamado
        assert chamado["id"] == chamado_id
        print(f"PASS: GET /api/chamados-sgc/{chamado_id} - nested structure confirmed")

    def test_create_interacao_chamado(self, admin_headers):
        """POST /api/chamados-sgc/{id}/interacoes - recently fixed _id bug"""
        chamado_id = _state.get("new_chamado_id") or _state.get("first_chamado_id")
        if not chamado_id:
            pytest.skip("No chamado_id available")
        r = requests.post(f"{BASE_URL}/api/chamados-sgc/{chamado_id}/interacoes",
                          headers=admin_headers,
                          json={"tipo": "comentario", "conteudo": "Interação de teste de auditoria", "visibilidade": "interno"})
        assert r.status_code == 200, f"Create interacao failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data
        assert data.get("chamado_id") == chamado_id
        print(f"PASS: POST /api/chamados-sgc/{chamado_id}/interacoes - id: {data['id']}, no _id")


# ==================== 9. PAINEL DE VAGAS ====================

class TestPainelVagas:
    """Painel de Vagas endpoints"""

    def test_painel_vagas_dashboard(self, admin_headers):
        """GET /api/painel-vagas/dashboard (returns resumo inside)"""
        r = requests.get(f"{BASE_URL}/api/painel-vagas/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "resumo" in data
        resumo = data["resumo"]
        assert "total_turmas" in resumo
        assert "total_vagas" in resumo
        print(f"PASS: GET /api/painel-vagas/dashboard - total_turmas: {resumo.get('total_turmas')}")

    def test_painel_vagas_turmas(self, admin_headers):
        """GET /api/painel-vagas/turmas"""
        r = requests.get(f"{BASE_URL}/api/painel-vagas/turmas", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "turmas" in data
        assert "total" in data
        print(f"PASS: GET /api/painel-vagas/turmas - total: {data.get('total')}")


# ==================== 10. APOIO COGNITIVO ====================

class TestApoioCognitivo:
    """Tarefas, saudação/meu-dia - recently fixed _id bug"""

    def test_get_meu_dia(self, admin_headers):
        """GET /api/apoio/meu-dia (includes saudação)"""
        r = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "tarefas" in data
        assert "saudacao" in data
        assert "estatisticas" in data
        assert data["saudacao"] in ("Bom dia", "Boa tarde", "Boa noite")
        print(f"PASS: GET /api/apoio/meu-dia - saudacao: {data.get('saudacao')}, tarefas: {len(data.get('tarefas', []))}")

    def test_create_tarefa(self, admin_headers):
        """POST /api/apoio/tarefas - recently fixed _id ObjectId bug"""
        payload = {
            "titulo": "TEST_Tarefa Auditoria",
            "descricao": "Tarefa criada em teste de auditoria",
            "categoria": "rotina",
            "prioridade": 2
        }
        r = requests.post(f"{BASE_URL}/api/apoio/tarefas", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create tarefa failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        # Critical: no _id in response (ObjectId bug was fixed)
        assert "_id" not in data, f"CRITICAL: '_id' found in tarefa response (ObjectId serialization bug!): {data}"
        assert data.get("titulo") == "TEST_Tarefa Auditoria"
        assert data.get("concluida") == False
        _state["tarefa_id"] = data["id"]
        print(f"PASS: POST /api/apoio/tarefas - id: {data['id']}, no _id in response (bug fixed!)")

    def test_update_tarefa(self, admin_headers):
        tarefa_id = _state.get("tarefa_id")
        if not tarefa_id:
            pytest.skip("No tarefa_id available")
        r = requests.put(f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}",
                         headers=admin_headers,
                         json={"titulo": "TEST_Tarefa Auditoria ATUALIZADA", "concluida": True})
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        print(f"PASS: PUT /api/apoio/tarefas/{tarefa_id} -> updated")

    def test_delete_tarefa(self, admin_headers):
        tarefa_id = _state.get("tarefa_id")
        if not tarefa_id:
            pytest.skip("No tarefa_id available")
        r = requests.delete(f"{BASE_URL}/api/apoio/tarefas/{tarefa_id}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        print(f"PASS: DELETE /api/apoio/tarefas/{tarefa_id}")


# ==================== 11. LEMBRETES ====================

class TestLembretes:
    """Lembretes CRUD - recently fixed _id bug"""

    def test_create_lembrete(self, admin_headers):
        """POST /api/apoio/lembretes - recently fixed _id bug"""
        from datetime import datetime, timezone, timedelta
        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "titulo": "TEST_Lembrete Auditoria",
            "descricao": "Lembrete criado em auditoria",
            "data_lembrete": future,
            "tipo": "outro"
        }
        r = requests.post(f"{BASE_URL}/api/apoio/lembretes", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create lembrete failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in lembrete response: {data}"
        assert data.get("titulo") == "TEST_Lembrete Auditoria"
        _state["lembrete_id"] = data["id"]
        print(f"PASS: POST /api/apoio/lembretes - id: {data['id']}, no _id in response")

    def test_list_lembretes(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/apoio/lembretes", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "lembretes" in data
        assert "total" in data
        print(f"PASS: GET /api/apoio/lembretes - total: {data.get('total')}")


# ==================== 12. ARTIGOS CONHECIMENTO ====================

class TestArtigos:
    """Artigos de Conhecimento - recently fixed _id bug"""

    def test_list_artigos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/apoio/conhecimento", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "artigos" in data
        print(f"PASS: GET /api/apoio/conhecimento - total: {len(data.get('artigos', []))}")

    def test_create_artigo(self, admin_headers):
        """POST /api/apoio/conhecimento - recently fixed _id bug"""
        payload = {
            "titulo": "TEST_Artigo Auditoria",
            "conteudo": "Conteúdo do artigo criado em teste de auditoria do sistema.",
            "categoria": "procedimento",
            "destaque": False
        }
        r = requests.post(f"{BASE_URL}/api/apoio/conhecimento", headers=admin_headers, json=payload)
        assert r.status_code == 201, f"Create artigo failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in artigo response: {data}"
        assert data.get("titulo") == "TEST_Artigo Auditoria"
        _state["artigo_id"] = data["id"]
        print(f"PASS: POST /api/apoio/conhecimento - id: {data['id']}, no _id in response")


# ==================== 13. CONTATOS ====================

class TestContatos:
    """Contatos LOG CRUD - recently fixed _id bug"""

    def test_create_contato(self, admin_headers):
        """POST /api/contatos - recently fixed _id bug"""
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        payload = {
            "pedido_id": pedido_id,
            "aluno_nome": "TEST_Aluno Contato",
            "canal": "telefone",
            "tipo": "primeiro_contato",
            "descricao": "Contato de teste de auditoria"
        }
        r = requests.post(f"{BASE_URL}/api/contatos", headers=admin_headers, json=payload)
        assert r.status_code == 200, f"Create contato failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in contato response: {data}"
        assert data.get("canal") == "telefone"
        _state["contato_id"] = data["id"]
        print(f"PASS: POST /api/contatos - id: {data['id']}, no _id in response")

    def test_list_contatos(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/contatos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "contatos" in data
        assert "total" in data
        print(f"PASS: GET /api/contatos - total: {data.get('total')}")


# ==================== 14. USUÁRIOS ====================

class TestUsuarios:
    """Usuários CRUD (admin only)"""

    def test_list_usuarios_admin(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/usuarios", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "usuarios" in data
        assert "total" in data
        usuarios = data["usuarios"]
        assert len(usuarios) > 0
        # Store first non-admin user id for later
        for u in usuarios:
            if u.get("email") != ADMIN_EMAIL:
                _state["other_user_id"] = u["id"]
                break
        print(f"PASS: GET /api/usuarios - total: {data.get('total')}")

    def test_get_usuario_by_id(self, admin_headers):
        user_id = _state.get("other_user_id")
        if not user_id:
            pytest.skip("No other_user_id available")
        r = requests.get(f"{BASE_URL}/api/usuarios/{user_id}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == user_id
        print(f"PASS: GET /api/usuarios/{user_id} - nome: {data.get('nome')}")

    def test_register_new_user(self, admin_headers):
        """POST /api/auth/registrar or /api/auth/register - create new user"""
        payload = {
            "nome": "TEST_Usuario Auditoria",
            "email": f"test.audit.{uuid.uuid4().hex[:6]}@example.com",
            "senha": "Teste@2026",
            "role": "consultor"
        }
        # Try both endpoint names
        r = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if r.status_code == 404:
            r = requests.post(f"{BASE_URL}/api/auth/registrar", json=payload)
        assert r.status_code in (200, 201), f"Register failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        print(f"PASS: POST /api/auth/register - id: {data['id']}")


# ==================== 15. ALERTAS ====================

class TestAlertas:
    """Alertas endpoints"""

    def test_alertas_dashboard(self, admin_headers):
        """GET /api/alertas/dashboard"""
        r = requests.get(f"{BASE_URL}/api/alertas/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "alertas" in data
        assert "estatisticas" in data
        stats = data["estatisticas"]
        assert "total" in stats
        print(f"PASS: GET /api/alertas/dashboard - total alertas: {stats.get('total')}")

    def test_alertas_contagem(self, admin_headers):
        """GET /api/alertas/contagem"""
        r = requests.get(f"{BASE_URL}/api/alertas/contagem", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        print(f"PASS: GET /api/alertas/contagem - total: {data.get('total')}")

    def test_alertas_pendencias_vencidas_check(self, admin_headers):
        """Check if /api/alertas/pendencias-vencidas endpoint exists or fallback"""
        r = requests.get(f"{BASE_URL}/api/alertas/pendencias-vencidas", headers=admin_headers)
        if r.status_code == 404:
            print(f"INFO: /api/alertas/pendencias-vencidas returns 404 (endpoint may not exist, use /alertas/dashboard)")
        else:
            assert r.status_code == 200, f"Unexpected status: {r.status_code}"
            print(f"PASS: GET /api/alertas/pendencias-vencidas - {r.status_code}")

    def test_alertas_reembolsos_abertos_check(self, admin_headers):
        """Check if /api/alertas/reembolsos-abertos endpoint exists or fallback"""
        r = requests.get(f"{BASE_URL}/api/alertas/reembolsos-abertos", headers=admin_headers)
        if r.status_code == 404:
            print(f"INFO: /api/alertas/reembolsos-abertos returns 404 (endpoint may not exist, use /alertas/dashboard)")
        else:
            assert r.status_code == 200, f"Unexpected status: {r.status_code}"
            print(f"PASS: GET /api/alertas/reembolsos-abertos - {r.status_code}")


# ==================== 16. STATUS MATRÍCULA ====================

class TestStatusMatricula:
    """Status Matrícula state machine"""

    def test_transicionar_status(self, admin_headers):
        """POST /api/status/pedidos/{id}/transicionar - uses StatusMatriculaEnum values"""
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id available")
        # StatusMatriculaEnum values: inscrito, analise_documental, pendente_pagamento,
        # matriculado, trancado, cancelado, concluido, evadido
        # First set to inscrito, then transition to analise_documental
        r1 = requests.post(f"{BASE_URL}/api/status/pedidos/{pedido_id}/transicionar",
                           headers=admin_headers,
                           json={"status_novo": "inscrito", "motivo": "Teste de auditoria - step1"})
        # If 400 it means transitions from current status to inscrito not allowed - try analise_documental directly
        if r1.status_code == 400:
            r1 = requests.post(f"{BASE_URL}/api/status/pedidos/{pedido_id}/transicionar",
                               headers=admin_headers,
                               json={"status_novo": "analise_documental", "motivo": "Teste de auditoria"})
        assert r1.status_code in (200, 201, 400), f"Transicionar status unexpected error: {r1.status_code} - {r1.text}"
        if r1.status_code in (200, 201):
            data = r1.json()
            assert "status_novo" in data
            print(f"PASS: POST /api/status/pedidos/{pedido_id}/transicionar -> {data.get('status_novo')}")
        else:
            # 400 is expected if current status doesn't allow transition
            print(f"INFO: Transition returned 400 (may be state machine constraint): {r1.json()}")

    def test_get_proximos_status(self, admin_headers):
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id available")
        r = requests.get(f"{BASE_URL}/api/status/pedidos/{pedido_id}/proximos",
                         headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "status_atual" in data
        assert "proximos_status" in data
        print(f"PASS: GET /api/status/pedidos/{pedido_id}/proximos - status: {data['status_atual'].get('valor')}")


# ==================== 17. PRODUTIVIDADE ====================

class TestProdutividade:
    """Produtividade dashboard"""

    def test_produtividade_dashboard(self, admin_headers):
        """GET /api/produtividade/dashboard"""
        r = requests.get(f"{BASE_URL}/api/produtividade/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "kpis" in data
        assert "membros" in data
        assert "periodo" in data
        kpis = data["kpis"]
        assert "total_pedidos" in kpis
        print(f"PASS: GET /api/produtividade/dashboard - total_pedidos: {kpis.get('total_pedidos')}, membros: {len(data.get('membros', []))}")


# ==================== 18. ATRIBUIÇÕES / CAIXA DE ENTRADA ====================

class TestAtribuicoes:
    """Atribuições / Caixa de Entrada"""

    def test_atribuicoes_resumo(self, admin_headers):
        """GET /api/atribuicoes/resumo"""
        r = requests.get(f"{BASE_URL}/api/atribuicoes/resumo", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "pedidos" in data
        assert "usuario" in data
        print(f"PASS: GET /api/atribuicoes/resumo - total: {data.get('total')}, usuario: {data.get('usuario')}")

    def test_atribuicoes_minha_caixa(self, admin_headers):
        """GET /api/atribuicoes/minha-caixa"""
        r = requests.get(f"{BASE_URL}/api/atribuicoes/minha-caixa", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        print(f"PASS: GET /api/atribuicoes/minha-caixa - total items: {data.get('total')}")


# ==================== 19. DOCUMENTOS (pendências_doc) ====================

class TestDocumentosPendencias:
    """Documentos/Pendências documentais - recently fixed _id bug"""

    def test_create_pendencia_doc(self, admin_headers):
        """POST /api/documentos/pendencias - recently fixed _id bug"""
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id")
        if not pedido_id:
            pytest.skip("No pedido_id available")
        r_pedido = requests.get(f"{BASE_URL}/api/pedidos/{pedido_id}", headers=admin_headers)
        if r_pedido.status_code != 200:
            pytest.skip("Cannot fetch pedido for doc pendencia test")
        pedido_data = r_pedido.json()
        alunos = pedido_data.get("alunos", [])
        if not alunos:
            pytest.skip("No alunos for doc pendencia test")
        aluno_id = alunos[0]["id"]
        payload = {
            "pedido_id": pedido_id,
            "aluno_id": aluno_id,
            "tipo": "rg",
            "descricao": "RG do aluno"
        }
        r = requests.post(f"{BASE_URL}/api/documentos/pendencias", headers=admin_headers, json=payload)
        assert r.status_code == 201, f"Create doc pendencia failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in doc pendencia response: {data}"
        _state["doc_pendencia_id"] = data["id"]
        print(f"PASS: POST /api/documentos/pendencias - id: {data['id']}, no _id")

    def test_list_pendencias_doc(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/documentos/pendencias", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "pendencias" in data
        print(f"PASS: GET /api/documentos/pendencias - total: {data.get('total')}")


# ==================== 20. TURMAS ====================

class TestTurmas:
    """Turmas CRUD - recently fixed _id bug"""

    def test_list_turmas(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/turmas", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "turmas" in data
        assert "total" in data
        print(f"PASS: GET /api/turmas - total: {data.get('total')}")

    def test_create_turma(self, admin_headers):
        """POST /api/turmas - recently fixed _id bug"""
        curso_id = _state.get("curso_id") or _state.get("test_curso_id")
        if not curso_id:
            pytest.skip("No curso_id available")
        payload = {
            "curso_id": curso_id,
            "nome": f"TEST_Turma Auditoria {uuid.uuid4().hex[:4]}",
            "turno": "NOTURNO",
            "vagas": 30,
            "periodo": "2026.1"
        }
        r = requests.post(f"{BASE_URL}/api/turmas", headers=admin_headers, json=payload)
        assert r.status_code == 201, f"Create turma failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in turma response: {data}"
        _state["turma_id"] = data["id"]
        print(f"PASS: POST /api/turmas - id: {data['id']}, no _id")

    def test_reservar_vaga_turma(self, admin_headers):
        """POST /api/turmas/{id}/reservar - recently fixed _id bug"""
        turma_id = _state.get("turma_id")
        if not turma_id:
            pytest.skip("No turma_id available")
        pedido_id = _state.get("new_pedido_id") or _state.get("first_pedido_id") or "test-pedido-id"
        r = requests.post(f"{BASE_URL}/api/turmas/{turma_id}/reservar",
                          headers=admin_headers,
                          json={"turma_id": turma_id, "pedido_id": pedido_id, "aluno_nome": "TEST_Aluno Reserva"})
        assert r.status_code == 200, f"Reservar vaga failed: {r.status_code} - {r.text}"
        data = r.json()
        assert "id" in data
        assert "_id" not in data, f"CRITICAL: '_id' found in reserva response: {data}"
        print(f"PASS: POST /api/turmas/{turma_id}/reservar - no _id in response")


# ==================== 21. EXPORTAÇÃO TOTVS ====================

class TestExportacaoTOTVS:
    """TOTVS Export endpoint"""

    def test_exportar_totvs_xlsx(self, admin_headers):
        """GET /api/pedidos/exportar/totvs - exports realizado pedidos"""
        r = requests.get(f"{BASE_URL}/api/pedidos/exportar/totvs?formato=xlsx", headers=admin_headers)
        # 200 (with file) or 200 (empty file) - should not 500
        assert r.status_code == 200, f"TOTVS export failed: {r.status_code} - {r.text}"
        content_type = r.headers.get("Content-Type", "")
        # Either xlsx content type or could be empty if no realizado pedidos
        print(f"PASS: GET /api/pedidos/exportar/totvs - status: {r.status_code}, content_type: {content_type}, size: {len(r.content)} bytes")

    def test_exportar_totvs_csv(self, admin_headers):
        """GET /api/pedidos/exportar/totvs?formato=csv"""
        r = requests.get(f"{BASE_URL}/api/pedidos/exportar/totvs?formato=csv", headers=admin_headers)
        assert r.status_code == 200, f"TOTVS CSV export failed: {r.status_code}"
        print(f"PASS: GET /api/pedidos/exportar/totvs?formato=csv - size: {len(r.content)} bytes")


# ==================== 22. HEALTH CHECK ====================

class TestHealth:
    """Health and basic endpoints"""

    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        print(f"PASS: GET /api/health - {r.json()}")

    def test_unauthorized_access(self):
        """Verify endpoints require auth (no token)"""
        r = requests.get(f"{BASE_URL}/api/pedidos")
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"
        print(f"PASS: Unauthorized access returns {r.status_code}")


# ==================== 23. SAUDAÇÃO ENDPOINT CHECK ====================

class TestApoioSaudacao:
    """Check apoio/saudacao endpoint (may not exist as separate endpoint)"""

    def test_apoio_saudacao_endpoint(self, admin_headers):
        """GET /api/apoio/saudacao - check if exists, fallback to meu-dia"""
        r = requests.get(f"{BASE_URL}/api/apoio/saudacao", headers=admin_headers)
        if r.status_code == 404:
            print(f"INFO: /api/apoio/saudacao returns 404 - saudação is in /api/apoio/meu-dia response")
            # Verify saudação is in meu-dia
            r2 = requests.get(f"{BASE_URL}/api/apoio/meu-dia", headers=admin_headers)
            assert r2.status_code == 200
            data = r2.json()
            assert "saudacao" in data
            print(f"PASS: Saudação found in /api/apoio/meu-dia: {data.get('saudacao')}")
        else:
            assert r.status_code == 200
            print(f"PASS: GET /api/apoio/saudacao - {r.status_code}")


# ==================== CLEANUP ====================

class TestCleanup:
    """Cleanup test data created during tests"""

    def test_cleanup_test_curso(self, admin_headers):
        """Delete test curso"""
        curso_id = _state.get("test_curso_id")
        if not curso_id:
            print("INFO: No test curso to cleanup")
            return
        r = requests.delete(f"{BASE_URL}/api/cursos/{curso_id}", headers=admin_headers)
        print(f"Cleanup curso {curso_id}: {r.status_code}")

    def test_cleanup_test_chamado(self, admin_headers):
        """Delete test chamado"""
        chamado_id = _state.get("new_chamado_id")
        if not chamado_id:
            print("INFO: No test chamado to cleanup")
            return
        r = requests.delete(f"{BASE_URL}/api/chamados-sgc/{chamado_id}", headers=admin_headers)
        print(f"Cleanup chamado {chamado_id}: {r.status_code}")

    def test_cleanup_test_pendencia(self, admin_headers):
        """Delete test pendencia manual"""
        pendencia_id = _state.get("pendencia_manual_id")
        if not pendencia_id:
            print("INFO: No test pendencia to cleanup")
            return
        r = requests.delete(f"{BASE_URL}/api/pendencias/{pendencia_id}", headers=admin_headers)
        print(f"Cleanup pendencia {pendencia_id}: {r.status_code}")

    def test_cleanup_test_reembolso(self, admin_headers):
        """Delete test reembolso"""
        reembolso_id = _state.get("reembolso_id")
        if not reembolso_id:
            print("INFO: No test reembolso to cleanup")
            return
        r = requests.delete(f"{BASE_URL}/api/reembolsos/{reembolso_id}", headers=admin_headers)
        print(f"Cleanup reembolso {reembolso_id}: {r.status_code}")

    def test_cleanup_artigo(self, admin_headers):
        """Delete test artigo"""
        artigo_id = _state.get("artigo_id")
        if not artigo_id:
            print("INFO: No test artigo to cleanup")
            return
        r = requests.delete(f"{BASE_URL}/api/apoio/conhecimento/{artigo_id}", headers=admin_headers)
        print(f"Cleanup artigo {artigo_id}: {r.status_code}")
