"""Tests for Cancelamento and Templates API endpoints"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


# ==================== CANCELAMENTO ENDPOINTS ====================

class TestCancelamentoTipos:
    """Tests for /api/cancelamento/tipos endpoint"""
    
    def test_listar_tipos_cancelamento_success(self):
        """Should return list of cancellation types"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/tipos")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "tipos" in data
        assert "descricoes" in data
        assert isinstance(data["tipos"], list)
        
        # Validate types
        tipos_values = [t["value"] for t in data["tipos"]]
        assert "solicitado_candidato" in tipos_values
        assert "senai" in tipos_values
        assert "prazo_expirado" in tipos_values
        assert "nao_atende_requisito" in tipos_values
        
        print(f"✓ Found {len(data['tipos'])} cancellation types")


class TestCancelamentoResponsabilidades:
    """Tests for /api/cancelamento/responsabilidades endpoint"""
    
    def test_listar_responsabilidades_success(self):
        """Should return responsibilities by status"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/responsabilidades")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "responsabilidades" in data
        assert "prazo_nrm_horas" in data
        assert "fluxo" in data
        
        # Validate prazo NRM
        assert data["prazo_nrm_horas"] == 48
        
        # Validate responsabilities mapping
        responsabilidades = data["responsabilidades"]
        assert responsabilidades.get("pre_analise") == "CAC"
        assert responsabilidades.get("matriculado") == "CAA"
        
        print(f"✓ Responsabilidades loaded correctly with {len(responsabilidades)} statuses")


class TestCancelamentoDocumentos:
    """Tests for /api/cancelamento/documentos/* endpoints"""
    
    def test_listar_documentos_escolaridade_success(self):
        """Should return TOTVS education documents"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/documentos/escolaridade")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documentos" in data
        assert "nota" in data
        assert len(data["documentos"]) >= 5
        
        # Validate known document codes
        codigos = [d["codigo"] for d in data["documentos"]]
        assert "136" in codigos
        assert "137" in codigos
        assert "93" in codigos
        assert "182" in codigos
        assert "165" in codigos
        
        print(f"✓ Found {len(data['documentos'])} education documents")
    
    def test_get_documento_especifico_success(self):
        """Should return specific document by code"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/documentos/escolaridade/182")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == "182"
        assert "nome" in data
        assert "descricao" in data
        
        print(f"✓ Document 182: {data['nome']}")
    
    def test_get_documento_not_found(self):
        """Should return 404 for unknown document code"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/documentos/escolaridade/999")
        
        assert response.status_code == 404


class TestCancelamentoFluxoValidacao:
    """Tests for /api/cancelamento/documentos/fluxo-validacao endpoint"""
    
    def test_get_fluxos_validacao_success(self):
        """Should return validation flows for education documents"""
        response = requests.get(f"{BASE_URL}/api/cancelamento/documentos/fluxo-validacao")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "fluxos" in data
        assert "instrucoes" in data
        
        fluxos = data["fluxos"]
        assert "historico_escolar" in fluxos
        assert "atestado_matricula" in fluxos
        assert "atestado_conclusao" in fluxos
        
        # Validate historico_escolar flow
        historico = fluxos["historico_escolar"]
        assert "documentos_validar" in historico
        assert "documentos_incluir" in historico
        assert "status_final" in historico
        assert historico["status_final"] == "MAC"
        
        print(f"✓ Found {len(fluxos)} validation flows")


class TestCancelamentoValidarEscolaridade:
    """Tests for /api/cancelamento/documentos/validar-escolaridade endpoint"""
    
    def test_validar_historico_escolar_success(self):
        """Should return actions for historico_escolar validation"""
        response = requests.post(
            f"{BASE_URL}/api/cancelamento/documentos/validar-escolaridade",
            params={"tipo_documento": "historico_escolar", "data_entrega": "15/01/2026"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tipo_documento"] == "historico_escolar"
        assert "acoes" in data
        assert data["status_final"] == "MAC"
        assert len(data["acoes"]) >= 4  # 3 validar + 1 incluir
        
        print(f"✓ historico_escolar: {len(data['acoes'])} actions")
    
    def test_validar_atestado_conclusao_success(self):
        """Should return actions for atestado_conclusao validation"""
        response = requests.post(
            f"{BASE_URL}/api/cancelamento/documentos/validar-escolaridade",
            params={"tipo_documento": "atestado_conclusao"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tipo_documento"] == "atestado_conclusao"
        assert "165" in str(data["acoes"])  # Should include document 165
        
        print(f"✓ atestado_conclusao validated")
    
    def test_validar_tipo_invalido(self):
        """Should return 400 for invalid document type"""
        response = requests.post(
            f"{BASE_URL}/api/cancelamento/documentos/validar-escolaridade",
            params={"tipo_documento": "tipo_invalido"}
        )
        
        assert response.status_code == 400


# ==================== TEMPLATES ENDPOINTS ====================

class TestTemplatesEmail:
    """Tests for /api/regras/templates/email endpoints"""
    
    def test_listar_templates_email_success(self):
        """Should return available email templates"""
        response = requests.get(f"{BASE_URL}/api/regras/templates/email")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) >= 5
        
        # Validate known templates
        nomes = [t["nome"] for t in templates]
        assert "documentos_pendentes" in nomes
        assert "confirmacao_matricula" in nomes
        assert "aguardando_pagamento" in nomes
        
        print(f"✓ Found {len(templates)} email templates")
    
    def test_render_email_template_success(self):
        """Should render email template with data"""
        response = requests.post(
            f"{BASE_URL}/api/regras/templates/email/render",
            json={
                "tipo": "documentos_pendentes",
                "dados": {
                    "aluno_nome": "João Silva",
                    "curso_nome": "Técnico em Automação",
                    "protocolo": "CM-2026-0001",
                    "documentos_lista": "<li>RG</li><li>CPF</li>",
                    "documentos_lista_texto": "• RG\n• CPF",
                    "dias_restantes": "3",
                    "link_portal": "https://portal.senai.br"
                },
                "formato": "html"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "assunto" in data
        assert "corpo" in data
        assert "João Silva" in data["corpo"]
        
        print(f"✓ Email template rendered: {data['assunto']}")
    
    def test_render_email_template_missing_fields(self):
        """Should return 400 when required fields are missing"""
        response = requests.post(
            f"{BASE_URL}/api/regras/templates/email/render",
            json={
                "tipo": "documentos_pendentes",
                "dados": {"aluno_nome": "João"},  # Missing required fields
                "formato": "html"
            }
        )
        
        assert response.status_code == 400
    
    def test_render_email_template_invalid_type(self):
        """Should return 404 for invalid template type"""
        response = requests.post(
            f"{BASE_URL}/api/regras/templates/email/render",
            json={
                "tipo": "template_inexistente",
                "dados": {},
                "formato": "html"
            }
        )
        
        assert response.status_code == 404


class TestTemplatesWhatsApp:
    """Tests for /api/regras/templates/whatsapp endpoints"""
    
    def test_listar_templates_whatsapp_success(self):
        """Should return available WhatsApp templates"""
        response = requests.get(f"{BASE_URL}/api/regras/templates/whatsapp")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) >= 5
        
        nomes = [t["nome"] for t in templates]
        assert "documentos_pendentes" in nomes
        assert "confirmacao_matricula" in nomes
        
        print(f"✓ Found {len(templates)} WhatsApp templates")
    
    def test_render_whatsapp_template_success(self):
        """Should render WhatsApp template with data and link"""
        response = requests.post(
            f"{BASE_URL}/api/regras/templates/whatsapp/render",
            json={
                "tipo": "documentos_pendentes",
                "dados": {
                    "aluno_nome": "Maria Santos",
                    "curso_nome": "Técnico em Mecânica",
                    "protocolo": "CM-2026-0002",
                    "documentos_lista": "• RG\n• Comprovante de Residência",
                    "dias_restantes": "2"
                },
                "telefone": "71999999999"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mensagem" in data
        assert "link_whatsapp" in data
        assert "Maria Santos" in data["mensagem"]
        assert "wa.me" in data["link_whatsapp"]
        
        print(f"✓ WhatsApp template rendered with link")
    
    def test_render_whatsapp_without_phone(self):
        """Should render template without generating link when phone is missing"""
        response = requests.post(
            f"{BASE_URL}/api/regras/templates/whatsapp/render",
            json={
                "tipo": "lembrete_documentos",
                "dados": {
                    "aluno_nome": "Pedro Costa",
                    "curso_nome": "Técnico em Eletrônica",
                    "protocolo": "CM-2026-0003",
                    "dias_restantes": "1"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mensagem" in data
        assert "link_whatsapp" not in data  # No phone provided
        
        print(f"✓ WhatsApp template rendered without link")


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
