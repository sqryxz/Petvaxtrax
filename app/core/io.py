"""
Data import/export utilities for PetVaxHK.

Supports:
- JSON import/export (full data with relationships)
- CSV import/export (flattened for spreadsheets)
- Database backup/restore
"""

import csv
import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def get_db_path() -> Path: 
    """Get the default database path."""
    return Path(__file__).parent.parent.parent / "outputs" / "pets.db"


def _row_to_dict(cursor: sqlite3.Cursor, row: tuple) -> Dict: 
    """Convert a database row to a dictionary using cursor description."""
    return {desc[0]: value for desc, value in zip(cursor.description, row)}


def export_json(db_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict: 
    """
    Export all data to JSON format.
    
    Args:
        db_path: Path to SQLite database. Defaults to default location.
        output_path: Optional path to write JSON file.
    
    Returns:
        Dictionary containing all exported data.
    """
    db_path = db_path or get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = _row_to_dict
    cursor = conn.cursor()
    
    data = {
        "export_metadata": {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "source": str(db_path)
        },
        "pets": [],
        "vaccines": [],
        "pet_vaccinations": [],
        "vet_clinics": [],
        "reminders": []
    }
    
    # Export pets
    cursor.execute("SELECT * FROM pets ORDER BY id")
    data["pets"] = cursor.fetchall()
    
    # Export vaccines
    cursor.execute("SELECT * FROM vaccines ORDER BY id")
    data["vaccines"] = cursor.fetchall()
    
    # Export pet vaccinations
    cursor.execute("SELECT * FROM pet_vaccinations ORDER BY id")
    data["pet_vaccinations"] = cursor.fetchall()
    
    # Export vet clinics
    cursor.execute("SELECT * FROM vet_clinics ORDER BY id")
    data["vet_clinics"] = cursor.fetchall()
    
    # Export reminders
    cursor.execute("SELECT * FROM reminders ORDER BY id")
    data["reminders"] = cursor.fetchall()
    
    conn.close()
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data


def import_json(data: Union[dict, str, Path], db_path: Optional[Path] = None, 
                merge: bool = True) -> Dict: 
    """
    Import data from JSON format.
    
    Args:
        data: JSON string, Path to JSON file, or dictionary.
        db_path: Path to SQLite database. Defaults to default location.
        merge: If True, merge with existing data. If False, replace.
    
    Returns:
        Dictionary with import results (counts, warnings, errors).
    """
    # Load data if path or string
    if isinstance(data, (str, Path)):
        with open(data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    db_path = db_path or get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {
        "pets_imported": 0,
        "vaccines_imported": 0,
        "pet_vaccinations_imported": 0,
        "vet_clinics_imported": 0,
        "reminders_imported": 0,
        "warnings": [],
        "errors": []
    }
    
    # Import vet clinics first (foreign key dependency)
    if "vet_clinics" in data:
        for clinic in data["vet_clinics"]:
            try:
                # Check if exists by name
                cursor.execute("SELECT id FROM vet_clinics WHERE name = ?", (clinic.get("name"),))
                existing = cursor.fetchone()
                
                if existing and merge:
                    # Update existing
                    cursor.execute("""
                        UPDATE vet_clinics 
                        SET address = ?, district = ?, phone = ?, email = ?,
                            opening_hours = ?, is_24hr = ?, notes = ?
                        WHERE name = ?
                    """, (
                        clinic.get("address"), clinic.get("district"),
                        clinic.get("phone"), clinic.get("email"),
                        clinic.get("opening_hours"), clinic.get("is_24hr", 0),
                        clinic.get("notes"), clinic.get("name")
                    ))
                elif not existing:
                    cursor.execute("""
                        INSERT INTO vet_clinics (name, address, district, phone, email, opening_hours, is_24hr, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        clinic.get("name"), clinic.get("address"), clinic.get("district"),
                        clinic.get("phone"), clinic.get("email"), clinic.get("opening_hours"),
                        clinic.get("is_24hr", 0), clinic.get("notes")
                    ))
                    results["vet_clinics_imported"] += 1
            except Exception as e:
                results["errors"].append(f"vet_clinic import error: {e}")
    
    # Import vaccines
    if "vaccines" in data:
        for vaccine in data["vaccines"]:
            try:
                cursor.execute("SELECT id FROM vaccines WHERE name = ? AND species = ?", 
                             (vaccine.get("name"), vaccine.get("species")))
                existing = cursor.fetchone()
                
                if not existing:
                    cursor.execute("""
                        INSERT INTO vaccines (name, species, description, is_mandatory, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        vaccine.get("name"), vaccine.get("species"),
                        vaccine.get("description"), vaccine.get("is_mandatory", 0),
                        vaccine.get("notes")
                    ))
                    results["vaccines_imported"] += 1
            except Exception as e:
                results["errors"].append(f"vaccine import error: {e}")
    
    # Import pets
    if "pets" in data:
        for pet in data["pets"]:
            try:
                cursor.execute("SELECT id FROM pets WHERE name = ? AND owner_name = ?", 
                             (pet.get("name"), pet.get("owner_name")))
                existing = cursor.fetchone()
                
                pet_id = None
                if existing:
                    if merge:
                        # Update existing
                        pet_id = existing[0]
                        cursor.execute("""
                            UPDATE pets 
                            SET species = ?, breed = ?, date_of_birth = ?, color = ?,
                                microchip_id = ?, gender = ?, neutered = ?, 
                                owner_phone = ?, owner_email = ?, notes = ?
                            WHERE id = ?
                        """, (
                            pet.get("species"), pet.get("breed"), pet.get("date_of_birth"),
                            pet.get("color"), pet.get("microchip_id"), pet.get("gender"),
                            pet.get("neutered", 0), pet.get("owner_phone"), pet.get("owner_email"),
                            pet.get("notes"), pet_id
                        ))
                else:
                    cursor.execute("""
                        INSERT INTO pets (name, species, breed, date_of_birth, color, 
                                         microchip_id, gender, neutered, owner_name, 
                                         owner_phone, owner_email, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pet.get("name"), pet.get("species"), pet.get("breed"),
                        pet.get("date_of_birth"), pet.get("color"), pet.get("microchip_id"),
                        pet.get("gender"), pet.get("neutered", 0), pet.get("owner_name"),
                        pet.get("owner_phone"), pet.get("owner_email"), pet.get("notes")
                    ))
                    pet_id = cursor.lastrowid
                    results["pets_imported"] += 1
                
                # Import pet vaccinations if we have a pet_id
                if pet_id and "pet_vaccinations" in data:
                    for pv in data["pet_vaccinations"]:
                        # Match by pet name (approximate)
                        if pv.get("pet_name") == pet.get("name") or pv.get("pet_id") == pet.get("id"):
                            # Get vaccine_id
                            cursor.execute("SELECT id FROM vaccines WHERE name = ?", (pv.get("vaccine_name"),))
                            vaccine_row = cursor.fetchone()
                            if vaccine_row:
                                # Check if vaccination record exists
                                cursor.execute("""
                                    SELECT id FROM pet_vaccinations 
                                    WHERE pet_id = ? AND vaccine_id = ? AND date_administered = ?
                                """, (pet_id, vaccine_row[0], pv.get("date_administered")))
                                if not cursor.fetchone():
                                    cursor.execute("""
                                        INSERT INTO pet_vaccinations 
                                        (pet_id, vaccine_id, date_administered, next_due_date, 
                                         batch_number, vet_name, vet_license, certificate_number, notes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        pet_id, vaccine_row[0], pv.get("date_administered"),
                                        pv.get("next_due_date"), pv.get("batch_number"),
                                        pv.get("vet_name"), pv.get("vet_license"),
                                        pv.get("certificate_number"), pv.get("notes")
                                    ))
                                    results["pet_vaccinations_imported"] += 1
                                    
            except Exception as e:
                results["errors"].append(f"pet import error: {e}")
    
    # Import reminders
    if "reminders" in data:
        for reminder in data["reminders"]:
            try:
                # Find pet_id by name
                cursor.execute("SELECT id FROM pets WHERE name = ?", (reminder.get("pet_name"),))
                pet_row = cursor.fetchone()
                
                cursor.execute("SELECT id FROM vaccines WHERE name = ?", (reminder.get("vaccine_name"),))
                vaccine_row = cursor.fetchone()
                
                if pet_row and vaccine_row:
                    # Check if reminder exists
                    cursor.execute("""
                        SELECT id FROM reminders 
                        WHERE pet_id = ? AND vaccine_id = ? AND due_date = ?
                    """, (pet_row[0], vaccine_row[0], reminder.get("due_date")))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            pet_row[0], vaccine_row[0], reminder.get("reminder_type"),
                            reminder.get("due_date"), reminder.get("status", "pending")
                        ))
                        results["reminders_imported"] += 1
            except Exception as e:
                results["errors"].append(f"reminder import error: {e}")
    
    conn.commit()
    conn.close()
    
    return results


