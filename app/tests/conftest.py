"""
Pytest configuration and shared fixtures for PetVaxHK tests.
"""
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "app" / "core" / "001_initial_schema.sql"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def schema_path() -> Path:
    """Return the path to the schema SQL file."""
    return SCHEMA_PATH


@pytest.fixture
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db(test_db_path: str, schema_path: Path) -> sqlite3.Connection:
    """Create a test database with the schema applied."""
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Apply schema
    with open(schema_path, "r") as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    
    conn.commit()
    
    yield conn
    
    conn.close()


@pytest.fixture
def sample_pet(test_db: sqlite3.Connection) -> dict:
    """Insert a sample pet and return its data."""
    cursor = test_db.cursor()
    cursor.execute("""
        INSERT INTO pets (
            name, species, breed, date_of_birth, color,
            microchip_id, gender, neutered, owner_name, owner_phone
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Max", "dog", "Golden Retriever", "2023-05-15", "Golden",
        "ABC123456789", "male", 1, "John Doe", "+852-1234-5678"
    ))
    test_db.commit()
    return {
        "id": cursor.lastrowid,
        "name": "Max",
        "species": "dog",
        "breed": "Golden Retriever",
        "date_of_birth": "2023-05-15",
        "color": "Golden",
        "microchip_id": "ABC123456789",
        "gender": "male",
        "neutered": 1,
        "owner_name": "John Doe",
        "owner_phone": "+852-1234-5678"
    }


@pytest.fixture
def sample_vaccination(test_db: sqlite3.Connection, sample_pet: dict) -> dict:
    """Insert a sample vaccination record and return its data."""
    cursor = test_db.cursor()
    # First ensure we have the vaccines (from schema seed data)
    cursor.execute("SELECT id FROM vaccines WHERE name = 'Rabies' AND species = 'dog'")
    rabies_vaccine = cursor.fetchone()
    
    cursor.execute("""
        INSERT INTO pet_vaccinations (
            pet_id, vaccine_id, date_administered, next_due_date,
            batch_number, vet_name, certificate_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        sample_pet["id"],
        rabies_vaccine["id"],
        "2024-03-01",
        "2027-03-01",
        "BATCH001",
        "Dr. Smith",
        "CERT001"
    ))
    test_db.commit()
    return {
        "id": cursor.lastrowid,
        "pet_id": sample_pet["id"],
        "vaccine_id": rabies_vaccine["id"],
        "date_administered": "2024-03-01",
        "next_due_date": "2027-03-01",
        "batch_number": "BATCH001",
        "vet_name": "Dr. Smith",
        "certificate_number": "CERT001"
    }


@pytest.fixture
def sample_vet_clinic(test_db: sqlite3.Connection) -> dict:
    """Insert a sample vet clinic and return its data."""
    cursor = test_db.cursor()
    cursor.execute("""
        INSERT INTO vet_clinics (
            name, address, district, phone, is_24hr
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        "Happy Paws Clinic", "123 Queen Street, Central", "Central & Western",
        "+852-2345-6789", 0
    ))
    test_db.commit()
    return {
        "id": cursor.lastrowid,
        "name": "Happy Paws Clinic",
        "address": "123 Queen Street, Central",
        "district": "Central & Western",
        "phone": "+852-2345-6789",
        "is_24hr": 0
    }
