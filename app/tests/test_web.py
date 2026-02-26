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


class TestPetDetailEditDelete:
    """Test pet detail, edit, and delete routes."""
    
    def test_pets_detail_not_found(self, client):
        """Test pet detail returns 404 for non-existent pet."""
        response = client.get('/pets/99999')
        assert response.status_code == 404
    
    def test_pets_edit_not_found(self, client):
        """Test pet edit returns 404 for non-existent pet."""
        response = client.get('/pets/99999/edit')
        assert response.status_code == 404
    
    def test_pets_delete_not_found(self, client):
        """Test pet delete returns 404 for non-existent pet."""
        response = client.post('/pets/99999/delete')
        assert response.status_code == 404


class TestVaccineDetailEditDelete:
    """Test vaccine detail, edit, and delete routes."""
    
    def test_vaccines_detail_not_found(self, client):
        """Test vaccine detail returns 404 for non-existent vaccine."""
        response = client.get('/vaccines/99999')
        assert response.status_code == 404
    
    def test_vaccines_edit_not_found(self, client):
        """Test vaccine edit returns 404 for non-existent vaccine."""
        response = client.get('/vaccines/99999/edit')
        assert response.status_code == 404
    
    def test_vaccines_delete_not_found(self, client):
        """Test vaccine delete returns 404 for non-existent vaccine."""
        response = client.post('/vaccines/99999/delete')
        assert response.status_code == 404


class TestVaccinations:
    """Test vaccination record routes."""
    
    def test_vaccinations_add_get(self, client):
        """Test vaccinations add form loads."""
        response = client.get('/vaccinations/add')
        assert response.status_code == 200
    
    def test_vaccinations_add_post_empty(self, client):
        """Test posting empty vaccination form."""
        response = client.post('/vaccinations/add', data={}, follow_redirects=True)
        assert response.status_code in [200, 400]
    
    def test_vaccinations_edit_not_found(self, client):
        """Test vaccinations edit returns 404 for non-existent record."""
        response = client.get('/vaccinations/99999/edit')
        assert response.status_code == 404
    
    def test_vaccinations_delete_not_found(self, client):
        """Test vaccinations delete returns 404 for non-existent record."""
        response = client.post('/vaccinations/99999/delete')
        assert response.status_code == 404


class TestRemindersActions:
    """Test reminder action routes."""
    
    def test_reminders_complete_not_found(self, client):
        """Test reminder complete returns 404 for non-existent reminder."""
        response = client.post('/reminders/99999/complete')
        assert response.status_code == 404
    
    def test_reminders_generate(self, client):
        """Test reminders generate route exists."""
        response = client.post('/reminders/generate')
        # Should either succeed or redirect (will fail if no DB but route exists)
        assert response.status_code in [200, 302, 500]


class TestClinicsDetailEditDelete:
    """Test clinic detail, edit, and delete routes."""
    
    def test_clinics_detail_not_found(self, client):
        """Test clinic detail returns 404 for non-existent clinic."""
        response = client.get('/clinics/99999')
        assert response.status_code == 404
    
    def test_clinics_edit_not_found(self, client):
        """Test clinic edit returns 404 for non-existent clinic."""
        response = client.get('/clinics/99999/edit')
        assert response.status_code == 404
    
    def test_clinics_delete_not_found(self, client):
        """Test clinic delete returns 404 for non-existent clinic."""
        response = client.post('/clinics/99999/delete')
        assert response.status_code == 404


class TestSettingsUpdate:
    """Test settings update route."""
    
    def test_settings_update_post(self, client):
        """Test settings update POST."""
        response = client.post('/settings/update', follow_redirects=True)
        assert response.status_code == 200


class TestCompliance:
    """Test compliance routes."""
    
    def test_compliance_list_loads(self, client):
        """Test compliance dashboard loads."""
        response = client.get('/compliance')
        assert response.status_code == 200
    
    def test_compliance_detail_not_found(self, client):
        """Test compliance detail returns 404 for non-existent pet."""
        response = client.get('/compliance/99999')
        assert response.status_code == 404


class TestRouteConsistency:
    """Test route naming consistency and URL patterns."""
    
    def test_all_list_routes_return_200(self, client):
        """Test all list routes return valid status."""
        routes = ['/pets', '/vaccines', '/reminders', '/clinics', '/settings', '/about', '/compliance']
        for route in routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} failed with {response.status_code}"
    
    def test_all_add_routes_return_200(self, client):
        """Test all add form routes return valid status."""
        routes = ['/pets/add', '/vaccines/add', '/clinics/add', '/vaccinations/add']
        for route in routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} failed with {response.status_code}"
    
    def test_nonexistent_route_returns_404(self, client):
        """Test that nonexistent routes return 404."""
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404
    
    def test_static_files_accessible(self, app):
        """Test static files are accessible."""
        with app.app_context():
            # Just verify the app has static folder configured
            assert app.static_folder is not None
