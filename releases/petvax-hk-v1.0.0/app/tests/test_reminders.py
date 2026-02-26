"""
Unit tests for the reminder engine.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.core.reminders import (
    ReminderEngine,
    ReminderConfig,
    Reminder,
    ReminderType,
    ReminderStatus,
    format_reminder_message
)


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with schema and sample data."""
    db_path = tmp_path / "test_pets.db"
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Create schema
    conn.executescript("""
        PRAGMA foreign_keys = ON;
        
        CREATE TABLE pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL CHECK(species IN ('dog', 'cat')),
            breed TEXT,
            date_of_birth TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE vaccines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL CHECK(species IN ('dog', 'cat', 'both')),
            is_mandatory INTEGER DEFAULT 0
        );
        
        CREATE TABLE pet_vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vaccine_id INTEGER NOT NULL,
            date_administered TEXT NOT NULL,
            next_due_date TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
            FOREIGN KEY (vaccine_id) REFERENCES vaccines(id)
        );
        
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vaccine_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            sent_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
            FOREIGN KEY (vaccine_id) REFERENCES vaccines(id)
        );
        
        -- Insert test vaccines
        INSERT INTO vaccines (id, name, species, is_mandatory) VALUES
        (1, 'Rabies', 'dog', 1),
        (2, 'DHPP', 'dog', 1),
        (3, 'Rabies', 'cat', 1),
        (4, 'FVRCP', 'cat', 1);
        
        -- Insert test pets
        INSERT INTO pets (id, name, species) VALUES
        (1, 'Buddy', 'dog'),
        (2, 'Whiskers', 'cat');
    """)
    
    conn.close()
    return db_path


@pytest.fixture
def config(test_db):
    """Create test config."""
    return ReminderConfig(
        db_path=str(test_db),  # Convert Path to string
        due_soon_days=30,
        overdue_days=0,
        upcoming_days=60,
        max_lookahead_days=90
    )


