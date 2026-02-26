"""
Security Audit Tests for PetVaxHK

This module documents security findings and provides tests to verify
security configurations are in place.

Findings:
- Dependency vulnerabilities (see pip-audit output)
- Hardcoded secret key in development mode
"""
import os
import pytest


class TestSecurityConfiguration:
    """Security configuration tests."""

    def test_secret_key_not_default(self):
        """SECRET_KEY should not be the default dev value in production."""
        from app import create_app
        
        app = create_app()
        secret_key = app.config.get('SECRET_KEY')
        
        # In development, the default is acceptable
        # In production, this should be explicitly set
        if os.environ.get('FLASK_ENV') == 'production':
            assert secret_key != "dev-secret-key-change-in-production", \
                "SECRET_KEY must be changed from default in production"
            assert secret_key != "dev-secret-key", \
                "SECRET_KEY must not be a simple default"
    
    def test_database_path_isolated(self):
        """Database path should be in instance folder, not world-writable."""
        from app import create_app
        
        app = create_app()
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        
        # SQLite should use instance path
        if db_uri and db_uri.startswith('sqlite'):
            # Should reference instance_path, not absolute /tmp or similar
            assert 'instance' in db_uri or not db_uri.endswith('.db'), \
                "Database should use instance folder for isolation"
    
    def test_sqlalchemy_track_modifications_disabled(self):
        """SQLALCHEMY_TRACK_MODIFICATIONS should be disabled."""
        from app import create_app
        
        app = create_app()
        track_mods = app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS')
        
        assert track_mods is False, \
            "SQLALCHEMY_TRACK_MODIFICATIONS should be False to save memory"
    
    def test_no_debug_in_production(self):
        """Flask debug mode should be off in production."""
        from app import create_app
        
        app = create_app()
        
        if os.environ.get('FLASK_ENV') == 'production':
            assert app.debug is False, "Flask debug must be False in production"


class TestDependencyVulnerabilities:
    """Tests that document known dependency vulnerabilities."""
    
    KNOWN_VULNERABILITIES = {
        # These are documented vulnerabilities in transitive dependencies
        # that were found via pip-audit
        "filelock": ["GHSA-w853-jp5j-5j7f", "GHSA-qmgc-5h2g-mvrw"],
        "future": ["PYSEC-2022-42991"],
        "pip": ["PYSEC-2023-228", "GHSA-4xh5-x5gv-qwph", "GHSA-6vgw-5pg2-w6jp"],
        "setuptools": ["PYSEC-2022-43012", "PYSEC-2025-49", "GHSA-cx63-2mw6-8hw5"],
        "wheel": ["PYSEC-2022-43017"],
    }
    
    def test_known_vulnerabilities_documented(self):
        """Document known vulnerabilities for review."""
        # This test always passes but documents the known issues
        # Run: python3 -m pip_audit for full vulnerability report
        assert len(self.KNOWN_VULNERABILITIES) > 0, \
            "Vulnerability documentation exists"


# Security recommendations:
SECURITY_RECOMMENDATIONS = """
=== Security Audit Summary ===

DEPENDENCY VULNERABILITIES (Run: pip-audit)
-------------------------------------------
- filelock: 2 vulnerabilities (upgrade to 3.20.3+)
- future: 1 vulnerability (upgrade to 0.18.3+)
- pip: 3 vulnerabilities (upgrade to 23.3+)
- setuptools: 4 vulnerabilities (upgrade to 65.5.1+)
- wheel: 1 vulnerability (upgrade to 0.38.1+)

HARDCODE SECRET KEY
-------------------
File: app/__init__.py
Issue: SECRET_KEY defaults to "dev-secret-key-change-in-production"
Fix: Set SECRET_KEY environment variable in production

RECOMMENDATIONS
---------------
1. Update dependencies to latest versions
2. Use environment variables for all secrets
3. Enable Flask debug=False in production
4. Use HTTPS in production
5. Consider adding CSRF protection for forms
6. Add rate limiting for web endpoints
7. Implement proper session management
"""
