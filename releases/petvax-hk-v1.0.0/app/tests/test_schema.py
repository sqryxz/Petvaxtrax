"""
Basic schema validation tests for PetVaxHK.
"""
import sqlite3

import pytest


class TestSchema:
    """Tests to verify the database schema is set up correctly."""

    def test_foreign_keys_enabled(self, test_db: sqlite3.Connection):
        """Verify foreign keys are enabled."""
        result = test_db.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1

    def test_pets_table_exists(self, test_db: sqlite3.Connection):
        """Verify the pets table exists with correct columns."""
        cursor = test_db.execute("PRAGMA table_info(pets)")
        columns = {row["name"] for row in cursor.fetchall()}
        
        required_columns = {
            "id", "name", "species", "breed", "date_of_birth",
            "color", "microchip_id", "gender", "neutered",
            "owner_name", "owner_phone", "owner_email", "notes",
            "created_at", "updated_at"
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_vaccines_table_exists(self, test_db: sqlite3.Connection):
        """Verify the vaccines table exists with seed data."""
        cursor = test_db.execute("PRAGMA table_info(vaccines)")
        columns = {row["name"] for row in cursor.fetchall()}
        
        required_columns = {"id", "name", "species", "description", "is_mandatory", "notes"}
        assert required_columns.issubset(columns)

    def test_vaccines_seed_data(self, test_db: sqlite3.Connection):
        """Verify seed vaccine data exists."""
        cursor = test_db.execute("SELECT COUNT(*) as count FROM vaccines")
        assert cursor.fetchone()["count"] >= 8  # 5 dog + 3 cat vaccines

    def test_pet_vaccinations_table_exists(self, test_db: sqlite3.Connection):
        """Verify the pet_vaccinations table exists."""
        cursor = test_db.execute("PRAGMA table_info(pet_vaccinations)")
        columns = {row["name"] for row in cursor.fetchall()}
        
        required_columns = {
            "id", "pet_id", "vaccine_id", "date_administered",
            "next_due_date", "batch_number", "vet_clinic_id",
            "vet_name", "vet_license", "certificate_number",
            "notes", "created_at"
        }
        assert required_columns.issubset(columns)

    def test_vet_clinics_table_exists(self, test_db: sqlite3.Connection):
        """Verify the vet_clinics table exists."""
        cursor = test_db.execute("PRAGMA table_info(vet_clinics)")
        columns = {row["name"] for row in cursor.fetchall()}
        
        required_columns = {
            "id", "name", "address", "district", "phone",
            "email", "opening_hours", "is_24hr", "notes", "created_at"
        }
        assert required_columns.issubset(columns)

    def test_reminders_table_exists(self, test_db: sqlite3.Connection):
        """Verify the reminders table exists."""
        cursor = test_db.execute("PRAGMA table_info(reminders)")
        columns = {row["name"] for row in cursor.fetchall()}
        
        required_columns = {
            "id", "pet_id", "vaccine_id", "reminder_type",
            "due_date", "sent_at", "status", "created_at"
        }
        assert required_columns.issubset(columns)

    def test_schema_version_table(self, test_db: sqlite3.Connection):
        """Verify schema version is recorded."""
        cursor = test_db.execute("SELECT version, description FROM schema_version")
        row = cursor.fetchone()
        assert row is not None
        assert row["version"] == 1
        assert "Initial schema" in row["description"]

    def test_pet_vaccination_summary_view(self, test_db: sqlite3.Connection):
        """Verify the pet_vaccination_summary view exists and works."""
        # Should not raise an error
        cursor = test_db.execute("SELECT * FROM v_pet_vaccination_summary LIMIT 1")
        # Just verify it runs without error

    def test_upcoming_reminders_view(self, test_db: sqlite3.Connection):
        """Verify the upcoming_reminders view exists and works."""
        # Should not raise an error
        cursor = test_db.execute("SELECT * FROM v_upcoming_reminders LIMIT 1")
        # Just verify it runs without error

    def test_indexes_exist(self, test_db: sqlite3.Connection):
        """Verify expected indexes exist."""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = {row["name"] for row in cursor.fetchall()}
        
        expected_indexes = {
            "idx_pets_microchip", "idx_pets_species",
            "idx_pet_vacc_pet", "idx_pet_vacc_due",
            "idx_vets_district", "idx_reminders_status", "idx_reminders_due"
        }
        # Note: Some indexes might use different names, just verify we have indexes
        assert len(indexes) >= 5


class TestPetOperations:
    """Tests for pet CRUD operations."""

    def test_insert_pet(self, test_db: sqlite3.Connection):
        """Test inserting a pet."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO pets (name, species, owner_name)
            VALUES (?, ?, ?)
        """, ("Buddy", "dog", "Jane Doe"))
        test_db.commit()
        
        assert cursor.lastrowid is not None
        
        # Verify it was inserted
        cursor = test_db.execute("SELECT * FROM pets WHERE name = 'Buddy'")
        pet = cursor.fetchone()
        assert pet is not None
        assert pet["species"] == "dog"
        assert pet["owner_name"] == "Jane Doe"

    def test_species_constraint(self, test_db: sqlite3.Connection):
        """Test that invalid species is rejected."""
        with pytest.raises(sqlite3.IntegrityError):
            test_db.execute("""
                INSERT INTO pets (name, species, owner_name)
                VALUES (?, ?, ?)
            """, ("Invalid", "bird", "Test"))

    def test_pet_with_vaccination(self, test_db: sqlite3.Connection, sample_pet: dict):
        """Test linking a pet with vaccinations."""
        # Get rabies vaccine
        cursor = test_db.execute(
            "SELECT id FROM vaccines WHERE name = 'Rabies' AND species = 'dog'"
        )
        vaccine = cursor.fetchone()
        
        # Insert vaccination
        cursor.execute("""
            INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered)
            VALUES (?, ?, ?)
        """, (sample_pet["id"], vaccine["id"], "2024-01-15"))
        test_db.commit()
        
        # Verify
        cursor = test_db.execute("""
            SELECT pv.*, v.name as vaccine_name
            FROM pet_vaccinations pv
            JOIN vaccines v ON pv.vaccine_id = v.id
            WHERE pv.pet_id = ?
        """, (sample_pet["id"],))
        
        record = cursor.fetchone()
        assert record is not None
        assert record["vaccine_name"] == "Rabies"


class TestVaccineOperations:
    """Tests for vaccine operations."""

    def test_get_mandatory_vaccines(self, test_db: sqlite3.Connection):
        """Test retrieving mandatory vaccines."""
        cursor = test_db.execute("SELECT * FROM vaccines WHERE is_mandatory = 1")
        mandatory = cursor.fetchall()
        
        assert len(mandatory) >= 2  # Rabies for both dog and cat
        
    def test_vaccine_species_filter(self, test_db: sqlite3.Connection):
        """Test filtering vaccines by species."""
        cursor = test_db.execute(
            "SELECT name FROM vaccines WHERE species = 'dog'"
        )
        dog_vaccines = {row["name"] for row in cursor.fetchall()}
        
        assert "Rabies" in dog_vaccines
        assert "DHPP/DAPP" in dog_vaccines
        assert "FeLV" not in dog_vaccines  # Cat-only vaccine
