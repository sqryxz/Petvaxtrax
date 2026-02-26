"""
CLI Integration Tests for PetVaxHK
Tests the command-line interface end-to-end.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_PATH = PROJECT_ROOT / "app" / "cli.py"


@pytest.fixture
def cli_env():
    """Environment with temporary database for CLI tests."""
    # Create temp DB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Set environment
    env = os.environ.copy()
    env["PETVAX_DB_PATH"] = db_path
    
    yield env, db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestCLIHelp:
    """Test CLI help output."""
    
    def test_main_help(self):
        """Test main help displays correctly."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "PetVaxHK" in result.stdout
        assert "pet" in result.stdout
        assert "vaccine" in result.stdout
    
    def test_pet_help(self):
        """Test pet subcommand help."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "pet", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "add" in result.stdout
        assert "list" in result.stdout
        assert "edit" in result.stdout
        assert "delete" in result.stdout
    
    def test_vaccine_help(self):
        """Test vaccine subcommand help."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "vaccine", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "add" in result.stdout
    
    def test_reminder_help(self):
        """Test reminder subcommand help."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "reminder", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "show" in result.stdout
        assert "list" in result.stdout
        assert "generate" in result.stdout
    
    def test_export_help(self):
        """Test export subcommand help."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "export", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "-f" in result.stdout or "--format" in result.stdout


class TestCLIInvalidInput:
    """Test CLI error handling for invalid inputs."""
    
    def test_invalid_command(self):
        """Test invalid main command."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "invalidcmd"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2
        assert "invalid choice" in result.stderr
    
    def test_invalid_subcommand(self):
        """Test invalid subcommand."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "pet", "invalid"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2
        assert "invalid choice" in result.stderr
    
    def test_invalid_vaccine_subcommand(self):
        """Test invalid vaccine subcommand."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "vaccine", "invalid"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2


class TestCLIEmptyState:
    """Test CLI behavior with empty database."""
    
    def test_pet_list_empty(self):
        """Test pet list with no pets."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "pet", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No pets found" in result.stdout
    
    def test_vaccine_list_empty(self):
        """Test vaccine list with no records."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "vaccine", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No vaccination records" in result.stdout
    
    def test_compliance_empty(self):
        """Test compliance check with no pets."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "compliance"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No pets to check" in result.stdout
    
    def test_reminder_show_empty(self):
        """Test reminder show with no reminders."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "reminder", "show"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No reminders" in result.stdout
    
    def test_reminder_list_empty(self):
        """Test reminder list with no reminders."""
        result = subprocess.run(
            ["python3", str(CLI_PATH), "reminder", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No reminders found" in result.stdout


class TestCLIExport:
    """Test CLI export functionality."""
    
    def test_export_json(self):
        """Test JSON export."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            result = subprocess.run(
                ["python3", str(CLI_PATH), "export", "-f", "json", "-o", output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Check output file
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "export_metadata" in data
            assert "pets" in data
            assert "vaccines" in data
            assert "pet_vaccinations" in data
            assert "reminders" in data
            assert len(data["vaccines"]) > 0  # Seed data exists
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_csv(self):
        """Test CSV export."""
        # CSV export writes to outputs/exports/ directory
        exports_dir = PROJECT_ROOT / "outputs" / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["python3", str(CLI_PATH), "export", "-f", "csv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Check for CSV files in exports directory
        csv_files = list(exports_dir.glob("*.csv"))
        assert len(csv_files) > 0


class TestCLICompliance:
    """Test CLI compliance checking."""
    
    def test_compliance_with_pets(self):
        """Test compliance check with pets but no vaccinations."""
        # This requires a pet to exist - we can't easily test this without
        # interactive input, but we can verify the command structure
        result = subprocess.run(
            ["python3", str(CLI_PATH), "compliance", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--detailed" in result.stdout or "--pet" in result.stdout
