"""
Web app integration tests for PetVaxHK Flask application.
"""
import os
import tempfile

import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Set the environment to use the test database
    os.environ['PETVAX_DB_PATH'] = db_path
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestIndex:
    """Test index/home page."""
    
    def test_index_loads(self, client):
        """Test that index page loads."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_contains_title(self, client):
        """Test that index page contains expected content."""
        response = client.get('/')
        assert b'PetVax' in response.data or b'Pet' in response.data


class TestPets:
    """Test pet management routes."""
    
    def test_pets_list_loads(self, client):
        """Test that pets list page loads."""
        response = client.get('/pets')
        assert response.status_code == 200
    
    def test_pets_add_get(self, client):
        """Test pets add form loads."""
        response = client.get('/pets/add')
        assert response.status_code == 200
    
    def test_pets_add_post_empty(self, client):
        """Test posting empty form shows validation."""
        response = client.post('/pets/add', data={}, follow_redirects=True)
        # Should either redirect or show form again with errors
        assert response.status_code in [200, 400]


class TestVaccines:
    """Test vaccine management routes."""
    
    def test_vaccines_list_loads(self, client):
        """Test that vaccines list page loads."""
        response = client.get('/vaccines')
        assert response.status_code == 200
    
    def test_vaccines_add_get(self, client):
        """Test vaccines add form loads."""
        response = client.get('/vaccines/add')
        assert response.status_code == 200


class TestReminders:
    """Test reminder routes."""
    
    def test_reminders_list_loads(self, client):
        """Test that reminders list page loads."""
        response = client.get('/reminders')
        assert response.status_code == 200


class TestClinics:
    """Test vet clinic routes."""
    
    def test_clinics_list_loads(self, client):
        """Test that clinics list page loads."""
        response = client.get('/clinics')
        assert response.status_code == 200
    
    def test_clinics_add_get(self, client):
        """Test clinics add form loads."""
        response = client.get('/clinics/add')
        assert response.status_code == 200


class TestSettings:
    """Test settings routes."""
    
    def test_settings_loads(self, client):
        """Test that settings page loads."""
        response = client.get('/settings')
        assert response.status_code == 200


class TestAbout:
    """Test about page."""
    
    def test_about_loads(self, client):
        """Test that about page loads."""
        response = client.get('/about')
        assert response.status_code == 200


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns OK."""
        response = client.get('/health')
        assert response.status_code == 200
        assert b'OK' in response.data or b'healthy' in response.data.lower()
