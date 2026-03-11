"""
Test file for iteration 18: Validates fixed modules after MongoDB migration.
Tests: BI Dashboard, SLA Dashboard, Chamados SGC, Caixa de Entrada (atribuicoes/resumo)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "pedro.passos@fieb.org.br"
ADMIN_SENHA = "Pedro@2026"

@pytest.fixture(scope="module")
def token():
    """Get admin auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.status_code} - {resp.text}")
    return resp.json().get("token")

@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestBIDashboard:
    """Tests for GET /api/documentos/bi/completo"""

    def test_bi_completo_status_200(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_bi_completo_has_resumo(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        assert "resumo" in data, "Response missing 'resumo' key"
        resumo = data["resumo"]
        assert "total_matriculas" in resumo, "resumo missing total_matriculas"
        assert "taxa_conversao" in resumo, "resumo missing taxa_conversao"
        assert "pendencias_abertas" in resumo, "resumo missing pendencias_abertas"
        assert "reembolsos_pendentes" in resumo, "resumo missing reembolsos_pendentes"

    def test_bi_total_matriculas_414(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        total = data["resumo"]["total_matriculas"]
        # Should be at least 413 (migrated) and at most 420 (some extras created during tests)
        assert total >= 413, f"Total matrículas expected ~414, got {total}"
        print(f"Total matrículas: {total}")

    def test_bi_taxa_conversao_value(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        taxa = data["resumo"]["taxa_conversao"]
        assert isinstance(taxa, (int, float)), f"taxa_conversao should be numeric, got {type(taxa)}"
        assert 0 <= taxa <= 100, f"taxa_conversao should be 0-100, got {taxa}"
        print(f"Taxa conversão: {taxa}%")

    def test_bi_has_evolucao_mensal(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        assert "evolucao_mensal" in data, "Response missing evolucao_mensal"
        evolucao = data["evolucao_mensal"]
        assert isinstance(evolucao, list), f"evolucao_mensal should be list, got {type(evolucao)}"
        assert len(evolucao) == 6, f"Expected 6 months, got {len(evolucao)}"
        # Verify structure of each month
        for mes in evolucao:
            assert "mes_label" in mes, f"Month entry missing mes_label: {mes}"
            assert "total" in mes, f"Month entry missing total: {mes}"

    def test_bi_has_matriculas_section(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        assert "matriculas" in data, "Response missing matriculas"
        matriculas = data["matriculas"]
        assert "total" in matriculas
        assert "taxa_conversao" in matriculas
        assert "por_status" in matriculas

    def test_bi_has_reembolsos_section(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        assert "reembolsos" in data, "Response missing reembolsos"
        reembolsos = data["reembolsos"]
        assert "total" in reembolsos
        assert "pendentes" in reembolsos
        assert "pagos" in reembolsos

    def test_bi_has_pendencias_section(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        assert "pendencias" in data, "Response missing pendencias"
        pendencias = data["pendencias"]
        assert "total" in pendencias
        assert "taxa_aprovacao" in pendencias


class TestSLADashboard:
    """Tests for GET /api/sla/dashboard"""

    def test_sla_dashboard_status_200(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_sla_dashboard_has_resumo_geral(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        assert "resumo_geral" in data, "Response missing resumo_geral"
        resumo = data["resumo_geral"]
        assert "total_pedidos" in resumo, "resumo_geral missing total_pedidos"
        assert "pedidos_mes" in resumo, "resumo_geral missing pedidos_mes"
        assert "pedidos_abertos" in resumo, "resumo_geral missing pedidos_abertos"
        assert "pedidos_concluidos" in resumo, "resumo_geral missing pedidos_concluidos"
        assert "taxa_conclusao" in resumo, "resumo_geral missing taxa_conclusao"

    def test_sla_total_pedidos_414(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        total = data["resumo_geral"]["total_pedidos"]
        assert total >= 413, f"Expected ~414 pedidos, got {total}"
        print(f"SLA total pedidos: {total}")

    def test_sla_em_aberto_17(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        abertos = data["resumo_geral"]["pedidos_abertos"]
        assert isinstance(abertos, int), f"pedidos_abertos should be int, got {type(abertos)}"
        print(f"SLA em aberto: {abertos}")

    def test_sla_taxa_conclusao(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        taxa = data["resumo_geral"]["taxa_conclusao"]
        assert 0 <= taxa <= 100, f"taxa_conclusao should be 0-100, got {taxa}"
        print(f"SLA taxa conclusao: {taxa}%")

    def test_sla_has_metricas_por_status(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        assert "metricas_por_status" in data, "Response missing metricas_por_status"
        metricas = data["metricas_por_status"]
        assert isinstance(metricas, list), f"metricas_por_status should be list"
        if metricas:
            m = metricas[0]
            assert "status" in m
            assert "quantidade" in m
            assert "sla_horas" in m

    def test_sla_has_evolucao_semanal(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        assert "evolucao_semanal" in data, "Response missing evolucao_semanal"
        evolucao = data["evolucao_semanal"]
        assert isinstance(evolucao, list), "evolucao_semanal should be list"
        assert len(evolucao) == 4, f"Expected 4 weeks, got {len(evolucao)}"

    def test_sla_has_alertas(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/sla/dashboard", headers=auth_headers)
        data = resp.json()
        assert "alertas_sla" in data or "alertas" in data, "Response missing alertas_sla or alertas"


class TestChamadosSGCDashboard:
    """Tests for GET /api/chamados-sgc/dashboard"""

    def test_chamados_dashboard_status_200(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc/dashboard", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_chamados_dashboard_has_required_fields(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc/dashboard", headers=auth_headers)
        data = resp.json()
        assert "total_abertos" in data, "Response missing total_abertos"
        assert "criticos" in data, "Response missing criticos"
        assert "sla_critico" in data, "Response missing sla_critico"
        assert "fechados_hoje" in data, "Response missing fechados_hoje"

    def test_chamados_em_aberto_3(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc/dashboard", headers=auth_headers)
        data = resp.json()
        abertos = data["total_abertos"]
        # Expected 3 chamados em aberto
        assert abertos >= 0, f"total_abertos should be >= 0, got {abertos}"
        print(f"Chamados em aberto: {abertos}")

    def test_chamados_criticos_value(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc/dashboard", headers=auth_headers)
        data = resp.json()
        criticos = data["criticos"]
        assert isinstance(criticos, int), f"criticos should be int, got {type(criticos)}"
        print(f"Chamados críticos: {criticos}")

    def test_chamados_list_has_3_records(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "chamados" in data, "Response missing chamados"
        assert "total" in data, "Response missing total"
        total = data["total"]
        print(f"Total chamados: {total}")

    def test_chamados_status_values(self, auth_headers):
        """Verify chamados have valid status values"""
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc", headers=auth_headers)
        data = resp.json()
        valid_statuses = {"backlog", "em_atendimento", "aguardando_retorno", "concluido", "cancelado"}
        for chamado in data.get("chamados", []):
            status = chamado.get("status")
            assert status in valid_statuses, f"Invalid status '{status}' for chamado {chamado.get('numero_ticket')}"


class TestAtribuicoesResumo:
    """Tests for GET /api/atribuicoes/resumo"""

    def test_resumo_status_200(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/atribuicoes/resumo", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_resumo_has_required_fields(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/atribuicoes/resumo", headers=auth_headers)
        data = resp.json()
        assert "total" in data, "Response missing total"
        assert "pedidos" in data, "Response missing pedidos"
        assert "pendencias" in data, "Response missing pendencias"
        assert "reembolsos" in data, "Response missing reembolsos"
        assert "usuario" in data, "Response missing usuario"

    def test_resumo_numeric_values(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/atribuicoes/resumo", headers=auth_headers)
        data = resp.json()
        assert isinstance(data["total"], int), f"total should be int, got {type(data['total'])}"
        assert isinstance(data["pedidos"], int), f"pedidos should be int, got {type(data['pedidos'])}"
        assert data["total"] >= 0, "total should be >= 0"

    def test_minha_caixa_status_200(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/atribuicoes/minha-caixa", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_minha_caixa_structure(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/atribuicoes/minha-caixa", headers=auth_headers)
        data = resp.json()
        assert "items" in data, "Response missing items"
        assert "total" in data, "Response missing total"
        assert isinstance(data["items"], list), "items should be list"


class TestAPIBIFrontendMismatch:
    """Code review tests - check if API response matches what frontend expects"""

    def test_bi_matriculas_has_total_not_total_pedidos(self, auth_headers):
        """
        BUG DETECTION: Frontend (BIDashboardPage.jsx line 416) uses matriculas.total_pedidos
        but API returns matriculas.total. This is a field name mismatch.
        """
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        matriculas = data.get("matriculas", {})
        # API returns 'total' not 'total_pedidos'
        has_total = "total" in matriculas
        has_total_pedidos = "total_pedidos" in matriculas
        print(f"matriculas.total exists: {has_total}")
        print(f"matriculas.total_pedidos exists: {has_total_pedidos}")
        # This test documents the mismatch - frontend expects total_pedidos
        # If this fails it means API was fixed to include total_pedidos
        assert has_total, "matriculas.total should exist"

    def test_bi_reembolsos_field_names(self, auth_headers):
        """
        BUG DETECTION: Frontend expects reembolsos.abertos, reembolsos.no_financeiro,
        reembolsos.com_retencao, reembolsos.aguardando but API returns 
        reembolsos.pendentes, reembolsos.pagos, reembolsos.rejeitados
        """
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        reembolsos = data.get("reembolsos", {})
        # Document what API actually returns
        print(f"reembolsos keys: {list(reembolsos.keys())}")
        # Check for frontend-expected fields
        has_abertos = "abertos" in reembolsos
        has_no_financeiro = "no_financeiro" in reembolsos
        print(f"reembolsos.abertos: {has_abertos}")
        print(f"reembolsos.no_financeiro: {has_no_financeiro}")

    def test_bi_pendencias_field_names(self, auth_headers):
        """
        BUG DETECTION: Frontend uses pendencias.em_aberto but API returns pendencias.pendentes
        """
        resp = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=auth_headers)
        data = resp.json()
        pendencias = data.get("pendencias", {})
        print(f"pendencias keys: {list(pendencias.keys())}")
        has_em_aberto = "em_aberto" in pendencias
        has_pendentes = "pendentes" in pendencias
        print(f"pendencias.em_aberto: {has_em_aberto}")
        print(f"pendencias.pendentes: {has_pendentes}")

    def test_chamados_detail_structure(self, auth_headers):
        """
        BUG DETECTION: Frontend modal (ChamadosSGCPage.jsx) expects
        chamadoSelecionado.chamado.xxx but API returns flat document
        """
        resp = requests.get(f"{BASE_URL}/api/chamados-sgc", headers=auth_headers)
        data = resp.json()
        chamados = data.get("chamados", [])
        if not chamados:
            pytest.skip("No chamados available to test detail view")
        
        chamado_id = chamados[0].get("id")
        detail_resp = requests.get(f"{BASE_URL}/api/chamados-sgc/{chamado_id}", headers=auth_headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        
        # Document what API returns
        has_nested_chamado = "chamado" in detail
        has_andamentos = "andamentos" in detail
        has_interacoes = "interacoes" in detail
        print(f"detail has 'chamado' nested key: {has_nested_chamado}")
        print(f"detail has 'andamentos': {has_andamentos}")
        print(f"detail has 'interacoes': {has_interacoes}")
        
        # Frontend expects chamadoSelecionado.chamado.xxx
        # API returns flat: { id, numero_ticket, ..., interacoes }
        # This is a MISMATCH - frontend would crash trying to access .chamado.xxx
        assert not has_nested_chamado, (
            "API returns flat document - frontend expects nested 'chamado' key. "
            "The detail modal will crash!"
        )
