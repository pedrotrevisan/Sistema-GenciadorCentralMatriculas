"""
Test suite for Documentos API - Fase 2: Gestão de Pendências Documentais

Tests cover:
- Reference endpoints (tipos, status, prioridades)
- Statistics endpoints (stats/resumo, stats/por-tipo, stats/vencendo)
- BI Dashboard endpoints (bi/matriculas, bi/evolucao, bi/reembolsos, bi/pendencias, bi/completo)
- CRUD operations (criar, listar, buscar, enviar, validar)
- Validation queue endpoint
"""
import pytest
import requests
import os
from uuid import uuid4

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://matriculas-core.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@senai.br",
        "senha": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.fail(f"Admin login failed: {response.text}")


@pytest.fixture(scope="module")
def assistente_token():
    """Get assistente authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "assistente@senai.br",
        "senha": "assistente123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Assistente login failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def assistente_headers(assistente_token):
    """Headers with assistente auth"""
    return {"Authorization": f"Bearer {assistente_token}"}


@pytest.fixture(scope="module")
def pedido_id(admin_headers):
    """Get a pedido ID for testing"""
    r = requests.get(f"{BASE_URL}/api/pedidos", headers=admin_headers)
    if r.status_code == 200:
        pedidos = r.json().get("pedidos", [])
        if pedidos:
            return pedidos[0]["id"]
    pytest.fail("No pedidos found for testing")


# ==================== REFERENCE ENDPOINTS ====================

class TestReferencEndpoints:
    """Tests for reference data endpoints"""
    
    def test_get_tipos_documento(self, admin_headers):
        """GET /api/documentos/tipos - Lista tipos de documento"""
        r = requests.get(f"{BASE_URL}/api/documentos/tipos", headers=admin_headers)
        assert r.status_code == 200
        
        tipos = r.json()
        assert isinstance(tipos, list)
        assert len(tipos) > 0
        
        # Verify structure
        for tipo in tipos:
            assert "value" in tipo
            assert "label" in tipo
    
    def test_get_status_documento(self, admin_headers):
        """GET /api/documentos/status - Lista status de documento"""
        r = requests.get(f"{BASE_URL}/api/documentos/status", headers=admin_headers)
        assert r.status_code == 200
        
        statuses = r.json()
        assert isinstance(statuses, list)
        assert len(statuses) > 0
        
        # Verify structure
        for status in statuses:
            assert "value" in status
            assert "label" in status
            assert "color" in status
    
    def test_get_prioridades(self, admin_headers):
        """GET /api/documentos/prioridades - Lista prioridades"""
        r = requests.get(f"{BASE_URL}/api/documentos/prioridades", headers=admin_headers)
        assert r.status_code == 200
        
        prioridades = r.json()
        assert isinstance(prioridades, list)
        assert len(prioridades) == 4  # baixa, media, alta, urgente
        
        # Verify structure
        for p in prioridades:
            assert "value" in p
            assert "label" in p
            assert "color" in p


# ==================== STATISTICS ENDPOINTS ====================

class TestStatisticsEndpoints:
    """Tests for document statistics endpoints"""
    
    def test_get_stats_resumo(self, admin_headers):
        """GET /api/documentos/stats/resumo - Estatísticas gerais"""
        r = requests.get(f"{BASE_URL}/api/documentos/stats/resumo", headers=admin_headers)
        assert r.status_code == 200
        
        stats = r.json()
        assert "total" in stats
        assert "pendentes" in stats
        assert "enviados" in stats
        assert "em_analise" in stats
        assert "aprovados" in stats
        assert "recusados" in stats
        assert "expirados" in stats
        assert "taxa_aprovacao" in stats
        assert "total_em_aberto" in stats
    
    def test_get_stats_por_tipo(self, admin_headers):
        """GET /api/documentos/stats/por-tipo - Estatísticas por tipo"""
        r = requests.get(f"{BASE_URL}/api/documentos/stats/por-tipo", headers=admin_headers)
        assert r.status_code == 200
        
        stats = r.json()
        assert isinstance(stats, list)
        
        # If there are stats, verify structure
        if stats:
            for item in stats:
                assert "tipo" in item
                assert "tipo_label" in item
                assert "total" in item
                assert "pendentes" in item
                assert "aprovados" in item
                assert "recusados" in item
                assert "taxa_aprovacao" in item
    
    def test_get_stats_vencendo(self, admin_headers):
        """GET /api/documentos/stats/vencendo - Documentos próximos a expirar"""
        r = requests.get(f"{BASE_URL}/api/documentos/stats/vencendo?dias=7", headers=admin_headers)
        assert r.status_code == 200
        
        docs = r.json()
        assert isinstance(docs, list)
        
        # If there are docs expiring, verify structure
        if docs:
            for doc in docs:
                assert "id" in doc
                assert "pedido_id" in doc
                assert "tipo" in doc


# ==================== BI DASHBOARD ENDPOINTS ====================

class TestBIDashboardEndpoints:
    """Tests for BI Dashboard endpoints"""
    
    def test_get_bi_matriculas(self, admin_headers):
        """GET /api/documentos/bi/matriculas - KPIs de matrículas"""
        r = requests.get(f"{BASE_URL}/api/documentos/bi/matriculas", headers=admin_headers)
        assert r.status_code == 200
        
        kpis = r.json()
        assert "total_pedidos" in kpis
        assert "pedidos_mes" in kpis
        assert "taxa_conversao" in kpis
        assert "por_status" in kpis
        assert isinstance(kpis["por_status"], dict)
    
    def test_get_bi_evolucao(self, admin_headers):
        """GET /api/documentos/bi/evolucao - Evolução mensal"""
        r = requests.get(f"{BASE_URL}/api/documentos/bi/evolucao?meses=6", headers=admin_headers)
        assert r.status_code == 200
        
        evolucao = r.json()
        assert isinstance(evolucao, list)
        
        # If there's data, verify structure
        if evolucao:
            for item in evolucao:
                assert "mes" in item
                assert "mes_label" in item
                assert "total" in item
                assert "convertidos" in item
                assert "taxa_conversao" in item
    
    def test_get_bi_reembolsos(self, admin_headers):
        """GET /api/documentos/bi/reembolsos - KPIs de reembolsos"""
        r = requests.get(f"{BASE_URL}/api/documentos/bi/reembolsos", headers=admin_headers)
        assert r.status_code == 200
        
        kpis = r.json()
        assert "total" in kpis
        assert "abertos" in kpis
        assert "aguardando" in kpis
        assert "no_financeiro" in kpis
        assert "pagos" in kpis
        assert "pendentes" in kpis
    
    def test_get_bi_pendencias(self, admin_headers):
        """GET /api/documentos/bi/pendencias - KPIs de pendências"""
        r = requests.get(f"{BASE_URL}/api/documentos/bi/pendencias", headers=admin_headers)
        assert r.status_code == 200
        
        kpis = r.json()
        assert "total" in kpis
        assert "pendentes" in kpis
        assert "em_aberto" in kpis
        assert "taxa_aprovacao" in kpis
    
    def test_get_bi_completo(self, admin_headers):
        """GET /api/documentos/bi/completo - Dashboard completo"""
        r = requests.get(f"{BASE_URL}/api/documentos/bi/completo", headers=admin_headers)
        assert r.status_code == 200
        
        dashboard = r.json()
        assert "matriculas" in dashboard
        assert "evolucao_mensal" in dashboard
        assert "reembolsos" in dashboard
        assert "pendencias" in dashboard
        assert "resumo" in dashboard
        
        # Verify resumo structure
        resumo = dashboard["resumo"]
        assert "total_matriculas" in resumo
        assert "matriculas_mes" in resumo
        assert "taxa_conversao" in resumo
        assert "pendencias_abertas" in resumo
        assert "reembolsos_pendentes" in resumo


# ==================== CRUD OPERATIONS ====================

class TestCRUDOperations:
    """Tests for CRUD operations on pendências documentais"""
    
    def test_criar_pendencia(self, admin_headers, pedido_id):
        """POST /api/documentos - Criar pendência documental"""
        payload = {
            "pedido_id": pedido_id,
            "tipo": "foto_3x4",
            "obrigatorio": True,
            "prioridade": "media",
            "prazo_dias": 10,
            "descricao": "TEST_Documento para teste automatizado"
        }
        r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        assert r.status_code == 200
        
        result = r.json()
        assert "id" in result
        assert "mensagem" in result
        assert "pendencia" in result
        
        # Verify pendencia data
        pendencia = result["pendencia"]
        assert pendencia["tipo"] == "foto_3x4"
        assert pendencia["prioridade"] == "media"
        assert pendencia["obrigatorio"] is True
        assert pendencia["status"] == "pendente"
        
        return result["id"]
    
    def test_criar_pendencias_padrao(self, admin_headers, pedido_id):
        """POST /api/documentos/padrao/{pedido_id} - Criar pendências padrão"""
        r = requests.post(
            f"{BASE_URL}/api/documentos/padrao/{pedido_id}?prazo_dias=7", 
            headers=admin_headers
        )
        assert r.status_code == 200
        
        result = r.json()
        assert "mensagem" in result
        assert "pendencias" in result
        assert len(result["pendencias"]) == 5  # 5 documentos padrão
        
        # Verify all are alta priority
        for p in result["pendencias"]:
            assert p["prioridade"] == "alta"
            assert p["obrigatorio"] is True
    
    def test_listar_pendencias_pedido(self, admin_headers, pedido_id):
        """GET /api/documentos/pedido/{pedido_id} - Listar pendências de um pedido"""
        r = requests.get(f"{BASE_URL}/api/documentos/pedido/{pedido_id}", headers=admin_headers)
        assert r.status_code == 200
        
        result = r.json()
        assert "total" in result
        assert "pendentes" in result
        assert "completo" in result
        assert "pendencias" in result
        assert isinstance(result["pendencias"], list)
    
    def test_buscar_pendencia_por_id(self, admin_headers, pedido_id):
        """GET /api/documentos/{pendencia_id} - Buscar pendência por ID"""
        # First create a pendencia
        payload = {
            "pedido_id": pedido_id,
            "tipo": "certidao_nascimento",
            "obrigatorio": False,
            "prioridade": "baixa",
            "prazo_dias": 30,
            "descricao": "TEST_Certidão para busca por ID"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Now search by ID
        r = requests.get(f"{BASE_URL}/api/documentos/{pendencia_id}", headers=admin_headers)
        assert r.status_code == 200
        
        pendencia = r.json()
        assert pendencia["id"] == pendencia_id
        assert pendencia["tipo"] == "certidao_nascimento"
        assert "status" in pendencia
        assert "prioridade" in pendencia
    
    def test_buscar_pendencia_inexistente(self, admin_headers):
        """GET /api/documentos/{pendencia_id} - 404 para pendência inexistente"""
        fake_id = str(uuid4())
        r = requests.get(f"{BASE_URL}/api/documentos/{fake_id}", headers=admin_headers)
        assert r.status_code == 404


# ==================== DOCUMENT WORKFLOW ====================

class TestDocumentWorkflow:
    """Tests for document submission and validation workflow"""
    
    def test_enviar_documento(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/enviar - Enviar documento"""
        # Create pendencia first
        payload = {
            "pedido_id": pedido_id,
            "tipo": "rg_frente",
            "obrigatorio": True,
            "prioridade": "alta",
            "prazo_dias": 5,
            "descricao": "TEST_RG para teste de envio"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Submit document
        envio_payload = {
            "arquivo_url": "https://storage.example.com/test_rg.pdf",
            "arquivo_nome": "rg_teste.pdf",
            "arquivo_tamanho": "1.2 MB"
        }
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar", 
            headers=admin_headers, 
            json=envio_payload
        )
        assert r.status_code == 200
        
        result = r.json()
        assert result["mensagem"] == "Documento enviado com sucesso"
        assert result["pendencia"]["status"] == "enviado"
        assert result["pendencia"]["arquivo_url"] == envio_payload["arquivo_url"]
        
        return pendencia_id
    
    def test_enviar_documento_ja_enviado(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/enviar - Erro se já foi enviado"""
        # Create and submit first
        payload = {
            "pedido_id": pedido_id,
            "tipo": "rg_verso",
            "obrigatorio": True,
            "prioridade": "alta",
            "prazo_dias": 5,
            "descricao": "TEST_RG verso para teste duplicado"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        envio_payload = {
            "arquivo_url": "https://storage.example.com/test_rg_verso.pdf",
            "arquivo_nome": "rg_verso.pdf",
            "arquivo_tamanho": "900 KB"
        }
        requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar",
            headers=admin_headers,
            json=envio_payload
        )
        
        # Try to send again
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar",
            headers=admin_headers,
            json=envio_payload
        )
        assert r.status_code == 400
    
    def test_validar_aprovar_documento(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/validar - Aprovar documento"""
        # Create, submit, then approve
        payload = {
            "pedido_id": pedido_id,
            "tipo": "cpf",
            "obrigatorio": True,
            "prioridade": "alta",
            "prazo_dias": 5,
            "descricao": "TEST_CPF para aprovação"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Submit
        envio_payload = {
            "arquivo_url": "https://storage.example.com/cpf.pdf",
            "arquivo_nome": "cpf.pdf",
            "arquivo_tamanho": "200 KB"
        }
        requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar",
            headers=admin_headers,
            json=envio_payload
        )
        
        # Approve
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/validar",
            headers=admin_headers,
            json={"aprovado": True}
        )
        assert r.status_code == 200
        
        result = r.json()
        assert result["mensagem"] == "Documento aprovado com sucesso"
        assert result["pendencia"]["status"] == "aprovado"
    
    def test_validar_recusar_documento(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/validar - Recusar documento"""
        # Create, submit, then reject
        payload = {
            "pedido_id": pedido_id,
            "tipo": "comprovante_residencia",
            "obrigatorio": False,
            "prioridade": "media",
            "prazo_dias": 10,
            "descricao": "TEST_Comprovante para recusa"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Submit
        envio_payload = {
            "arquivo_url": "https://storage.example.com/comprovante.pdf",
            "arquivo_nome": "comprovante.pdf",
            "arquivo_tamanho": "500 KB"
        }
        requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar",
            headers=admin_headers,
            json=envio_payload
        )
        
        # Reject
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/validar",
            headers=admin_headers,
            json={
                "aprovado": False,
                "motivo": "Documento está ilegível. Por favor, envie uma cópia mais clara."
            }
        )
        assert r.status_code == 200
        
        result = r.json()
        assert result["mensagem"] == "Documento recusado"
        assert result["pendencia"]["status"] == "recusado"
        assert "Documento está ilegível" in result["pendencia"]["motivo_recusa"]
    
    def test_validar_recusar_sem_motivo(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/validar - Erro ao recusar sem motivo"""
        # Create and submit
        payload = {
            "pedido_id": pedido_id,
            "tipo": "historico_escolar",
            "obrigatorio": True,
            "prioridade": "alta",
            "prazo_dias": 7,
            "descricao": "TEST_Histórico para teste sem motivo"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Submit
        envio_payload = {
            "arquivo_url": "https://storage.example.com/historico.pdf",
            "arquivo_nome": "historico.pdf",
            "arquivo_tamanho": "1 MB"
        }
        requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/enviar",
            headers=admin_headers,
            json=envio_payload
        )
        
        # Try to reject without motivo
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/validar",
            headers=admin_headers,
            json={"aprovado": False}
        )
        assert r.status_code == 400
    
    def test_validar_documento_nao_enviado(self, admin_headers, pedido_id):
        """POST /api/documentos/{pendencia_id}/validar - Erro se não foi enviado"""
        # Create pendencia only (don't submit)
        payload = {
            "pedido_id": pedido_id,
            "tipo": "laudo_medico",
            "obrigatorio": False,
            "prioridade": "baixa",
            "prazo_dias": 30,
            "descricao": "TEST_Laudo para teste não enviado"
        }
        create_r = requests.post(f"{BASE_URL}/api/documentos", headers=admin_headers, json=payload)
        pendencia_id = create_r.json()["id"]
        
        # Try to approve without sending
        r = requests.post(
            f"{BASE_URL}/api/documentos/{pendencia_id}/validar",
            headers=admin_headers,
            json={"aprovado": True}
        )
        assert r.status_code == 422  # Business rule error


# ==================== VALIDATION QUEUE ====================

class TestValidationQueue:
    """Tests for validation queue endpoint"""
    
    def test_get_fila_validacao(self, admin_headers):
        """GET /api/documentos/validacao/fila - Fila de validação"""
        r = requests.get(f"{BASE_URL}/api/documentos/validacao/fila?limite=20", headers=admin_headers)
        assert r.status_code == 200
        
        result = r.json()
        assert "total" in result
        assert "pendencias" in result
        assert isinstance(result["pendencias"], list)
        
        # If there are items in queue, verify structure
        if result["pendencias"]:
            for p in result["pendencias"]:
                assert "id" in p
                assert "tipo" in p
                assert "status" in p
                assert p["status"] == "enviado"


# ==================== AUTHENTICATION ====================

class TestAuthentication:
    """Tests for authentication requirements"""
    
    def test_endpoint_requires_auth(self):
        """Endpoints should require authentication"""
        # No auth header
        r = requests.get(f"{BASE_URL}/api/documentos/tipos")
        assert r.status_code == 401
    
    def test_assistente_can_access(self, assistente_headers):
        """Assistente role should have access"""
        r = requests.get(f"{BASE_URL}/api/documentos/tipos", headers=assistente_headers)
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
