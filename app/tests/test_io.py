"""Tests for data import/export utilities."""

import csv
import json
import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.core.io import (
    export_json,
    import_json,
    export_csv,
    import_csv,
    backup_db,
    restore_db,
    get_export_stats,
)


@pytest.fixture
def test_db():
    """Create a test database with schema and sample data."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Create schema
    schema_path = Path(__file__).parent.parent / "core" / "001_initial_schema.sql"
    conn = sqlite3.connect(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    
    # Add test data
    cursor = conn.cursor()
    
    # Add a vet clinic
    cursor.execute("""
        INSERT INTO vet_clinics (name, address, district, phone)
        VALUES ('Test Vet Clinic', '123 Test St', 'Central & Western', '12345678')
    """)
    clinic_id = cursor.lastrowid
    
    # Add a pet
    cursor.execute("""
        INSERT INTO pets (name, species, breed, date_of_birth, owner_name, owner_phone)
        VALUES ('Buddy', 'dog', 'Labrador', '2020-01-15', 'John Doe', '98765432')
    """)
    pet_id = cursor.lastrowid
    
    # Add vaccination record
    cursor.execute("""
        INSERT INTO pet_vaccinations 
        (pet_id, vaccine_id, date_administered, next_due_date, vet_clinic_id)
        VALUES (?, 1, '2024-01-15', '2025-01-15', ?)
    """, (pet_id, clinic_id))
    
    # Add a reminder
    cursor.execute("""
        INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
        VALUES (?, 1, 'due_soon', '2025-01-15', 'pending')
    """, (pet_id,))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_json_export():
    """Sample JSON export data."""
    return {
        "export_metadata": {
            "exported_at": "2026-02-26T15:00:00",
            "version": "1.0"
        },
        "pets": [
            {
                "id": 1,
                "name": "Buddy",
                "species": "dog",
                "breed": "Labrador",
                "date_of_birth": "2020-01-15",
                "owner_name": "John Doe",
                "owner_phone": "98765432",
                "neutered": 0
            }
        ],
        "vaccines": [
            {"id": 1, "name": "Rabies", "species": "dog", "is_mandatory": 1}
        ],
        "pet_vaccinations": [
            {
                "id": 1,
                "pet_id": 1,
                "vaccine_id": 1,
                "date_administered": "2024-01-15",
                "next_due_date": "2025-01-15"
            }
        ],
        "vet_clinics": [
            {"id": 1, "name": "Test Vet", "phone": "12345678"}
        ],
        "reminders": [
            {
                "id": 1,
                "pet_id": 1,
                "vaccine_id": 1,
                "due_date": "2025-01-15",
                "status": "pending"
            }
        ]
    }


class TestExportJson:
    """Tests for JSON export functionality."""
    
    def test_export_json_returns_dict(self, test_db):
        """Export should return a dictionary."""
        result = export_json(test_db)
        assert isinstance(result, dict)
    
    def test_export_json_contains_all_tables(self, test_db):
        """Export should contain all tables."""
        result = export_json(test_db)
        assert "pets" in result
        assert "vaccines" in result
        assert "pet_vaccinations" in result
        assert "vet_clinics" in result
        assert "reminders" in result
    
    def test_export_json_pets_count(self, test_db):
        """Export should contain correct pet count."""
        result = export_json(test_db)
        assert len(result["pets"]) == 1
        assert result["pets"][0]["name"] == "Buddy"
    
    def test_export_json_to_file(self, test_db):
        """Export should write to file when path provided."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            export_json(test_db, output_path)
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            assert "pets" in data
        finally:
            output_path.unlink(missing_ok=True)
    
    def test_export_json_metadata(self, test_db):
        """Export should include metadata."""
        result = export_json(test_db)
        assert "export_metadata" in result
        assert "exported_at" in result["export_metadata"]