def export_csv(db_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> Dict: 
    """
    Export data to CSV files (one per table).
    
    Args:
        db_path: Path to SQLite database. Defaults to default location.
        output_dir: Directory to write CSV files. Defaults to outputs/exports/.
    
    Returns:
        Dictionary mapping table names to output file paths.
    """
    db_path = db_path or get_db_path()
    output_dir = output_dir or Path(__file__).parent.parent.parent / "outputs" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = _row_to_dict
    cursor = conn.cursor()
    
    output_files = {}
    
    tables = ["pets", "vaccines", "pet_vaccinations", "vet_clinics", "reminders"]
    
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if rows:
            output_file = output_dir / f"{table}.csv"
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            
            output_files[table] = str(output_file)
    
    # Also export a combined summary CSV
    cursor.execute("""
        SELECT 
            p.name as pet_name, p.species, p.breed, p.owner_name,
            v.name as vaccine_name, v.is_mandatory,
            pv.date_administered, pv.next_due_date,
            CASE 
                WHEN pv.next_due_date IS NULL THEN 'unknown'
                WHEN pv.next_due_date < date('now') THEN 'overdue'
                WHEN pv.next_due_date <= date('now', '+30 days') THEN 'due_soon'
                ELSE 'up_to_date'
            END as vaccination_status
        FROM pets p
        LEFT JOIN pet_vaccinations pv ON p.id = pv.pet_id
        LEFT JOIN vaccines v ON pv.vaccine_id = v.id
        ORDER BY p.name, v.name
    """)
    
    rows = cursor.fetchall()
    if rows:
        output_file = output_dir / "pet_vaccination_summary.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        output_files["summary"] = str(output_file)
    
    conn.close()
    
    return output_files


def import_csv(csv_path: Union[Path, str], table: str, db_path: Optional[Path] = None) -> Dict: 
    """
    Import data from a CSV file into a specific table.
    
    Args:
        csv_path: Path to CSV file.
        table: Target table name (pets, vaccines, pet_vaccinations, vet_clinics, reminders).
        db_path: Path to SQLite database. Defaults to default location.
    
    Returns:
        Dictionary with import results.
    """
    db_path = db_path or get_db_path()
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    valid_tables = ["pets", "vaccines", "pet_vaccinations", "vet_clinics", "reminders"]
    if table not in valid_tables:
        raise ValueError(f"Invalid table. Must be one of: {valid_tables}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {"imported": 0, "errors": []}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    for row in rows:
        try:
            # Filter out None/empty values
            cleaned_row = {k: v for k, v in row.items() if v}
            
            # Convert numeric fields
            if "is_mandatory" in cleaned_row:
                cleaned_row["is_mandatory"] = int(cleaned_row["is_mandatory"])
            if "neutered" in cleaned_row:
                cleaned_row["neutered"] = int(cleaned_row["neutered"])
            if "is_24hr" in cleaned_row:
                cleaned_row["is_24hr"] = int(cleaned_row["is_24hr"])
            
            columns = ", ".join(cleaned_row.keys())
            placeholders = ", ".join(["?"] * len(cleaned_row))
            
            cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", 
                         list(cleaned_row.values()))
            results["imported"] += 1
            
        except Exception as e:
            results["errors"].append(f"Row error: {e}")
    
    conn.commit()
    conn.close()
    
    return results


def backup_db(db_path: Optional[Path] = None, backup_dir: Optional[Path] = None) -> Path: 
    """
    Create a timestamped backup of the database.
    
    Args:
        db_path: Path to SQLite database. Defaults to default location.
        backup_dir: Directory for backups. Defaults to outputs/backups/.
    
    Returns:
        Path to the backup file.
    """
    db_path = db_path or get_db_path()
    backup_dir = backup_dir or Path(__file__).parent.parent.parent / "outputs" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"pets_backup_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def restore_db(backup_path: Union[Path, str], db_path: Optional[Path] = None) -> None:
    """
    Restore database from a backup file.
    
    Args:
        backup_path: Path to backup file.
        db_path: Target database path. Defaults to default location.
    """
    db_path = db_path or get_db_path()
    backup_path = Path(backup_path)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Create a backup of current db first
    if db_path.exists():
        current_backup = db_path.with_suffix('.db.pre_restore')
        shutil.copy2(db_path, current_backup)
    
    shutil.copy2(backup_path, db_path)


def get_export_stats(db_path: Optional[Path] = None) -> Dict: 
    """
    Get statistics about the database for export.
    
    Args:
        db_path: Path to SQLite database. Defaults to default location.
    
    Returns:
        Dictionary with counts per table.
    """
    db_path = db_path or get_db_path()
    
    if not db_path.exists():
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    tables = ["pets", "vaccines", "pet_vaccinations", "vet_clinics", "reminders"]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize the database with schema from 001_initial_schema.sql.
    
    Args:
        db_path: Optional path to database. Defaults to default location.
    """
    db_path = db_path or get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Skip if database already exists and has tables
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vaccines'")
        if cursor.fetchone():
            conn.close()
            return  # Already initialized
        conn.close()
    
    schema_path = Path(__file__).parent / "001_initial_schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    cursor.executescript(schema)
    conn.commit()
    conn.close()


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a database connection.
    
    Args:
        db_path: Optional path to database. Defaults to default location.
    
    Returns:
        SQLite connection object.
    """
    db_path = db_path or get_db_path()
    
    # Ensure db exists
    if not db_path.exists():
        init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