class TestReminderEngine:
    """Tests for ReminderEngine."""
    
    def test_get_pets_with_vaccinations(self, config):
        """Test fetching pets with vaccination records."""
        with ReminderEngine(config) as engine:
            pets_vaccs = engine.get_pets_with_vaccinations()
            
            # Should have 2 pets x 2 relevant vaccines = 4 records
            assert len(pets_vaccs) == 4
            
            # Check structure
            for pv in pets_vaccs:
                assert "pet_id" in pv
                assert "vaccine_id" in pv
                assert "pet_name" in pv
                assert "vaccine_name" in pv
    
    def test_calculate_reminder_due_soon(self, config):
        """Test reminder calculation for due soon."""
        engine = ReminderEngine(config)
        
        # Due in 15 days - should create due_soon
        reminder = engine.calculate_reminder(
            pet_id=1,
            vaccine_id=1,
            next_due_date=(datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
            is_mandatory=True
        )
        
        assert reminder is not None
        assert reminder.reminder_type == ReminderType.DUE_SOON
    
    def test_calculate_reminder_overdue(self, config):
        """Test reminder calculation for overdue."""
        engine = ReminderEngine(config)
        
        # Overdue by 5 days
        reminder = engine.calculate_reminder(
            pet_id=1,
            vaccine_id=1,
            next_due_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            is_mandatory=True
        )
        
        assert reminder is not None
        assert reminder.reminder_type == ReminderType.OVERDUE
    
    def test_calculate_reminder_upcoming(self, config):
        """Test reminder calculation for upcoming."""
        engine = ReminderEngine(config)
        
        # Due in 45 days - should create upcoming (within 60 days)
        reminder = engine.calculate_reminder(
            pet_id=1,
            vaccine_id=1,
            next_due_date=(datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
            is_mandatory=True
        )
        
        assert reminder is not None
        assert reminder.reminder_type == ReminderType.UPCOMING
    
    def test_calculate_reminder_too_far(self, config):
        """Test that reminders beyond max_lookahead are skipped."""
        engine = ReminderEngine(config)
        
        # Due in 100 days - beyond max_lookahead_days (90)
        reminder = engine.calculate_reminder(
            pet_id=1,
            vaccine_id=1,
            next_due_date=(datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d"),
            is_mandatory=True
        )
        
        assert reminder is None
    
    def test_calculate_reminder_no_due_date(self, config):
        """Test that missing due date returns None."""
        engine = ReminderEngine(config)
        
        reminder = engine.calculate_reminder(
            pet_id=1,
            vaccine_id=1,
            next_due_date=None,
            is_mandatory=True
        )
        
        assert reminder is None
    
    def test_get_existing_reminders(self, config, test_db):
        """Test fetching existing pending reminders."""
        # Pre-add a reminder
        conn = sqlite3.connect(str(test_db))
        conn.execute("""
            INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
            VALUES (1, 1, 'due_soon', '2026-03-01', 'pending')
        """)
        conn.commit()
        conn.close()
        
        with ReminderEngine(config) as engine:
            existing = engine.get_existing_reminders()
            
            assert (1, 1) in existing
            assert existing[(1, 1)] == "pending"
    
    def test_create_reminder(self, config):
        """Test creating a reminder."""
        engine = ReminderEngine(config)
        
        reminder = Reminder(
            id=None,
            pet_id=1,
            vaccine_id=1,
            reminder_type=ReminderType.DUE_SOON,
            due_date="2026-03-15",
            status=ReminderStatus.PENDING,
            created_at=None
        )
        
        reminder_id = engine.create_reminder(reminder)
        
        assert reminder_id > 0
        
        # Verify it was created using engine's connection
        cursor = engine.conn.execute(
            "SELECT * FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["pet_id"] == 1
        assert row["vaccine_id"] == 1
        assert row["status"] == "pending"
        engine.close()
    
    def test_generate_reminders(self, config, test_db):
        """Test generating reminders from pet data."""
        # Add a vaccination record due soon
        conn = sqlite3.connect(str(test_db))
        conn.execute("""
            INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered, next_due_date)
            VALUES (1, 1, '2026-01-01', '2026-03-01')
        """)
        conn.commit()
        conn.close()
        
        with ReminderEngine(config) as engine:
            stats = engine.generate_reminders()
            
            assert stats["created"] >= 1
            assert stats["errors"] == 0
    
    def test_get_pending_reminders(self, config, test_db):
        """Test fetching pending reminders."""
        # Add a reminder
        conn = sqlite3.connect(str(test_db))
        conn.execute("""
            INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
            VALUES (1, 1, 'due_soon', '2026-03-15', 'pending')
        """)
        conn.commit()
        conn.close()
        
        with ReminderEngine(config) as engine:
            reminders = engine.get_pending_reminders(days_ahead=60)
            
            assert len(reminders) >= 1
            r = reminders[0]
            assert r.pet_name == "Buddy"
            assert r.vaccine_name == "Rabies"
    
    def test_mark_sent(self, config, test_db):
        """Test marking a reminder as sent."""
        # Add a reminder
        conn = sqlite3.connect(str(test_db))
        cursor = conn.execute("""
            INSERT INTO reminders (pet_id, vaccine_id, reminder_type, due_date, status)
            VALUES (1, 1, 'due_soon', '2026-03-15', 'pending')
        """)
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        with ReminderEngine(config) as engine:
            result = engine.mark_sent(reminder_id)
            assert result is True
            
            # Verify using engine's connection
            cursor = engine.conn.execute(
                "SELECT status, sent_at FROM reminders WHERE id = ?",
                (reminder_id,)
            )
            row = cursor.fetchone()
            assert row["status"] == "sent"
            assert row["sent_at"] is not None
    
    def test_context_manager(self, config):
        """Test context manager cleanup."""
        engine = ReminderEngine(config)
        
        with engine as eng:
            assert eng.conn is not None
        
        # Connection should be closed after exiting
        assert engine._conn is None


class TestFormatReminderMessage:
    """Tests for reminder message formatting."""
    
    def test_format_due_soon(self):
        """Test formatting a due soon reminder."""
        reminder = Reminder(
            id=1,
            pet_id=1,
            vaccine_id=1,
            reminder_type=ReminderType.DUE_SOON,
            due_date=(datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
            status=ReminderStatus.PENDING,
            created_at=None,
            pet_name="Buddy",
            vaccine_name="Rabies"
        )
        
        msg = format_reminder_message(reminder)
        
        assert "Buddy" in msg
        assert "Rabies" in msg
        assert "Due in" in msg
        assert "⚠️" in msg
    
    def test_format_overdue(self):
        """Test formatting an overdue reminder."""
        reminder = Reminder(
            id=1,
            pet_id=1,
            vaccine_id=1,
            reminder_type=ReminderType.OVERDUE,
            due_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            status=ReminderStatus.PENDING,
            created_at=None,
            pet_name="Whiskers",
            vaccine_name="FVRCP"
        )
        
        msg = format_reminder_message(reminder)
        
        assert "Whiskers" in msg
        assert "Overdue" in msg
        assert "🚨" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
