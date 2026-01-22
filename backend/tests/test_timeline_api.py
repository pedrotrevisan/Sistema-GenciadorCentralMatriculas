"""
Test Timeline de Auditoria API
Tests for GET /api/pedidos/{id}/timeline endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTimelineAPI:
    """Tests for Timeline de Auditoria endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@senai.br", "senha": "admin123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get a pedido ID for testing
        pedidos_response = self.session.get(f"{BASE_URL}/api/pedidos?pagina=1&por_pagina=1")
        assert pedidos_response.status_code == 200
        pedidos = pedidos_response.json()["pedidos"]
        if pedidos:
            self.pedido_id = pedidos[0]["id"]
            self.pedido_protocolo = pedidos[0]["numero_protocolo"]
        else:
            self.pedido_id = None
            self.pedido_protocolo = None
    
    def test_timeline_endpoint_returns_200(self):
        """Test that timeline endpoint returns 200 for valid pedido"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_timeline_returns_required_fields(self):
        """Test that timeline response contains all required fields"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level fields
        assert "pedido_id" in data, "Missing pedido_id field"
        assert "numero_protocolo" in data, "Missing numero_protocolo field"
        assert "total_eventos" in data, "Missing total_eventos field"
        assert "timeline" in data, "Missing timeline field"
        
        # Verify pedido_id matches
        assert data["pedido_id"] == self.pedido_id
    
    def test_timeline_event_has_required_fields(self):
        """Test that each timeline event has all required fields"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        # Check first event has all required fields
        event = timeline[0]
        required_fields = ["id", "acao", "acao_label", "icon", "color", "usuario_nome", "timestamp"]
        
        for field in required_fields:
            assert field in event, f"Missing required field: {field}"
    
    def test_timeline_event_acao_label_is_translated(self):
        """Test that acao_label is properly translated (not raw action code)"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        
        # acao_label should be a human-readable label, not the raw action code
        # For CRIACAO action, it should be "Solicitação Criada"
        if event["acao"] == "CRIACAO":
            assert event["acao_label"] == "Solicitação Criada", f"Expected 'Solicitação Criada', got '{event['acao_label']}'"
    
    def test_timeline_event_has_valid_icon(self):
        """Test that timeline event has a valid icon"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        valid_icons = ["plus", "check", "check-circle", "x", "file", "download", "refresh", "circle", "alert"]
        
        assert event["icon"] in valid_icons, f"Invalid icon: {event['icon']}"
    
    def test_timeline_event_has_valid_color(self):
        """Test that timeline event has a valid color"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        valid_colors = ["blue", "green", "yellow", "orange", "red", "gray"]
        
        assert event["color"] in valid_colors, f"Invalid color: {event['color']}"
    
    def test_timeline_event_has_usuario_nome(self):
        """Test that timeline event has usuario_nome (not just usuario_id)"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        
        assert "usuario_nome" in event, "Missing usuario_nome field"
        assert event["usuario_nome"] is not None, "usuario_nome should not be None"
        assert len(event["usuario_nome"]) > 0, "usuario_nome should not be empty"
    
    def test_timeline_event_has_timestamp(self):
        """Test that timeline event has a valid timestamp"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        
        assert "timestamp" in event, "Missing timestamp field"
        assert event["timestamp"] is not None, "timestamp should not be None"
        # Timestamp should be in ISO format
        assert "T" in event["timestamp"], "timestamp should be in ISO format"
    
    def test_timeline_total_eventos_matches_timeline_length(self):
        """Test that total_eventos matches the actual timeline length"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        
        assert data["total_eventos"] == len(data["timeline"]), \
            f"total_eventos ({data['total_eventos']}) doesn't match timeline length ({len(data['timeline'])})"
    
    def test_timeline_returns_404_for_invalid_pedido(self):
        """Test that timeline returns 404 for non-existent pedido"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.session.get(f"{BASE_URL}/api/pedidos/{fake_id}/timeline")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_timeline_requires_authentication(self):
        """Test that timeline endpoint requires authentication"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        # Create a new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_timeline_event_detalhes_field(self):
        """Test that timeline event has detalhes field (can be empty string)"""
        if not self.pedido_id:
            pytest.skip("No pedidos available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pedidos/{self.pedido_id}/timeline")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data["timeline"]
        
        if len(timeline) == 0:
            pytest.skip("No timeline events to test")
        
        event = timeline[0]
        
        # detalhes field should exist (can be empty string or have content)
        assert "detalhes" in event, "Missing detalhes field"


class TestTimelineWithStatusChange:
    """Tests for timeline after status changes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@senai.br", "senha": "admin123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_status_change_creates_timeline_event(self):
        """Test that changing status creates a new timeline event"""
        # Get a pedido
        pedidos_response = self.session.get(f"{BASE_URL}/api/pedidos?pagina=1&por_pagina=1")
        assert pedidos_response.status_code == 200
        pedidos = pedidos_response.json()["pedidos"]
        
        if not pedidos:
            pytest.skip("No pedidos available for testing")
        
        pedido_id = pedidos[0]["id"]
        current_status = pedidos[0]["status"]
        
        # Get initial timeline count
        timeline_response = self.session.get(f"{BASE_URL}/api/pedidos/{pedido_id}/timeline")
        assert timeline_response.status_code == 200
        initial_count = timeline_response.json()["total_eventos"]
        
        # Change status
        new_status = "em_analise" if current_status == "pendente" else "pendente"
        status_response = self.session.patch(
            f"{BASE_URL}/api/pedidos/{pedido_id}/status",
            json={"status": new_status}
        )
        
        if status_response.status_code != 200:
            pytest.skip(f"Could not change status: {status_response.text}")
        
        # Get updated timeline
        timeline_response = self.session.get(f"{BASE_URL}/api/pedidos/{pedido_id}/timeline")
        assert timeline_response.status_code == 200
        new_count = timeline_response.json()["total_eventos"]
        
        # Should have one more event
        assert new_count == initial_count + 1, \
            f"Expected {initial_count + 1} events, got {new_count}"
        
        # Revert status
        self.session.patch(
            f"{BASE_URL}/api/pedidos/{pedido_id}/status",
            json={"status": current_status}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