class TestImportJson:
    """Tests for JSON import functionality."""
    
    def test_import_json_from_dict(self, test_db, sample_json_export):
        """Import should accept dictionary."""
        # Create a fresh db for import test
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            import_db = Path(f.name)
        
        # Create schema
        schema_path = Path(__file__).parent.parent / "core" / "001_initial_schema.sql"
        conn = sqlite3.connect(import_db)
        with open(schema_path) as f:
            conn.executescript(f.read())
        conn.close()
        
        result = import_json(sample_json_export, import_db)
        
        assert result["pets_imported"] >= 0
        import_db.unlink(missing_ok=True)
    
    def test_import_json_merges_existing(self, test_db, sample_json_export):
        """Import with merge=True should not duplicate."""
        result = import_json(sample_json_export, test_db, merge=True)
        
        # Check pet count - should not double
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pets WHERE name = 'Buddy'")
        count = cursor.fetchone()[0]
        conn.close()
        
        # With merge, should update not duplicate
        assert count == 1


class TestExportCsv:
    """Tests for CSV export functionality."""
    
    def test_export_csv_creates_files(self, test_db):
        """Export should create CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = export_csv(test_db, output_dir)
            
            assert "pets" in result
            assert Path(result["pets"]).exists()
    
    def test_export_csv_contains_data(self, test_db):
        """CSV files should contain correct data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            export_csv(test_db, output_dir)
            
            with open(output_dir / "pets.csv") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]["name"] == "Buddy"
    
    def test_export_csv_summary(self, test_db):
        """Export should create summary CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = export_csv(test_db, output_dir)
            
            assert "summary" in result
            assert Path(result["summary"]).exists()


class TestImportCsv:
    """Tests for CSV import functionality."""
    
    def test_import_csv_pets(self, test_db):
        """Import should add pets from CSV."""
        # Create a fresh db
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            import_db = Path(f.name)
        
        schema_path = Path(__file__).parent.parent / "core" / "001_initial_schema.sql"
        conn = sqlite3.connect(import_db)
        with open(schema_path) as f:
            conn.executescript(f.read())
        conn.close()
        
        # Create CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=['name', 'species', 'breed', 'owner_name'])
            writer.writeheader()
            writer.writerow({
                'name': 'Max',
                'species': 'dog',
                'breed': 'Poodle',
                'owner_name': 'Jane Doe'
            })
        
        try:
            result = import_csv(csv_path, 'pets', import_db)
            assert result["imported"] == 1
            
            # Verify
            conn = sqlite3.connect(import_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM pets WHERE name = 'Max'")
            assert cursor.fetchone()[0] == 'Max'
            conn.close()
        finally:
            csv_path.unlink(missing_ok=True)
            import_db.unlink(missing_ok=True)


class TestBackupRestore:
    """Tests for backup and restore functionality."""
    
    def test_backup_creates_file(self, test_db):
        """Backup should create a backup file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            backup_path = backup_db(test_db, backup_dir)
            
            assert backup_path.exists()
            assert backup_path.suffix == '.db'
    
    def test_backup_contains_data(self, test_db):
        """Backup should contain same data as original."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            backup_path = backup_db(test_db, backup_dir)
            
            # Check backup has data
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pets")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 1
    
    def test_restore_from_backup(self, test_db):
        """Restore should recover data from backup."""
        # Backup first
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            backup_path = backup_db(test_db, backup_dir)
            
            # Create new db
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                new_db = Path(f.name)
            
            schema_path = Path(__file__).parent.parent / "core" / "001_initial_schema.sql"
            conn = sqlite3.connect(new_db)
            with open(schema_path) as f:
                conn.executescript(f.read())
            conn.close()
            
            # Restore
            restore_db(backup_path, new_db)
            
            # Verify
            conn = sqlite3.connect(new_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM pets")
            name = cursor.fetchone()[0]
            conn.close()
            
            assert name == "Buddy"
            
            new_db.unlink(missing_ok=True)


class TestGetExportStats:
    """Tests for export statistics."""
    
    def test_get_stats_returns_dict(self, test_db):
        """Stats should return a dictionary."""
        stats = get_export_stats(test_db)
        assert isinstance(stats, dict)
    
    def test_get_stats_correct_counts(self, test_db):
        """Stats should have correct counts."""
        stats = get_export_stats(test_db)
        
        assert stats["pets"] == 1
        assert stats["vaccines"] >= 5  # Default vaccines
        assert stats["pet_vaccinations"] == 1
        assert stats["vet_clinics"] == 1
        assert stats["reminders"] == 1
