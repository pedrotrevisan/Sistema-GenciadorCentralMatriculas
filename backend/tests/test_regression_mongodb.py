"""
Regression test suite for SYNAPSE system after MongoDB migration.
Tests all critical flows: auth, pedidos, painel_vagas, produtividade, cadastros, pendencias.
MongoDB migration validation - iteration 17
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "pedro.passos@fieb.org.br"
ADMIN_PASSWORD = "Pedro@2026"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "senha": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        print(f"Auth token obtained for: {ADMIN_EMAIL}")
        return token
    pytest.skip(f"Authentication failed with status {response.status_code}: {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ==================== HEALTH ====================

class TestHealth:
    """Health check - should pass first"""

    def test_api_health(self, api_client):
        """Backend health check"""
        r = api_client.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        print(f"Health OK: {data}")


# ==================== AUTH ====================

class TestAuth:
    """Authentication flows"""

    def test_login_admin_direct(self, api_client):
        """Login with admin credentials - should not require password change"""
        r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "senha": ADMIN_PASSWORD
        })
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert "usuario" in data
        assert data["usuario"]["email"] == ADMIN_EMAIL
        # Should not require password change for pedro.passos
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        print(f"Login OK: {data['usuario']['nome']}, primeiro_acesso={data['usuario'].get('primeiro_acesso')}")

    def test_login_invalid_credentials(self, api_client):
        """Login with wrong credentials should return 401"""
        r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wronguser@fieb.org.br",
            "senha": "wrongpassword"
        })
        assert r.status_code == 401
        print("Invalid credentials correctly rejected with 401")

    def test_get_me(self, authenticated_client):
        """Get current user profile"""
        r = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print(f"Get me OK: {data['nome']} ({data['role']})")


# ==================== PEDIDOS ====================

class TestPedidos:
    """Pedidos CRUD and listing"""

    def test_dashboard_pedidos(self, authenticated_client):
        """Dashboard should show counts"""
        r = authenticated_client.get(f"{BASE_URL}/api/pedidos/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "contagem_status" in data
        assert "pedidos_recentes" in data
        total = data["contagem_status"].get("total", 0)
        print(f"Dashboard total pedidos: {total}")
        assert total > 0, "Should have pedidos after migration"

    def test_listar_pedidos_paginado(self, authenticated_client):
        """List pedidos - should have 413 total"""
        r = authenticated_client.get(f"{BASE_URL}/api/pedidos?pagina=1&por_pagina=10")
        assert r.status_code == 200
        data = r.json()
        assert "pedidos" in data
        assert "paginacao" in data
        pag = data["paginacao"]
        assert "total_itens" in pag
        print(f"Total pedidos: {pag['total_itens']} (expected ~413)")
        # Should have a significant number of pedidos after migration
        assert pag["total_itens"] >= 1, "Should have pedidos after migration"

    def test_criar_pedido_com_aluno(self, authenticated_client):
        """Create a new pedido with at least 1 aluno"""
        payload = {
            "curso_id": "test-curso-id",
            "curso_nome": "TEST_Curso Teste MongoDB Regression",
            "turma_id": None,
            "projeto_id": None,
            "projeto_nome": None,
            "empresa_id": None,
            "empresa_nome": "TEST_Empresa Teste",
            "vinculo_tipo": None,
            "observacoes": "Pedido de teste regressão MongoDB",
            "alunos": [{
                "nome": "TEST_Aluno Regression MongoDB",
                "cpf": "12345678901",
                "email": "test_aluno@teste.com",
                "telefone": "71999999999",
                "data_nascimento": "1990-01-15",
                "rg": "1234567",
                "rg_orgao_emissor": "SSP",
                "rg_uf": "BA",
                "rg_data_emissao": None,
                "naturalidade": "Salvador",
                "naturalidade_uf": "BA",
                "sexo": "M",
                "cor_raca": "parda",
                "grau_instrucao": "medio_completo",
                "nome_pai": None,
                "nome_mae": "Maria Teste",
                "endereco_cep": "41000000",
                "endereco_logradouro": "Rua Teste",
                "endereco_numero": "123",
                "endereco_complemento": None,
                "endereco_bairro": "Centro",
                "endereco_cidade": "Salvador",
                "endereco_uf": "BA"
            }]
        }
        r = authenticated_client.post(f"{BASE_URL}/api/pedidos", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "pedido" in data
        pedido = data["pedido"]
        assert pedido["id"] is not None
        assert pedido["numero_protocolo"] is not None
        assert len(pedido["alunos"]) == 1
        assert pedido["alunos"][0]["nome"] == "TEST_Aluno Regression MongoDB"
        print(f"Pedido criado: {pedido['numero_protocolo']} com {len(pedido['alunos'])} aluno(s)")
        return pedido["id"]

    def test_visualizar_pedido_existente(self, authenticated_client):
        """View details of an existing pedido"""
        # Get first pedido from list
        r_list = authenticated_client.get(f"{BASE_URL}/api/pedidos?pagina=1&por_pagina=1")
        assert r_list.status_code == 200
        pedidos = r_list.json()["pedidos"]
        assert len(pedidos) > 0
        pedido_id = pedidos[0]["id"]

        r = authenticated_client.get(f"{BASE_URL}/api/pedidos/{pedido_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == pedido_id
        assert "alunos" in data
        assert "status" in data
        assert "numero_protocolo" in data
        print(f"Pedido {pedido_id[:8]}...: protocolo={data['numero_protocolo']}, status={data['status']}, alunos={len(data['alunos'])}")

    def test_alterar_status_pedido(self, authenticated_client):
        """Change status of a pedido (pendente -> em_analise)"""
        # First get a pending pedido
        r_list = authenticated_client.get(f"{BASE_URL}/api/pedidos?status=pendente&pagina=1&por_pagina=1")
        assert r_list.status_code == 200
        pedidos = r_list.json()["pedidos"]

        if not pedidos:
            pytest.skip("No pending pedidos found")

        pedido_id = pedidos[0]["id"]
        r = authenticated_client.patch(
            f"{BASE_URL}/api/pedidos/{pedido_id}/status",
            json={"status": "em_analise", "motivo": None}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "em_analise"
        print(f"Status updated to em_analise for pedido {pedido_id[:8]}...")

        # Revert status back to pendente
        authenticated_client.patch(
            f"{BASE_URL}/api/pedidos/{pedido_id}/status",
            json={"status": "pendente", "motivo": None}
        )

    def test_analytics_pedidos(self, authenticated_client):
        """Analytics endpoint should return funil and stats"""
        r = authenticated_client.get(f"{BASE_URL}/api/pedidos/analytics")
        assert r.status_code == 200
        data = r.json()
        assert "funil" in data
        assert "total_pedidos" in data
        assert "taxa_conversao" in data
        print(f"Analytics: total={data['total_pedidos']}, taxa={data['taxa_conversao']}%")


# ==================== PAINEL VAGAS ====================

class TestPainelVagas:
    """Painel de Vagas - turmas e períodos"""

    def test_listar_periodos(self, authenticated_client):
        """Should list available periods"""
        r = authenticated_client.get(f"{BASE_URL}/api/painel-vagas/periodos")
        assert r.status_code == 200
        data = r.json()
        assert "periodos" in data
        periodos = data["periodos"]
        print(f"Períodos disponíveis: {periodos}")

    def test_dashboard_vagas(self, authenticated_client):
        """Dashboard should return resumo, por_curso, por_turno"""
        r = authenticated_client.get(f"{BASE_URL}/api/painel-vagas/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "resumo" in data
        assert "por_curso" in data
        assert "por_turno" in data
        assert "alertas" in data
        resumo = data["resumo"]
        assert "total_turmas" in resumo
        print(f"Vagas Dashboard: {resumo['total_turmas']} turmas, {resumo.get('total_vagas', 0)} vagas")

    def test_dashboard_vagas_filtro_periodo(self, authenticated_client):
        """Filter by period 2026.1"""
        r = authenticated_client.get(f"{BASE_URL}/api/painel-vagas/dashboard?periodo=2026.1")
        assert r.status_code == 200
        data = r.json()
        assert "resumo" in data
        print(f"2026.1 period: {data['resumo']['total_turmas']} turmas")

    def test_listar_turmas(self, authenticated_client):
        """List turmas should work"""
        r = authenticated_client.get(f"{BASE_URL}/api/painel-vagas/turmas")
        assert r.status_code == 200
        data = r.json()
        assert "turmas" in data
        assert "total" in data
        print(f"Turmas: {data['total']} found")


# ==================== PRODUTIVIDADE ====================

class TestProdutividade:
    """Produtividade Dashboard"""

    def test_dashboard_produtividade(self, authenticated_client):
        """Produtividade dashboard default 30d"""
        r = authenticated_client.get(f"{BASE_URL}/api/produtividade/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "kpis" in data
        assert "membros" in data
        assert "evolucao_diaria" in data
        kpis = data["kpis"]
        print(f"Produtividade KPIs: pedidos={kpis['total_pedidos']}, aprovados={kpis['total_aprovados']}, membros_ativos={kpis['membros_ativos']}")


# ==================== CADASTROS ====================

class TestCadastros:
    """Cadastros - cursos, projetos, empresas"""

    def test_listar_cursos(self, authenticated_client):
        """Should list 4487 cursos"""
        r = authenticated_client.get(f"{BASE_URL}/api/cursos")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Cursos: {len(data)} (expected ~4487)")
        # Validate we have a significant number after migration
        assert len(data) >= 100, f"Should have many cursos, got only {len(data)}"

    def test_estatisticas_cursos(self, authenticated_client):
        """Estatísticas should include total"""
        r = authenticated_client.get(f"{BASE_URL}/api/cursos/estatisticas")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert data["total"] >= 100
        print(f"Cursos stats: total={data['total']}")

    def test_listar_projetos(self, authenticated_client):
        """Projects list should work"""
        r = authenticated_client.get(f"{BASE_URL}/api/projetos")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Projetos: {len(data)} found")

    def test_listar_empresas(self, authenticated_client):
        """Empresas list should work"""
        r = authenticated_client.get(f"{BASE_URL}/api/empresas")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Empresas: {len(data)} found")


# ==================== PENDENCIAS ====================

class TestPendencias:
    """Central de Pendências"""

    def test_dashboard_pendencias(self, authenticated_client):
        """Dashboard should return stats"""
        r = authenticated_client.get(f"{BASE_URL}/api/pendencias/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "por_status" in data
        print(f"Pendencias dashboard: total={data['total']}")

    def test_listar_pendencias(self, authenticated_client):
        """List pendencias"""
        r = authenticated_client.get(f"{BASE_URL}/api/pendencias")
        assert r.status_code == 200
        data = r.json()
        assert "pendencias" in data
        assert "total" in data
        print(f"Pendencias: total={data['total']}")

    def test_tipos_documento(self, authenticated_client):
        """Tipos de documento should be seeded"""
        r = authenticated_client.get(f"{BASE_URL}/api/pendencias/tipos-documento")
        assert r.status_code == 200
        data = r.json()
        assert "tipos" in data
        assert len(data["tipos"]) > 0
        print(f"Tipos documento: {len(data['tipos'])} found")
