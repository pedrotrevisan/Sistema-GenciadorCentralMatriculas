"""
Test Suite for Sistema Central de Matrículas SENAI CIMATEC
Focus: Importação em Lote endpoints and Dashboard 2.0 Analytics
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@senai.br", "senha": "admin123"}
ASSISTENTE_CREDENTIALS = {"email": "assistente@senai.br", "senha": "assistente123"}
CONSULTOR_CREDENTIALS = {"email": "consultor@senai.br", "senha": "consultor123"}


class TestHealthEndpoints:
    """Health check endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SENAI" in data["message"]
        print(f"✓ API root: {data['message']}")
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health: {data['status']}")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "usuario" in data
        assert data["usuario"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['usuario']['email']}")
        return data["token"]
    
    def test_assistente_login(self):
        """Test assistente login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ASSISTENTE_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "assistente"
        print(f"✓ Assistente login successful: {data['usuario']['email']}")
        return data["token"]
    
    def test_consultor_login(self):
        """Test consultor login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONSULTOR_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["usuario"]["role"] == "consultor"
        print(f"✓ Consultor login successful: {data['usuario']['email']}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "senha": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")


class TestImportacaoTemplate:
    """Tests for GET /api/importacao/template"""
    
    def test_download_template_returns_excel(self):
        """Test template download returns valid Excel file"""
        response = requests.get(f"{BASE_URL}/api/importacao/template")
        assert response.status_code == 200
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        assert 'spreadsheet' in content_type or 'excel' in content_type or 'octet-stream' in content_type
        
        # Check content disposition
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disp
        assert 'template_importacao_alunos.xlsx' in content_disp
        
        # Check file size (should be > 0)
        assert len(response.content) > 0
        print(f"✓ Template downloaded: {len(response.content)} bytes")
    
    def test_template_is_valid_xlsx(self):
        """Test template is a valid XLSX file"""
        response = requests.get(f"{BASE_URL}/api/importacao/template")
        assert response.status_code == 200
        
        # XLSX files start with PK (ZIP signature)
        assert response.content[:2] == b'PK'
        print("✓ Template is valid XLSX format")


