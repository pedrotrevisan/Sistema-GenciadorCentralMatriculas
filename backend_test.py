#!/usr/bin/env python3
"""
Backend API Testing for Sistema Central de Matrículas - SENAI CIMATEC
Tests all API endpoints with proper authentication and role-based access
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SenaiMatriculasAPITester:
    def __init__(self, base_url="https://synapse-hub-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    token: str = None, expected_status: int = 200) -> tuple:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}", {}

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            return success, f"Status: {response.status_code}", response_data

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}", {}

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        success, details, data = self.make_request('GET', '', expected_status=200)
        self.log_test("Root endpoint (/api/)", success, details)
        
        # Test health endpoint
        success, details, data = self.make_request('GET', 'health', expected_status=200)
        self.log_test("Health endpoint (/api/health)", success, details)

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Authentication...")
        
        # Test login for all user types
        test_users = [
            {"email": "admin@senai.br", "senha": "admin123", "role": "admin"},
            {"email": "assistente@senai.br", "senha": "assistente123", "role": "assistente"},
            {"email": "consultor@senai.br", "senha": "consultor123", "role": "consultor"}
        ]
        
        for user_data in test_users:
            success, details, response = self.make_request(
                'POST', 'auth/login', 
                {"email": user_data["email"], "senha": user_data["senha"]},
                expected_status=200
            )
            
            if success and 'token' in response:
                self.tokens[user_data["role"]] = response['token']
                self.users[user_data["role"]] = response.get('usuario', {})
                self.log_test(f"Login {user_data['role']}", True)
            else:
                self.log_test(f"Login {user_data['role']}", False, details)

        # Test /auth/me endpoint for each logged in user
        for role, token in self.tokens.items():
            success, details, response = self.make_request(
                'GET', 'auth/me', token=token, expected_status=200
            )
            self.log_test(f"Get current user ({role})", success, details)

    def test_auxiliary_endpoints(self):
        """Test auxiliary data endpoints (no auth required)"""
        print("\n🔍 Testing Auxiliary Data Endpoints...")
        
        endpoints = ['cursos', 'projetos', 'empresas', 'status-pedido']
        
        for endpoint in endpoints:
            success, details, response = self.make_request('GET', endpoint, expected_status=200)
            
            # Check if response is a list and has data
            if success and isinstance(response, list) and len(response) > 0:
                self.log_test(f"Get {endpoint}", True, f"Returned {len(response)} items")
            else:
                self.log_test(f"Get {endpoint}", False, f"{details} - Empty or invalid response")

    def test_pedidos_endpoints(self):
        """Test pedidos (orders) endpoints"""
        print("\n🔍 Testing Pedidos Endpoints...")
        
        # Test dashboard endpoint for each user type
        for role, token in self.tokens.items():
            success, details, response = self.make_request(
                'GET', 'pedidos/dashboard', token=token, expected_status=200
            )
            self.log_test(f"Dashboard ({role})", success, details)

        # Test list pedidos for each user type
        for role, token in self.tokens.items():
            success, details, response = self.make_request(
                'GET', 'pedidos', token=token, expected_status=200
            )
            self.log_test(f"List pedidos ({role})", success, details)

        # Test create pedido (only for users with permission)
        if 'consultor' in self.tokens:
            pedido_data = {
                "curso_id": "1",
                "curso_nome": "Técnico em Mecatrônica",
                "projeto_id": "1",
                "projeto_nome": "Projeto SENAI de Inovação",
                "observacoes": "Teste automatizado",
                "alunos": [
                    {
                        "nome": "João Silva Teste",
                        "cpf": "12345678901",
                        "email": "joao.teste@email.com",
                        "telefone": "11999999999",
                        "data_nascimento": "1990-01-01",
                        "rg": "123456789",
                        "rg_orgao_emissor": "SSP",
                        "rg_uf": "SP",
                        "endereco_cep": "01234-567",
                        "endereco_logradouro": "Rua Teste",
                        "endereco_numero": "123",
                        "endereco_bairro": "Centro",
                        "endereco_cidade": "São Paulo",
                        "endereco_uf": "SP"
                    }
                ]
            }
            
            success, details, response = self.make_request(
                'POST', 'pedidos', pedido_data, 
                token=self.tokens['consultor'], expected_status=201
            )
            
            if success and 'id' in response:
                pedido_id = response['id']
                self.log_test("Create pedido (consultor)", True)
                
                # Test get specific pedido
                success, details, response = self.make_request(
                    'GET', f'pedidos/{pedido_id}', 
                    token=self.tokens['consultor'], expected_status=200
                )
                self.log_test("Get specific pedido", success, details)
                
                # Test update status (assistente/admin only)
                if 'assistente' in self.tokens:
                    status_data = {
                        "status": "em_analise",
                        "motivo": "Teste de atualização de status"
                    }
                    success, details, response = self.make_request(
                        'PATCH', f'pedidos/{pedido_id}/status', status_data,
                        token=self.tokens['assistente'], expected_status=200
                    )
                    self.log_test("Update pedido status (assistente)", success, details)
                    
            else:
                self.log_test("Create pedido (consultor)", False, details)

    def test_usuarios_endpoints(self):
        """Test user management endpoints (admin only)"""
        print("\n🔍 Testing User Management Endpoints...")
        
        if 'admin' not in self.tokens:
            self.log_test("User management tests", False, "No admin token available")
            return

        admin_token = self.tokens['admin']
        
        # Test list users
        success, details, response = self.make_request(
            'GET', 'usuarios', token=admin_token, expected_status=200
        )
        self.log_test("List users (admin)", success, details)
        
        # Test create new user
        new_user_data = {
            "nome": "Usuário Teste",
            "email": f"teste_{datetime.now().strftime('%H%M%S')}@senai.br",
            "senha": "teste123",
            "role": "consultor"
        }
        
        success, details, response = self.make_request(
            'POST', 'auth/register', new_user_data, expected_status=201
        )
        
        if success and 'id' in response:
            user_id = response['id']
            self.log_test("Create new user", True)
            
            # Test get specific user
            success, details, response = self.make_request(
                'GET', f'usuarios/{user_id}', 
                token=admin_token, expected_status=200
            )
            self.log_test("Get specific user", success, details)
            
            # Test update user
            update_data = {
                "nome": "Usuário Teste Atualizado",
                "role": "assistente",
                "ativo": True
            }
            success, details, response = self.make_request(
                'PATCH', f'usuarios/{user_id}', update_data,
                token=admin_token, expected_status=200
            )
            self.log_test("Update user", success, details)
            
            # Test delete user
            success, details, response = self.make_request(
                'DELETE', f'usuarios/{user_id}', 
                token=admin_token, expected_status=200
            )
            self.log_test("Delete user", success, details)
            
        else:
            self.log_test("Create new user", False, details)

    def test_export_functionality(self):
        """Test TOTVS export functionality"""
        print("\n🔍 Testing Export Functionality...")
        
        # Test export (admin/assistente only)
        for role in ['admin', 'assistente']:
            if role in self.tokens:
                success, details, response = self.make_request(
                    'GET', 'pedidos/exportar/totvs?formato=xlsx', 
                    token=self.tokens[role], expected_status=200
                )
                self.log_test(f"Export TOTVS ({role})", success, details)

    def test_authorization(self):
        """Test role-based authorization"""
        print("\n🔍 Testing Authorization...")
        
        # Test consultor trying to access admin endpoints
        if 'consultor' in self.tokens:
            success, details, response = self.make_request(
                'GET', 'usuarios', 
                token=self.tokens['consultor'], expected_status=403
            )
            # Should fail with 403
            auth_success = not success and "403" in details
            self.log_test("Consultor blocked from users endpoint", auth_success, 
                         "Should be blocked" if auth_success else "Authorization not working")

        # Test assistente trying to create users
        if 'assistente' in self.tokens:
            success, details, response = self.make_request(
                'POST', 'auth/register', 
                {"nome": "Test", "email": "test@test.com", "senha": "test123"},
                token=self.tokens['assistente'], expected_status=403
            )
            # Should fail with 403 or similar
            auth_success = not success
            self.log_test("Assistente blocked from creating users", auth_success,
                         "Should be blocked" if auth_success else "Authorization not working")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting SENAI CIMATEC Matrículas API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        try:
            self.test_health_endpoints()
            self.test_authentication()
            self.test_auxiliary_endpoints()
            self.test_pedidos_endpoints()
            self.test_usuarios_endpoints()
            self.test_export_functionality()
            self.test_authorization()
            
        except Exception as e:
            print(f"\n💥 Test suite failed with error: {str(e)}")
            return False
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Save detailed results
        results = {
            "summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "success_rate": (self.tests_passed/self.tests_run)*100,
                "timestamp": datetime.now().isoformat()
            },
            "test_details": self.test_results,
            "tokens_obtained": list(self.tokens.keys()),
            "base_url": self.base_url
        }
        
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    tester = SenaiMatriculasAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())