#!/usr/bin/env python3
"""
Backup/Restore Testing Script for PetVaxHK.

Tests the backup and restore functionality to ensure data integrity.
Run with: python -m app.scripts.test_backup_restore
"""

import os
import sys
import tempfile
import shutil
import json
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.io import (
    get_db_path, init_db, backup_db, restore_db,
    export_json, import_json, get_export_stats
)


def create_test_data(db_path: Path) -> dict:
    """Create test data in the database for backup/restore testing."""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current vaccine count to track what we add
    cursor.execute("SELECT COUNT(*) FROM vaccines")
    initial_vaccine_count = cursor.fetchone()[0]
    
    # Insert test vet clinic
    cursor.execute("""
        INSERT INTO vet_clinics (name, address, district, phone, email, opening_hours, is_24hr, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("Test Vet Clinic", "123 Test Street", "Central", "+852-1234-5678", 
          "test@vet.hk", "09:00-18:00", 0, "Test clinic"))
    clinic_id = cursor.lastrowid
    
    # Insert test vaccines (these are new ones)
    cursor.execute("""
        INSERT INTO vaccines (name, species, description, is_mandatory, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ("Test Rabies", "dog", "Test Rabies vaccination", 1, "Test vaccine"))
    rabies_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO vaccines (name, species, description, is_mandatory, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ("Test DHPP", "dog", "Test Distemper vaccine", 1, "Test vaccine"))
    dhpp_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO vaccines (name, species, description, is_mandatory, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ("Test FVRCP", "cat", "Test Feline vaccine", 1, "Test vaccine"))
    fvrcp_id = cursor.lastrowid
    
    # Get final counts
    final_counts = get_db_record_counts(db_path)
    
    # Insert test pet
    cursor.execute("""
        INSERT INTO pets (name, species, breed, date_of_birth, color, microchip_id, gender, neutered, owner_name, owner_phone, owner_email, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("Max", "dog", "Golden Retriever", "2022-03-15", "Golden", "123456789012345", "male", 1, 
          "John Doe", "+852-9876-5432", "john@example.com", "Test dog"))
    pet_id = cursor.lastrowid
    
    # Insert test pet 2
    cursor.execute("""
        INSERT INTO pets (name, species, breed, date_of_birth, color, microchip_id, gender, neutered, owner_name, owner_phone, owner_email, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("Whiskers", "cat", "Persian", "2021-08-20", "White", "987654321098765", "female", 1,
          "Jane Smith", "+852-1111-2222", "jane@example.com", "Test cat"))
    pet2_id = cursor.lastrowid
    
    # Insert vaccination records using the test vaccines
    cursor.execute("""
        INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered, next_due_date, batch_number, vet_name, vet_license, certificate_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, rabies_id, "2025-03-01", "2026-03-01", "RAB2025001", "Dr. Smith", "VET001", "CERT001", "Annual rabies"))
    
    cursor.execute("""
        INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered, next_due_date, batch_number, vet_name, vet_license, certificate_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, dhpp_id, "2025-03-01", "2026-03-01", "DHPP2025001", "Dr. Smith", "VET001", "CERT002", "Annual DHPP"))
    
    cursor.execute("""
        INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered, next_due_date, batch_number, vet_name, vet_license, certificate_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pet2_id, fvrcp_id, "2025-06-15", "2026-06-15", "FVRCP2025001", "Dr. Lee", "VET002", "CERT003", "Annual FVRCP"))
    
    # Insert test reminders
    cursor.execute("""
        INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (pet_id, rabies_id, "due_soon", "2026-03-01", "pending"))
    
    cursor.execute("""
        INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (pet2_id, fvrcp_id, "upcoming", "2026-06-15", "pending"))
    
    conn.commit()
    conn.close()
    
    # Return actual counts from database
    return get_db_record_counts(db_path)


def get_db_record_counts(db_path: Path) -> dict:
    """Get record counts from all tables."""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    counts = {}
    tables = ["pets", "vaccines", "pet_vaccinations", "vet_clinics", "reminders"]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    conn.close()
    return counts


def test_backup_restore():
    """Main test function for backup/restore functionality."""
    print("=" * 60)
    print("PetVaxHK Backup/Restore Testing Script")
    print("=" * 60)
    
    results = {
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Use a test database in temp directory
        test_db = tmpdir / "test_pets.db"
        
        print("\n[1] Initializing test database...")
        try:
            init_db(test_db)
            print(f"    ✓ Database initialized: {test_db}")
            results["tests_passed"] += 1
        except Exception as e:
            print(f"    ✗ Failed to initialize database: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"init_db failed: {e}")
            return results
        
        print("\n[2] Creating test data...")
        try:
            actual_counts = create_test_data(test_db)
            
            print(f"    Created records:")
            for table, count in actual_counts.items():
                print(f"      - {table}: {count}")
            
            # Verify data was created (at least some records exist)
            if actual_counts["pets"] >= 2 and actual_counts["vet_clinics"] >= 1:
                print(f"    ✓ Test data created successfully")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Insufficient test data created!")
                results["tests_failed"] += 1
        except Exception as e:
            print(f"    ✗ Failed to create test data: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"create_test_data failed: {e}")
            return results
        
        # Export original data for comparison
        original_data = export_json(test_db)
        original_stats = get_export_stats(test_db)
        print(f"\n[3] Original database stats: {original_stats}")
        
        print("\n[4] Testing backup_db()...")
        try:
            backup_path = backup_db(test_db, tmpdir)
            print(f"    ✓ Backup created: {backup_path}")
            
            # Verify backup exists
            if backup_path.exists():
                backup_size = backup_path.stat().st_size
                print(f"    ✓ Backup file exists, size: {backup_size} bytes")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Backup file not found!")
                results["tests_failed"] += 1
        except Exception as e:
            print(f"    ✗ Backup failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"backup_db failed: {e}")
            return results
        
        print("\n[5] Adding more data to simulate real-world scenario...")
        try:
            import sqlite3
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Add another pet
            cursor.execute("""
                INSERT INTO pets (name, species, breed, date_of_birth, color, gender, neutered, owner_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("Buddy", "dog", "Labrador", "2023-01-10", "Black", "male", 0, "Bob Wilson"))
            
            conn.commit()
            conn.close()
            
            new_counts = get_db_record_counts(test_db)
            print(f"    New counts: {new_counts}")
            print(f"    ✓ Additional data added")
            results["tests_passed"] += 1
        except Exception as e:
            print(f"    ✗ Failed to add more data: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"Add more data failed: {e}")
        
        print("\n[6] Testing restore_db()...")
        try:
            restore_db(backup_path, test_db)
            print(f"    ✓ Restore completed")
            results["tests_passed"] += 1
        except Exception as e:
            print(f"    ✗ Restore failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"restore_db failed: {e}")
            return results
        
        print("\n[7] Verifying restored data integrity...")
        try:
            restored_counts = get_db_record_counts(test_db)
            print(f"    Restored counts: {restored_counts}")
            
            # Compare with original
            if restored_counts == original_stats:
                print(f"    ✓ Record counts match original!")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Record counts don't match!")
                print(f"      Original: {original_stats}")
                print(f"      Restored: {restored_counts}")
                results["tests_failed"] += 1
                results["details"].append("Restored counts mismatch")
        except Exception as e:
            print(f"    ✗ Verification failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"Verification failed: {e}")
        
        # Verify specific data
        print("\n[8] Verifying specific data values...")
        try:
            import sqlite3
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Check pet names
            cursor.execute("SELECT name FROM pets ORDER BY name")
            pet_names = [row[0] for row in cursor.fetchall()]
            expected_pets = ["Max", "Whiskers"]  # Should be restored, not include Buddy
            
            if pet_names == expected_pets:
                print(f"    ✓ Pet names correct: {pet_names}")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Pet names mismatch!")
                print(f"      Expected: {expected_pets}")
                print(f"      Got: {pet_names}")
                results["tests_failed"] += 1
                results["details"].append("Pet names mismatch")
            
            # Check vaccination records
            cursor.execute("SELECT COUNT(*) FROM pet_vaccinations")
            vax_count = cursor.fetchone()[0]
            
            if vax_count == original_stats["pet_vaccinations"]:
                print(f"    ✓ Vaccination records correct: {vax_count}")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Vaccination records mismatch!")
                results["tests_failed"] += 1
            
            # Check reminders
            cursor.execute("SELECT COUNT(*) FROM reminders")
            rem_count = cursor.fetchone()[0]
            
            if rem_count == original_stats["reminders"]:
                print(f"    ✓ Reminder records correct: {rem_count}")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Reminder records mismatch!")
                results["tests_failed"] += 1
            
            conn.close()
        except Exception as e:
            print(f"    ✗ Data verification failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"Data verification failed: {e}")
        
        # Test JSON export/import cycle
        print("\n[9] Testing JSON export/import cycle...")
        try:
            json_export = tmpdir / "test_export.json"
            export_json(test_db, json_export)
            
            # Verify JSON is valid
            with open(json_export, 'r') as f:
                data = json.load(f)
            
            if "pets" in data and "vaccines" in data:
                print(f"    ✓ JSON export valid, contains {len(data['pets'])} pets")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ JSON export missing required keys")
                results["tests_failed"] += 1
        except Exception as e:
            print(f"    ✗ JSON export/import test failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"JSON test failed: {e}")
        
        # Test backup list functionality
        print("\n[10] Testing backup listing...")
        try:
            # Create another backup
            backup2_path = backup_db(test_db, tmpdir)
            
            # Also manually copy to create a second backup file for testing
            backup3_path = tmpdir / "pets_backup_20260226_manual.db"
            shutil.copy2(backup_path, backup3_path)
            
            # List all backups in directory
            backups = list(tmpdir.glob("pets_backup_*.db"))
            
            if len(backups) >= 2:
                print(f"    ✓ Found {len(backups)} backup files")
                for b in backups:
                    print(f"      - {b.name}")
                results["tests_passed"] += 1
            else:
                print(f"    ✗ Expected at least 2 backups, found {len(backups)}")
                results["tests_failed"] += 1
        except Exception as e:
            print(f"    ✗ Backup listing failed: {e}")
            results["tests_failed"] += 1
            results["details"].append(f"Backup listing failed: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    
    if results["details"]:
        print("\nDetails:")
        for detail in results["details"]:
            print(f"  - {detail}")
    
    if results["tests_failed"] == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {results['tests_failed']} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = test_backup_restore()
    sys.exit(exit_code)
