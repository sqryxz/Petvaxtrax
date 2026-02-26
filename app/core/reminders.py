"""
Reminder Engine for PetVaxHK.

Generates reminders for upcoming and overdue vaccinations based on
vaccination records in the database and HK AFCD compliance rules.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ReminderType(Enum):
    """Types of reminders."""
    DUE_SOON = "due_soon"      # Within 30 days
    OVERDUE = "overdue"        # Past due date
    UPCOMING = "upcoming"      # Future reminder (e.g., 60 days out)


class ReminderStatus(Enum):
    """Status of a reminder."""
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Reminder:
    """Represents a single reminder."""
    id: Optional[int]
    pet_id: int
    vaccine_id: int
    reminder_type: ReminderType
    due_date: str  # ISO 8601 date
    status: ReminderStatus
    created_at: Optional[str]
    # Join data
    pet_name: Optional[str] = None
    vaccine_name: Optional[str] = None


@dataclass
class ReminderConfig:
    """Configuration for reminder generation."""
    db_path: str
    due_soon_days: int = 30        # Remind when within this many days
    overdue_days: int = 0          # Remind when past due
    upcoming_days: int = 60        # Future reminder lead time
    max_lookahead_days: int = 90   # Don't create reminders beyond this


class ReminderEngine:
    """Engine for generating and managing vaccination reminders."""
    
    def __init__(self, config: ReminderConfig):
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.config.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_pets_with_vaccinations(self) -> list[dict]:
        """Get all pets with their vaccination records."""
        query = """
            SELECT 
                p.id as pet_id,
                p.name as pet_name,
                p.species,
                p.date_of_birth,
                v.id as vaccine_id,
                v.name as vaccine_name,
                v.is_mandatory,
                pv.date_administered,
                pv.next_due_date
            FROM pets p
            CROSS JOIN vaccines v
            LEFT JOIN pet_vaccinations pv ON p.id = pv.pet_id AND v.id = pv.vaccine_id
            WHERE v.species = p.species OR v.species = 'both'
            ORDER BY p.id, v.id
        """
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def calculate_reminder(
        self,
        pet_id: int,
        vaccine_id: int,
        next_due_date: Optional[str],
        is_mandatory: bool
    ) -> Optional[Reminder]:
        """
        Calculate if a reminder should be created for a vaccination.
        
        Args:
            pet_id: Pet ID
            vaccine_id: Vaccine ID
            next_due_date: Next due date from vaccination record
            is_mandatory: Whether this vaccine is mandatory
        
        Returns:
            Reminder if one should be created, None otherwise
        """
        if not next_due_date:
            return None
        
        try:
            due_date = datetime.strptime(next_due_date, "%Y-%m-%d")
        except ValueError:
            return None
        
        now = datetime.now()
        today = now.date()
        due = due_date.date()
        days_until_due = (due - today).days
        
        # Don't create reminders too far in the future
        if days_until_due > self.config.max_lookahead_days:
            return None
        
        # Determine reminder type
        if days_until_due < self.config.overdue_days:
            reminder_type = ReminderType.OVERDUE
        elif days_until_due <= self.config.due_soon_days:
            reminder_type = ReminderType.DUE_SOON
        elif days_until_due <= self.config.upcoming_days:
            reminder_type = ReminderType.UPCOMING
        else:
            return None  # No reminder needed
        
        return Reminder(
            id=None,
            pet_id=pet_id,
            vaccine_id=vaccine_id,
            reminder_type=reminder_type,
            due_date=next_due_date,
            status=ReminderStatus.PENDING,
            created_at=None
        )
    
    def get_existing_reminders(self) -> dict[tuple[int, int], str]:
        """Get existing pending reminders to avoid duplicates."""
        query = """
            SELECT pet_id, vaccine_id, status 
            FROM reminders 
            WHERE status = 'pending'
        """
        cursor = self.conn.execute(query)
        return {
            (row["pet_id"], row["vaccine_id"]): row["status"]
            for row in cursor.fetchall()
        }
    
    def create_reminder(self, reminder: Reminder) -> int:
        """Insert a new reminder into the database."""
        query = """
            INSERT INTO reminders (
                pet_id, vaccine_id, reminder_type, due_date, status, created_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        """
        cursor = self.conn.execute(
            query,
            (
                reminder.pet_id,
                reminder.vaccine_id,
                reminder.reminder_type.value,
                reminder.due_date,
                reminder.status.value
            )
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def generate_reminders(self) -> dict[str, int]:
        """
        Generate reminders for all pets and vaccinations.
        
        Returns:
            Dict with counts: {'created': N, 'skipped': N, 'errors': N}
        """
        stats = {"created": 0, "skipped": 0, "errors": 0}
        
        existing = self.get_existing_reminders()
        pets_vaccs = self.get_pets_with_vaccinations()
        
        for record in pets_vaccs:
            try:
                pet_id = record["pet_id"]
                vaccine_id = record["vaccine_id"]
                
                # Skip if already has pending reminder
                if (pet_id, vaccine_id) in existing:
                    stats["skipped"] += 1
                    continue
                
                # Calculate if reminder needed
                reminder = self.calculate_reminder(
                    pet_id=pet_id,
                    vaccine_id=vaccine_id,
                    next_due_date=record["next_due_date"],
                    is_mandatory=bool(record["is_mandatory"])
                )
                
                if reminder:
                    self.create_reminder(reminder)
                    stats["created"] += 1
                else:
                    stats["skipped"] += 1
                    
            except Exception as e:
                print(f"Error processing pet {record.get('pet_id')}, vaccine {record.get('vaccine_id')}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def get_pending_reminders(
        self,
        days_ahead: int = 30
    ) -> list[Reminder]:
        """Get all pending reminders within the specified timeframe."""
        query = """
            SELECT 
                r.id,
                r.pet_id,
                r.vaccine_id,
                r.reminder_type,
                r.due_date,
                r.status,
                r.created_at,
                p.name as pet_name,
                v.name as vaccine_name
            FROM reminders r
            JOIN pets p ON r.pet_id = p.id
            JOIN vaccines v ON r.vaccine_id = v.id
            WHERE r.status = 'pending'
            AND r.due_date <= date('now', '+' || ? || ' days')
            ORDER BY r.due_date
        """
        cursor = self.conn.execute(query, (days_ahead,))
        
        reminders = []
        for row in cursor.fetchall():
            reminder = Reminder(
                id=row["id"],
                pet_id=row["pet_id"],
                vaccine_id=row["vaccine_id"],
                reminder_type=ReminderType(row["reminder_type"]),
                due_date=row["due_date"],
                status=ReminderStatus(row["status"]),
                created_at=row["created_at"],
                pet_name=row["pet_name"],
                vaccine_name=row["vaccine_name"]
            )
            reminders.append(reminder)
        
        return reminders
    
    def mark_sent(self, reminder_id: int) -> bool:
        """Mark a reminder as sent."""
        query = "UPDATE reminders SET status = 'sent', sent_at = datetime('now') WHERE id = ?"
        cursor = self.conn.execute(query, (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def mark_completed(self, reminder_id: int) -> bool:
        """Mark a reminder as completed (vaccination received)."""
        query = "UPDATE reminders SET status = 'completed' WHERE id = ?"
        cursor = self.conn.execute(query, (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def cancel_reminder(self, reminder_id: int) -> bool:
        """Cancel a reminder."""
        query = "UPDATE reminders SET status = 'cancelled' WHERE id = ?"
        cursor = self.conn.execute(query, (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0


def format_reminder_message(reminder: Reminder) -> str:
    """Format a reminder as a human-readable message."""
    due_date = datetime.strptime(reminder.due_date, "%Y-%m-%d")
    now = datetime.now()
    days_until = (due_date.date() - now.date()).days
    
    type_emoji = {
        ReminderType.DUE_SOON: "⚠️",
        ReminderType.OVERDUE: "🚨",
        ReminderType.UPCOMING: "📅"
    }.get(reminder.reminder_type, "📋")
    
    status_text = {
        ReminderType.DUE_SOON: f"Due in {days_until} days",
        ReminderType.OVERDUE: f"Overdue by {-days_until} days",
        ReminderType.UPCOMING: f"Due in {days_until} days"
    }.get(reminder.reminder_type, "")
    
    return (
        f"{type_emoji} **{reminder.pet_name}**: {reminder.vaccine_name} "
        f"vaccination {status_text}"
    )


if __name__ == "__main__":
    # Demo usage
    config = ReminderConfig(db_path="outputs/pets.db")
    
    with ReminderEngine(config) as engine:
        print("=== PetVaxHK Reminder Engine Demo ===\n")
        
        # Generate reminders
        stats = engine.generate_reminders()
        print(f"Generated reminders: {stats}")
        
        # Get pending reminders
        reminders = engine.get_pending_reminders(days_ahead=60)
        print(f"\nPending reminders ({len(reminders)}):")
        for r in reminders[:10]:
            print(f"  {format_reminder_message(r)}")
