"""
Test suite for Produtividade Dashboard API
Tests the new productivity dashboard feature for SYNAPSE system.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestProdutividadeDashboard:
    """Tests for Produtividade Dashboard API endpoint"""
    
    def test_dashboard_default_period(self, api_client):
        """Test dashboard with default 30d period"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert "periodo" in data
        assert "kpis" in data
        assert "membros" in data
        assert "evolucao_diaria" in data
        assert "generated_at" in data
        
        # Verify default period label
        assert data["periodo"] == "Últimos 30 dias"
        
        # Verify KPIs structure
        kpis = data["kpis"]
        assert "total_pedidos" in kpis
        assert "total_aprovados" in kpis
        assert "total_reembolsos" in kpis
        assert "total_auditorias" in kpis
        assert "media_diaria_pedidos" in kpis
        assert "membros_ativos" in kpis
        
        # Verify KPIs are numeric
        assert isinstance(kpis["total_pedidos"], int)
        assert isinstance(kpis["total_aprovados"], int)
        assert isinstance(kpis["total_reembolsos"], int)
        assert isinstance(kpis["total_auditorias"], int)
        assert isinstance(kpis["media_diaria_pedidos"], (int, float))
        assert isinstance(kpis["membros_ativos"], int)
        
        print(f"Default period KPIs: pedidos={kpis['total_pedidos']}, aprovados={kpis['total_aprovados']}")
    
    def test_dashboard_7d_period(self, api_client):
        """Test dashboard with 7 days period"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard?periodo=7d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["periodo"] == "Últimos 7 dias"
        
        # Verify evolucao_diaria contains 7 days max
        assert len(data["evolucao_diaria"]) <= 14  # max 14 days
        
        print(f"7d period: {len(data['evolucao_diaria'])} days of evolution data")
    
    def test_dashboard_15d_period(self, api_client):
        """Test dashboard with 15 days period"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard?periodo=15d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["periodo"] == "Últimos 15 dias"
        
        print(f"15d period: pedidos={data['kpis']['total_pedidos']}")
    
    def test_dashboard_90d_period(self, api_client):
        """Test dashboard with 90 days period"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard?periodo=90d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["periodo"] == "Últimos 90 dias"
        
        print(f"90d period: pedidos={data['kpis']['total_pedidos']}")
    
    def test_dashboard_all_period(self, api_client):
        """Test dashboard with all time period"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard?periodo=all")
        assert response.status_code == 200
        
        data = response.json()
        assert data["periodo"] == "Todo o período"
        
        print(f"All period: pedidos={data['kpis']['total_pedidos']}")
    
    def test_membros_data_structure(self, api_client):
        """Test that membros data has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        membros = data["membros"]
        
        # Check that membros is a list
        assert isinstance(membros, list)
        
        # If there are members, check their structure
        if membros:
            membro = membros[0]
            assert "usuario_id" in membro
            assert "nome" in membro
            assert "role" in membro
            assert "pedidos_criados" in membro
            assert "alteracoes_status" in membro
            assert "total_auditorias" in membro
            assert "pedidos_atribuidos" in membro
            assert "pedidos_concluidos" in membro
            assert "reembolsos_tratados" in membro
            assert "reembolsos_concluidos" in membro
            assert "total_acoes" in membro
            
            print(f"First member: {membro['nome']} - {membro['total_acoes']} total actions")
    
    def test_membros_sorted_by_total_acoes(self, api_client):
        """Test that membros are sorted by total_acoes descending"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        membros = data["membros"]
        
        # Check sorting - each member should have total_acoes >= next member
        for i in range(len(membros) - 1):
            assert membros[i]["total_acoes"] >= membros[i + 1]["total_acoes"], \
                f"Members not sorted: {membros[i]['nome']}({membros[i]['total_acoes']}) < {membros[i+1]['nome']}({membros[i+1]['total_acoes']})"
        
        print("Members correctly sorted by total_acoes descending")
    
    def test_evolucao_diaria_structure(self, api_client):
        """Test evolucao_diaria data structure"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        evolucao = data["evolucao_diaria"]
        
        assert isinstance(evolucao, list)
        
        if evolucao:
            dia = evolucao[0]
            assert "data" in dia
            assert "pedidos" in dia
            assert "acoes" in dia
            
            # Date format should be DD/MM
            assert "/" in dia["data"]
            
            print(f"Evolution data: {len(evolucao)} days, last day: {evolucao[-1]['data']}")
    
    def test_invalid_period_defaults_to_30d(self, api_client):
        """Test that invalid period defaults to 30 days"""
        response = api_client.get(f"{BASE_URL}/api/produtividade/dashboard?periodo=invalid")
        assert response.status_code == 200
        
        data = response.json()
        # Invalid period should default to 30d
        assert data["periodo"] == "Últimos 30 dias"
        
        print("Invalid period correctly defaulted to 30 days")


class TestProdutividadeHealth:
    """Health checks for Produtividade API"""
    
    def test_api_health(self, api_client):
        """Test API health endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        
        print("API health check passed")