class TestImportacaoValidar:
    """Tests for POST /api/importacao/validar"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json()["token"]
    
    @pytest.fixture
    def curso_id(self, admin_token):
        """Get first active curso ID"""
        response = requests.get(f"{BASE_URL}/api/cursos")
        cursos = response.json()
        active_cursos = [c for c in cursos if c.get('ativo', True)]
        return active_cursos[0]["id"] if active_cursos else None
    
    def test_validar_requires_auth(self):
        """Test validation endpoint requires authentication"""
        # Create a simple CSV content
        csv_content = "nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf\n"
        csv_content += "Test User,12345678901,test@test.com,71999999999,01/01/2000,123456,41820000,Rua Test,123,Centro,Salvador,BA"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar?curso_id=test",
            files=files
        )
        assert response.status_code == 401
        print("✓ Validation requires authentication")
    
    def test_validar_requires_curso_id(self, admin_token, curso_id):
        """Test validation requires curso_id parameter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        csv_content = "nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf\n"
        csv_content += "Test User,12345678901,test@test.com,71999999999,01/01/2000,123456,41820000,Rua Test,123,Centro,Salvador,BA"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar",
            files=files,
            headers=headers
        )
        # Should fail without curso_id
        assert response.status_code == 422  # Missing required parameter
        print("✓ Validation requires curso_id parameter")
    
    def test_validar_invalid_file_format(self, admin_token, curso_id):
        """Test validation rejects invalid file formats"""
        if not curso_id:
            pytest.skip("No curso available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        files = {'file': ('test.txt', 'invalid content', 'text/plain')}
        
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar?curso_id={curso_id}",
            files=files,
            headers=headers
        )
        assert response.status_code == 400
        print("✓ Invalid file format rejected")
    
    def test_validar_missing_columns(self, admin_token, curso_id):
        """Test validation detects missing required columns"""
        if not curso_id:
            pytest.skip("No curso available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        # CSV with missing columns
        csv_content = "nome,cpf\nTest User,12345678901"
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar?curso_id={curso_id}",
            files=files,
            headers=headers
        )
        assert response.status_code == 400
        assert "obrigatórias" in response.json().get("detail", "").lower() or "faltantes" in response.json().get("detail", "").lower()
        print("✓ Missing columns detected")
    
    def test_validar_valid_csv(self, admin_token, curso_id):
        """Test validation with valid CSV data"""
        if not curso_id:
            pytest.skip("No curso available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Valid CSV with all required columns
        csv_content = """nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf
João Carlos Silva,11122233344,joao.test@email.com,71999998888,15/03/1995,12345678,41820000,Rua das Flores,123,Pituba,Salvador,BA"""
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar?curso_id={curso_id}",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_linhas" in data
        assert "linhas_validas" in data
        assert "linhas_com_erro" in data
        assert "preview" in data
        print(f"✓ Valid CSV processed: {data['total_linhas']} lines, {data['linhas_validas']} valid")
    
    def test_validar_detects_invalid_cpf(self, admin_token, curso_id):
        """Test validation detects invalid CPF"""
        if not curso_id:
            pytest.skip("No curso available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # CSV with invalid CPF (too short)
        csv_content = """nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf
João Carlos Silva,123,joao.test2@email.com,71999998888,15/03/1995,12345678,41820000,Rua das Flores,123,Pituba,Salvador,BA"""
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/importacao/validar?curso_id={curso_id}",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["linhas_com_erro"] > 0
        # Check that error mentions CPF
        if data["erros"]:
            error_text = str(data["erros"])
            assert "cpf" in error_text.lower() or "dígitos" in error_text.lower()
        print(f"✓ Invalid CPF detected: {data['linhas_com_erro']} errors")


class TestImportacaoExecutar:
    """Tests for POST /api/importacao/executar"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json()["token"]
    
    @pytest.fixture
    def curso_data(self, admin_token):
        """Get first active curso"""
        response = requests.get(f"{BASE_URL}/api/cursos")
        cursos = response.json()
        active_cursos = [c for c in cursos if c.get('ativo', True)]
        return active_cursos[0] if active_cursos else None
    
    @pytest.fixture
    def projeto_data(self, admin_token):
        """Get first active projeto"""
        response = requests.get(f"{BASE_URL}/api/projetos")
        projetos = response.json()
        active_projetos = [p for p in projetos if p.get('ativo', True)]
        return active_projetos[0] if active_projetos else None
    
    def test_executar_requires_auth(self):
        """Test execution endpoint requires authentication"""
        csv_content = "nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf\n"
        csv_content += "Test User,12345678901,test@test.com,71999999999,01/01/2000,123456,41820000,Rua Test,123,Centro,Salvador,BA"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/importacao/executar?curso_id=test&curso_nome=Test",
            files=files
        )
        assert response.status_code == 401
        print("✓ Execution requires authentication")
    
    def test_executar_requires_curso_params(self, admin_token):
        """Test execution requires curso_id and curso_nome"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        csv_content = "nome,cpf,email,telefone,data_nascimento,rg,cep,logradouro,numero,bairro,cidade,uf\n"
        csv_content += "Test User,12345678901,test@test.com,71999999999,01/01/2000,123456,41820000,Rua Test,123,Centro,Salvador,BA"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/importacao/executar",
            files=files,
            headers=headers
        )
        assert response.status_code == 422  # Missing required parameters
        print("✓ Execution requires curso parameters")


class TestDashboardAnalytics:
    """Tests for GET /api/pedidos/analytics (Dashboard 2.0)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json()["token"]
    
    @pytest.fixture
    def consultor_token(self):
        """Get consultor token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONSULTOR_CREDENTIALS)
        return response.json()["token"]
    
    def test_analytics_requires_auth(self):
        """Test analytics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pedidos/analytics")
        assert response.status_code == 401
        print("✓ Analytics requires authentication")
    
    def test_analytics_admin_access(self, admin_token):
        """Test admin can access analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/pedidos/analytics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "funil" in data
        assert "tempo_medio_dias" in data
        assert "top_empresas" in data
        assert "top_projetos" in data
        assert "pedidos_criticos" in data
        assert "total_alunos" in data
        assert "matriculas_por_mes" in data
        assert "taxa_conversao" in data
        assert "total_pedidos" in data
        
        print(f"✓ Admin analytics: {data['total_pedidos']} pedidos, {data['total_alunos']} alunos")
    
    def test_analytics_funil_structure(self, admin_token):
        """Test funil data structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/pedidos/analytics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify funil structure
        funil = data["funil"]
        assert isinstance(funil, list)
        
        expected_statuses = ['pendente', 'em_analise', 'documentacao_pendente', 'aprovado', 'realizado', 'exportado']
        funil_statuses = [f["status"] for f in funil]
        
        for status in expected_statuses:
            assert status in funil_statuses, f"Missing status: {status}"
        
        # Each funil item should have status, label, total
        for item in funil:
            assert "status" in item
            assert "label" in item
            assert "total" in item
            assert isinstance(item["total"], int)
        
        print(f"✓ Funil structure valid: {len(funil)} statuses")
    
    def test_analytics_consultor_access(self, consultor_token):
        """Test consultor can access analytics (filtered by their pedidos)"""
        headers = {"Authorization": f"Bearer {consultor_token}"}
        response = requests.get(f"{BASE_URL}/api/pedidos/analytics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Consultor should see filtered data
        assert "funil" in data
        assert "total_pedidos" in data
        print(f"✓ Consultor analytics: {data['total_pedidos']} pedidos (filtered)")


class TestAuxiliaryEndpoints:
    """Tests for auxiliary data endpoints"""
    
    def test_list_cursos(self):
        """Test listing cursos"""
        response = requests.get(f"{BASE_URL}/api/cursos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "nome" in data[0]
        print(f"✓ Cursos: {len(data)} items")
    
    def test_list_projetos(self):
        """Test listing projetos"""
        response = requests.get(f"{BASE_URL}/api/projetos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "nome" in data[0]
        print(f"✓ Projetos: {len(data)} items")
    
    def test_list_empresas(self):
        """Test listing empresas"""
        response = requests.get(f"{BASE_URL}/api/empresas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "nome" in data[0]
        print(f"✓ Empresas: {len(data)} items")
    
    def test_list_status_pedido(self):
        """Test listing status options"""
        response = requests.get(f"{BASE_URL}/api/status-pedido")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "value" in data[0]
            assert "label" in data[0]
        print(f"✓ Status options: {len(data)} items")


class TestDashboardEndpoint:
    """Tests for GET /api/pedidos/dashboard"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json()["token"]
    
    def test_dashboard_requires_auth(self):
        """Test dashboard endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pedidos/dashboard")
        assert response.status_code == 401
        print("✓ Dashboard requires authentication")
    
    def test_dashboard_returns_data(self, admin_token):
        """Test dashboard returns expected data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/pedidos/dashboard", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "contagem_status" in data
        assert "pedidos_recentes" in data
        print(f"✓ Dashboard: {len(data['pedidos_recentes'])} recent pedidos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
