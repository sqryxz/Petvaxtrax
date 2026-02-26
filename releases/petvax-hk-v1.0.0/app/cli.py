#!/usr/bin/env python3
"""
PetVaxHK CLI - Command-line interface for PetVaxHK
Local-first pet vaccine tracker for Hong Kong (dogs + cats)

Usage:
    petvax <command> [options]

Commands:
    pet         Manage pets (add, list, edit, delete)
    vaccine     Manage vaccinations (add, list, edit, delete)
    reminder    Show upcoming reminders
    compliance  Check HK vaccination compliance
    export      Export data (JSON, CSV)
"""
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))


def cmd_pet(args):
    """Pet management commands"""
    from app.core.io import get_db_connection, init_db
    
    if args.subcommand == 'add':
        # Interactive pet creation
        print("Add a new pet to the registry:")
        print("-" * 40)
        
        name = input("Pet name: ").strip()
        if not name:
            print("Error: Pet name is required.")
            return
        
        species = input("Species (dog/cat): ").strip().lower()
        if species not in ('dog', 'cat'):
            print("Error: Species must be 'dog' or 'cat'.")
            return
        
        breed = input("Breed (optional): ").strip() or None
        dob = input("Date of birth (YYYY-MM-DD, optional): ").strip() or None
        color = input("Color (optional): ").strip() or None
        microchip = input("Microchip ID (optional): ").strip() or None
        gender = input("Gender (male/female/unknown, optional): ").strip().lower() or None
        if gender and gender not in ('male', 'female', 'unknown'):
            print("Warning: Invalid gender, setting to unknown.")
            gender = 'unknown'
        
        neutered_input = input("Neutered (y/n): ").strip().lower()
        neutered = 1 if neutered_input == 'y' else 0
        
        owner_name = input("Owner name: ").strip()
        if not owner_name:
            print("Error: Owner name is required.")
            return
        
        owner_phone = input("Owner phone (optional): ").strip() or None
        owner_email = input("Owner email (optional): ").strip() or None
        notes = input("Notes (optional): ").strip() or None
        
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO pets (name, species, breed, date_of_birth, color, microchip_id, 
                                gender, neutered, owner_name, owner_phone, owner_email, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, species, breed, dob, color, microchip, gender, neutered, 
                  owner_name, owner_phone, owner_email, notes))
            conn.commit()
            pet_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"\n✓ Pet '{name}' added successfully! (ID: {pet_id})")
        except Exception as e:
            print(f"Error adding pet: {e}")
        finally:
            conn.close()
            
    elif args.subcommand == 'list':
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT id, name, species, breed, date_of_birth, color, gender, neutered, owner_name
            FROM pets ORDER BY name
        """)
        pets = cursor.fetchall()
        if not pets:
            print("No pets found. Add a pet with: petvax pet add")
        else:
            print(f"{'ID':<4} {'Name':<12} {'Species':<8} {'Breed':<15} {'DOB':<12} {'Gender':<8} {'Neut':<5} {'Owner':<15}")
            print("-" * 95)
            for p in pets:
                dob = p[4] or "N/A"
                gender = p[6] or "-"
                neutered = "Yes" if p[7] else "No"
                breed = p[3][:15] if p[3] else "-"
                owner = p[8][:15] if p[8] else "-"
                print(f"{p[0]:<4} {p[1]:<12} {p[2]:<8} {breed:<15} {dob:<12} {gender:<8} {neutered:<5} {owner:<15}")
        conn.close()
        
    elif args.subcommand == 'edit':
        conn = get_db_connection()
        
        # First, show list of pets to choose from
        cursor = conn.execute("SELECT id, name, species FROM pets ORDER BY name")
        pets = cursor.fetchall()
        
        if not pets:
            print("No pets to edit. Add a pet first.")
            conn.close()
            return
        
        print("Select a pet to edit:")
        for p in pets:
            print(f"  [{p[0]}] {p[1]} ({p[2]})")
        
        try:
            pet_id = int(input("\nEnter pet ID: ").strip())
            cursor = conn.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
            pet = cursor.fetchone()
            
            if not pet:
                print(f"Error: Pet with ID {pet_id} not found.")
                conn.close()
                return
            
            # Show current values and get new ones
            print(f"\nEditing pet: {pet[1]} ({pet[2]})")
            print("Press Enter to keep current value.\n")
            
            fields = ['name', 'species', 'breed', 'date_of_birth', 'color', 'microchip_id', 
                     'gender', 'neutered', 'owner_name', 'owner_phone', 'owner_email', 'notes']
            current = dict(zip(fields, pet[1:]))
            
            updates = {}
            for field in fields:
                current_val = current[field]
                prompt = f"{field.replace('_', ' ').title()} [{current_val}]: "
                new_val = input(prompt).strip()
                if new_val:
                    updates[field] = new_val
            
            if updates:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [pet_id]
                conn.execute(f"UPDATE pets SET {set_clause} WHERE id = ?", values)
                conn.commit()
                print(f"\n✓ Pet updated successfully!")
            else:
                print("\nNo changes made.")
                
        except ValueError:
            print("Error: Invalid pet ID.")
        except Exception as e:
            print(f"Error updating pet: {e}")
        finally:
            conn.close()
            
    elif args.subcommand == 'delete':
        conn = get_db_connection()
        
        # First show list of pets
        cursor = conn.execute("SELECT id, name, species FROM pets ORDER BY name")
        pets = cursor.fetchall()
        
        if not pets:
            print("No pets to delete.")
            conn.close()
            return
        
        print("Select a pet to delete:")
        for p in pets:
            print(f"  [{p[0]}] {p[1]} ({p[2]})")
        
        try:
            pet_id = int(input("\nEnter pet ID to delete: ").strip())
            cursor = conn.execute("SELECT name FROM pets WHERE id = ?", (pet_id,))
            pet = cursor.fetchone()
            
            if not pet:
                print(f"Error: Pet with ID {pet_id} not found.")
                conn.close()
                return
            
            confirm = input(f"⚠️  Delete pet '{pet[0]}' and ALL vaccination records? (yes/no): ").strip().lower()
            if confirm == 'yes':
                conn.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
                conn.commit()
                print(f"✓ Pet '{pet[0]}' deleted successfully.")
            else:
                print("Deletion cancelled.")
                
        except ValueError:
            print("Error: Invalid pet ID.")
        except Exception as e:
            print(f"Error deleting pet: {e}")
        finally:
            conn.close()


def cmd_vaccine(args):
    """Vaccination management commands"""
    from app.core.io import get_db_connection
    from app.core.dates import calculate_rabies_due_date, calculate_annual_booster_due
    
    if args.subcommand == 'add':
        conn = get_db_connection()
        
        # First, show list of pets to choose from
        cursor = conn.execute("SELECT id, name, species FROM pets ORDER BY name")
        pets = cursor.fetchall()
        
        if not pets:
            print("No pets found. Add a pet first with: petvax pet add")
            conn.close()
            return
        
        print("Select a pet to add vaccination record for:")
        for p in pets:
            print(f"  [{p[0]}] {p[1]} ({p[2]})")
        
        try:
            pet_id = int(input("\nEnter pet ID: ").strip())
            cursor = conn.execute("SELECT name, species FROM pets WHERE id = ?", (pet_id,))
            pet = cursor.fetchone()
            
            if not pet:
                print(f"Error: Pet with ID {pet_id} not found.")
                conn.close()
                return
            
            pet_name, pet_species = pet
            print(f"\nAdding vaccination for: {pet_name} ({pet_species})")
            print("-" * 40)
            
            # Show available vaccines for this species
            cursor = conn.execute("""
                SELECT id, name, description, is_mandatory 
                FROM vaccines 
                WHERE species = ? OR species = 'both'
                ORDER BY is_mandatory DESC, name
            """, (pet_species,))
            vaccines = cursor.fetchall()
            
            print("\nAvailable vaccines:")
            for v in vaccines:
                mandatory = " [MANDATORY]" if v[3] else ""
                print(f"  [{v[0]}] {v[1]}{mandatory}")
                if v[2]:
                    print(f"       {v[2][:60]}...")
            
            vaccine_id = int(input("\nEnter vaccine ID: ").strip())
            cursor = conn.execute("SELECT name FROM vaccines WHERE id = ?", (vaccine_id,))
            vaccine = cursor.fetchone()
            
            if not vaccine:
                print(f"Error: Vaccine with ID {vaccine_id} not found.")
                conn.close()
                return
            
            vaccine_name = vaccine[0]
            
            # Get date administered
            date_administered = input("Date administered (YYYY-MM-DD): ").strip()
            if not date_administered:
                print("Error: Date administered is required.")
                conn.close()
                return
            
            # Validate date format
            from datetime import datetime
            try:
                administered_date = datetime.strptime(date_administered, "%Y-%m-%d")
            except ValueError:
                print("Error: Invalid date format. Use YYYY-MM-DD.")
                conn.close()
                return
            
            # Auto-calculate next due date based on vaccine type
            next_due_date = None
            if vaccine_name.lower() == 'rabies':
                next_due = calculate_rabies_due_date(administered_date, is_boosters=True)
                next_due_date = next_due.strftime("%Y-%m-%d")
                print(f"Next due date (auto-calculated for rabies booster): {next_due_date}")
            elif vaccine_name.lower() in ['dhpp', 'dapp', 'fvrcp']:
                next_due = calculate_annual_booster_due(administered_date, vaccine_name.lower())
                next_due_date = next_due.strftime("%Y-%m-%d")
                print(f"Next due date (auto-calculated for annual booster): {next_due_date}")
            else:
                next_due_date = input("Next due date (YYYY-MM-DD, optional): ").strip() or None
            
            # Optional fields
            batch_number = input("Batch number (optional): ").strip() or None
            vet_name = input("Vet name (optional): ").strip() or None
            vet_license = input("Vet license number (optional): ").strip() or None
            certificate_number = input("Certificate number (optional): ").strip() or None
            notes = input("Notes (optional): ").strip() or None
            
            # Insert the record
            conn.execute("""
                INSERT INTO pet_vaccinations 
                (pet_id, vaccine_id, date_administered, next_due_date, batch_number, 
                 vet_name, vet_license, certificate_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pet_id, vaccine_id, date_administered, next_due_date, batch_number,
                  vet_name, vet_license, certificate_number, notes))
            conn.commit()
            
            record_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"\n✓ Vaccination record added successfully! (ID: {record_id})")
            if next_due_date:
                print(f"  Next due: {next_due_date}")
                
        except ValueError:
            print("Error: Invalid ID. Please enter a number.")
        except Exception as e:
            print(f"Error adding vaccination record: {e}")
        finally:
            conn.close()
            
    elif args.subcommand == 'list':
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT pv.id, p.name, p.species, v.name, pv.date_administered, pv.next_due_date, v.is_mandatory
            FROM pet_vaccinations pv
            JOIN pets p ON pv.pet_id = p.id
            JOIN vaccines v ON pv.vaccine_id = v.id
            ORDER BY p.name, pv.date_administered DESC
        """)
        records = cursor.fetchall()
        if not records:
            print("No vaccination records found.")
            print("Add a record with: petvax vaccine add")
        else:
            print(f"{'ID':<4} {'Pet':<12} {'Species':<7} {'Vaccine':<15} {'Given':<12} {'Next Due':<12} {'Mand':<5}")
            print("-" * 85)
            for r in records:
                given = r[4] or "N/A"
                due = r[5] or "N/A"
                mand = "Yes" if r[6] else "-"
                print(f"{r[0]:<4} {r[1]:<12} {r[2]:<7} {r[3]:<15} {given:<12} {due:<12} {mand:<5}")
        conn.close()
        
    elif args.subcommand == 'edit':
        conn = get_db_connection()
        
        # First, show list of vaccination records
        cursor = conn.execute("""
            SELECT pv.id, p.name, v.name, pv.date_administered, pv.next_due_date
            FROM pet_vaccinations pv
            JOIN pets p ON pv.pet_id = p.id
            JOIN vaccines v ON pv.vaccine_id = v.id
            ORDER BY p.name, pv.date_administered
        """)
        records = cursor.fetchall()
        
        if not records:
            print("No vaccination records to edit.")
            conn.close()
            return
        
        print("Select a vaccination record to edit:")
        for r in records:
            print(f"  [{r[0]}] {r[1]} - {r[2]} (given: {r[3]}, due: {r[4] or 'N/A'})")
        
        try:
            record_id = int(input("\nEnter record ID: ").strip())
            cursor = conn.execute("SELECT * FROM pet_vaccinations WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            
            if not record:
                print(f"Error: Record with ID {record_id} not found.")
                conn.close()
                return
            
            print(f"\nEditing vaccination record #{record_id}")
            print("Press Enter to keep current value.\n")
            
            # Record fields: id, pet_id, vaccine_id, date_administered, next_due_date,
            #                batch_number, vet_clinic_id, vet_name, vet_license, 
            #                certificate_number, notes, created_at
            fields = ['date_administered', 'next_due_date', 'batch_number', 
                     'vet_name', 'vet_license', 'certificate_number', 'notes']
            current = dict(zip(fields, record[3:10]))
            
            updates = {}
            for field in fields:
                current_val = current[field] or ""
                prompt = f"{field.replace('_', ' ').title()} [{current_val}]: "
                new_val = input(prompt).strip()
                if new_val:
                    updates[field] = new_val
            
            if updates:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [record_id]
                conn.execute(f"UPDATE pet_vaccinations SET {set_clause} WHERE id = ?", values)
                conn.commit()
                print(f"\n✓ Vaccination record updated successfully!")
            else:
                print("\nNo changes made.")
                
        except ValueError:
            print("Error: Invalid record ID.")
        except Exception as e:
            print(f"Error updating record: {e}")
        finally:
            conn.close()
            
    elif args.subcommand == 'delete':
        conn = get_db_connection()
        
        # First, show list of vaccination records
        cursor = conn.execute("""
            SELECT pv.id, p.name, v.name, pv.date_administered
            FROM pet_vaccinations pv
            JOIN pets p ON pv.pet_id = p.id
            JOIN vaccines v ON pv.vaccine_id = v.id
            ORDER BY p.name, pv.date_administered
        """)
        records = cursor.fetchall()
        
        if not records:
            print("No vaccination records to delete.")
            conn.close()
            return
        
        print("Select a vaccination record to delete:")
        for r in records:
            print(f"  [{r[0]}] {r[1]} - {r[2]} (given: {r[3]})")
        
        try:
            record_id = int(input("\nEnter record ID to delete: ").strip())
            cursor = conn.execute("""
                SELECT p.name, v.name 
                FROM pet_vaccinations pv
                JOIN pets p ON pv.pet_id = p.id
                JOIN vaccines v ON pv.vaccine_id = v.id
                WHERE pv.id = ?
            """, (record_id,))
            record = cursor.fetchone()
            
            if not record:
                print(f"Error: Record with ID {record_id} not found.")
                conn.close()
                return
            
            confirm = input(f"⚠️  Delete vaccination record for '{record[0]}' - {record[1]}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                conn.execute("DELETE FROM pet_vaccinations WHERE id = ?", (record_id,))
                conn.commit()
                print(f"✓ Vaccination record deleted successfully.")
            else:
                print("Deletion cancelled.")
                
        except ValueError:
            print("Error: Invalid record ID.")
        except Exception as e:
            print(f"Error deleting record: {e}")
        finally:
            conn.close()


def cmd_reminder(args):
    """Show, generate, and manage reminders"""
    from app.core.reminders import ReminderEngine, ReminderConfig, ReminderType, ReminderStatus
    from app.core.io import get_db_connection, get_db_path
    
    # Default to 'show' if no subcommand
    subcommand = args.subcommand if args.subcommand else 'show'
    
    # Get days for show command (default to 30 if not specified)
    days = getattr(args, 'days', 30) if subcommand == 'show' else 30
    
    if subcommand == 'list':
        # List all reminders with optional filtering
        conn = get_db_connection()
        
        status_filter = args.status if hasattr(args, 'status') else None
        type_filter = args.type if hasattr(args, 'type') else None
        
        query = """
            SELECT 
                r.id,
                r.pet_id,
                r.vaccine_id,
                r.reminder_type,
                r.due_date,
                r.status,
                r.created_at,
                r.sent_at,
                p.name as pet_name,
                v.name as vaccine_name
            FROM reminders r
            JOIN pets p ON r.pet_id = p.id
            JOIN vaccines v ON r.vaccine_id = v.id
            WHERE 1=1
        """
        params = []
        
        if status_filter:
            query += " AND r.status = ?"
            params.append(status_filter)
        if type_filter:
            query += " AND r.reminder_type = ?"
            params.append(type_filter)
        
        query += " ORDER BY r.due_date"
        
        cursor = conn.execute(query, params)
        reminders = cursor.fetchall()
        
        if not reminders:
            print("No reminders found.")
        else:
            print(f"{'ID':<4} {'Pet':<12} {'Vaccine':<15} {'Type':<10} {'Due Date':<12} {'Status':<10}")
            print("-" * 75)
            for r in reminders:
                print(f"{r[0]:<4} {r[8]:<12} {r[9]:<15} {r[3]:<10} {r[4]:<12} {r[5]:<10}")
        conn.close()
        
    elif subcommand == 'generate':
        # Generate new reminders from vaccination records
        conn = get_db_connection()
        config = ReminderConfig(
            db_path=str(get_db_path()),
            due_soon_days=30,
            overdue_days=0,
            upcoming_days=60
        )
        engine = ReminderEngine(config)
        
        stats = engine.generate_reminders()
        print(f"Reminder generation complete:")
        print(f"  Created: {stats['created']}")
        print(f"  Skipped (existing): {stats['skipped']}")
        if stats['errors'] > 0:
            print(f"  Errors: {stats['errors']}")
        
        engine.close()
        
    elif subcommand == 'show':
        # Show upcoming reminders (default behavior)
        conn = get_db_connection()
        config = ReminderConfig(
            db_path=str(get_db_path()),
            due_soon_days=days,
            overdue_days=0,
            upcoming_days=days
        )
        engine = ReminderEngine(config)
        
        reminders = engine.get_pending_reminders(days_ahead=days)
        
        if not reminders:
            print(f"No reminders for the next {days} days.")
        else:
            print(f"Reminders for the next {days} days:")
            print("-" * 70)
            for r in reminders:
                status = r.reminder_type.value
                message = f"{r.vaccine_name} - due {r.due_date}"
                print(f"[{status:^12}] {r.pet_name}: {message}")
        engine.close()
        
    elif subcommand == 'mark':
        # Mark a reminder as sent or completed
        conn = get_db_connection()
        
        if not args.id:
            print("Error: Reminder ID required. Use: petvax reminder mark <id> <sent|completed>")
            conn.close()
            return
        
        try:
            reminder_id = int(args.id)
        except ValueError:
            print("Error: Invalid reminder ID.")
            conn.close()
            return
        
        if args.mark_type not in ('sent', 'completed'):
            print("Error: Mark type must be 'sent' or 'completed'")
            conn.close()
            return
        
        cursor = conn.execute("SELECT id, status FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            print(f"Error: Reminder with ID {reminder_id} not found.")
            conn.close()
            return
        
        new_status = 'sent' if args.mark_type == 'sent' else 'completed'
        conn.execute(f"UPDATE reminders SET status = '{new_status}' WHERE id = ?", (reminder_id,))
        conn.commit()
        print(f"✓ Reminder {reminder_id} marked as {new_status}")
        
        conn.close()
        
    elif subcommand == 'cancel':
        # Cancel a reminder
        conn = get_db_connection()
        
        if not args.id:
            print("Error: Reminder ID required. Use: petvax reminder cancel <id>")
            conn.close()
            return
        
        try:
            reminder_id = int(args.id)
        except ValueError:
            print("Error: Invalid reminder ID.")
            conn.close()
            return
        
        cursor = conn.execute("SELECT id FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            print(f"Error: Reminder with ID {reminder_id} not found.")
            conn.close()
            return
        
        conn.execute("UPDATE reminders SET status = 'cancelled' WHERE id = ?", (reminder_id,))
        conn.commit()
        print(f"✓ Reminder {reminder_id} cancelled")
        
        conn.close()
        
    elif subcommand == 'delete':
        # Delete a reminder permanently
        conn = get_db_connection()
        
        if not args.id:
            print("Error: Reminder ID required. Use: petvax reminder delete <id>")
            conn.close()
            return
        
        try:
            reminder_id = int(args.id)
        except ValueError:
            print("Error: Invalid reminder ID.")
            conn.close()
            return
        
        cursor = conn.execute("""
            SELECT r.id, p.name, v.name, r.due_date
            FROM reminders r
            JOIN pets p ON r.pet_id = p.id
            JOIN vaccines v ON r.vaccine_id = v.id
            WHERE r.id = ?
        """, (reminder_id,))
        reminder = cursor.fetchone()
        
        if not reminder:
            print(f"Error: Reminder with ID {reminder_id} not found.")
            conn.close()
            return
        
        confirm = input(f"⚠️  Delete reminder for '{reminder[1]}' - {reminder[2]}? (yes/no): ").strip().lower()
        if confirm == 'yes':
            conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            print(f"✓ Reminder {reminder_id} deleted")
        else:
            print("Deletion cancelled.")
        
        conn.close()


def cmd_compliance(args):
    """Check HK vaccination compliance"""
    from app.core.rules import check_compliance, format_compliance_summary, Scenario, PetType
    from app.core.io import get_db_connection
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all pets or specific pet if --pet flag provided
    if hasattr(args, 'pet_id') and args.pet_id:
        cursor.execute("SELECT id, name, species, date_of_birth FROM pets WHERE id = ?", (args.pet_id,))
        pets = cursor.fetchall()
        if not pets:
            print(f"No pet found with ID {args.pet_id}")
            conn.close()
            return
    else:
        cursor.execute("SELECT id, name, species, date_of_birth FROM pets")
        pets = cursor.fetchall()
    
    if not pets:
        print("No pets to check. Add a pet first with: petvax pet add")
        conn.close()
        return
    
    # Check if detailed output is requested
    detailed = getattr(args, 'detailed', False)
    
    compliant_count = 0
    non_compliant_count = 0
    
    for pet in pets:
        pet_id, pet_name, species, dob = pet
        pet_type = PetType.DOG if species == 'dog' else PetType.CAT
        
        # Get vaccinations for this pet
        cursor.execute("""
            SELECT v.name, pv.date_administered, pv.next_due_date
            FROM pet_vaccinations pv
            JOIN vaccines v ON pv.vaccine_id = v.id
            WHERE pv.pet_id = ?
        """, (pet_id,))
        
        vaccinations = []
        for row in cursor.fetchall():
            vaccinations.append({
                "vaccine_name": row[0],
                "date_administered": datetime.strptime(row[1], "%Y-%m-%d") if row[1] else None,
                "next_due_date": datetime.strptime(row[2], "%Y-%m-%d") if row[2] else None
            })
        
        result = check_compliance(
            pet_id=pet_id,
            pet_name=pet_name,
            scenario=Scenario.HK_RESIDENT,
            pet_type=pet_type,
            vaccinations=vaccinations
        )
        
        if result.is_compliant:
            compliant_count += 1
            if detailed:
                print(format_compliance_summary(result))
        else:
            non_compliant_count += 1
            # Print detailed info for non-compliant pets
            if detailed:
                print(format_compliance_summary(result))
            else:
                # Brief summary of what's missing
                missing = [r.vaccine_name for r in result.requirements if r.status.value in ['not_done', 'overdue']]
                print(f"⚠️  {pet_name}: Missing/overdue: {', '.join(missing)}")
    
    print(f"\nCompliance Report: {compliant_count} compliant, {non_compliant_count} non-compliant")
    conn.close()


def cmd_export(args):
    """Export data"""
    from app.core.io import export_json, export_csv, get_db_path
    
    if args.format == 'json':
        data = export_json()
        output_path = args.output or "pets_export.json"
        import json
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Exported to: {output_path}")
    elif args.format == 'csv':
        files = export_csv()
        print("Exported to:")
        for name, path in files.items():
            print(f"  {name}: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="PetVaxHK - Local-first pet vaccine tracker for Hong Kong",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Pet subcommand
    pet_parser = subparsers.add_parser('pet', help='Manage pets')
    pet_sub = pet_parser.add_subparsers(dest='subcommand', help='Pet operations')
    pet_sub.add_parser('list', help='List all pets')
    pet_sub.add_parser('add', help='Add a new pet')
    pet_sub.add_parser('edit', help='Edit a pet')
    pet_sub.add_parser('delete', help='Delete a pet')
    pet_parser.set_defaults(func=cmd_pet)
    
    # Vaccine subcommand
    vaccine_parser = subparsers.add_parser('vaccine', help='Manage vaccinations')
    vaccine_sub = vaccine_parser.add_subparsers(dest='subcommand', help='Vaccine operations')
    vaccine_sub.add_parser('list', help='List all vaccinations')
    vaccine_sub.add_parser('add', help='Add a vaccination record')
    vaccine_sub.add_parser('edit', help='Edit a vaccination record')
    vaccine_sub.add_parser('delete', help='Delete a vaccination record')
    vaccine_parser.set_defaults(func=cmd_vaccine)
    
    # Reminder subcommand
    reminder_parser = subparsers.add_parser('reminder', help='Show, generate, and manage reminders')
    reminder_sub = reminder_parser.add_subparsers(dest='subcommand', help='Reminder operations')
    
    # reminder show (default)
    reminder_show = reminder_sub.add_parser('show', help='Show upcoming reminders')
    reminder_show.add_argument('-d', '--days', type=int, default=30, help='Days ahead to check (default: 30)')
    
    # reminder list
    reminder_list = reminder_sub.add_parser('list', help='List all reminders')
    reminder_list.add_argument('-s', '--status', choices=['pending', 'sent', 'completed', 'cancelled'], 
                                help='Filter by status')
    reminder_list.add_argument('-t', '--type', choices=['due_soon', 'overdue', 'upcoming'],
                                help='Filter by reminder type')
    
    # reminder generate
    reminder_sub.add_parser('generate', help='Generate new reminders from vaccination records')
    
    # reminder mark
    reminder_mark = reminder_sub.add_parser('mark', help='Mark reminder as sent or completed')
    reminder_mark.add_argument('id', help='Reminder ID')
    reminder_mark.add_argument('mark_type', choices=['sent', 'completed'], help='Status to set')
    
    # reminder cancel
    reminder_cancel = reminder_sub.add_parser('cancel', help='Cancel a reminder')
    reminder_cancel.add_argument('id', help='Reminder ID')
    
    # reminder delete
    reminder_delete = reminder_sub.add_parser('delete', help='Delete a reminder permanently')
    reminder_delete.add_argument('id', help='Reminder ID')
    
    reminder_parser.set_defaults(func=cmd_reminder)
    
    # Compliance subcommand
    compliance_parser = subparsers.add_parser('compliance', help='Check HK vaccination compliance')
    compliance_parser.add_argument('-d', '--detailed', action='store_true', 
                                   help='Show detailed compliance report for each pet')
    compliance_parser.add_argument('-p', '--pet', type=int, dest='pet_id', 
                                   help='Check compliance for a specific pet by ID')
    compliance_parser.set_defaults(func=cmd_compliance)
    
    # Export subcommand
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('-f', '--format', choices=['json', 'csv'], default='json', help='Export format')
    export_parser.add_argument('-o', '--output', help='Output file path')
    export_parser.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    # Initialize database if needed
    from app.core.io import init_db
    init_db()
    
    # Execute command
    args.func(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
