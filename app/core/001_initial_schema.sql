-- PetVaxHK SQLite Schema Migration v1
-- Created: 2026-02-26
-- Purpose: Pet vaccine tracking database for Hong Kong

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- PETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT NOT NULL CHECK(species IN ('dog', 'cat')),
    breed TEXT,
    date_of_birth TEXT,  -- ISO 8601 format: YYYY-MM-DD
    color TEXT,
    microchip_id TEXT UNIQUE,
    gender TEXT CHECK(gender IN ('male', 'female', 'unknown')),
    neutered INTEGER DEFAULT 0,
    owner_name TEXT NOT NULL,
    owner_phone TEXT,
    owner_email TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Index for looking up pets by microchip
CREATE INDEX IF NOT EXISTS idx_pets_microchip ON pets(microchip_id);

-- Index for looking up pets by species
CREATE INDEX IF NOT EXISTS idx_pets_species ON pets(species);

-- ============================================================================
-- VACCINES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS vaccines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT NOT NULL CHECK(species IN ('dog', 'cat', 'both')),
    description TEXT,
    is_mandatory INTEGER DEFAULT 0,
    notes TEXT
);

-- Insert default vaccines for Hong Kong
-- Dogs
INSERT OR IGNORE INTO vaccines (id, name, species, description, is_mandatory) VALUES
(1, 'Rabies', 'dog', 'Required for all dogs in Hong Kong. First vaccination at 3 months, booster within 30 days, then every 3 years.', 1),
(2, 'DHPP/DAPP', 'dog', 'Distemper, Hepatitis, Parainfluenza, Parvovirus. Core vaccine for dogs.', 1),
(3, 'Bordetella', 'dog', 'Kennel cough. Required for dogs in boarding facilities.', 0),
(4, 'Leptospirosis', 'dog', 'Leptospira bacteria vaccine. Recommended for dogs in Hong Kong.', 0),
(5, 'Canine Influenza', 'dog', 'Dog flu vaccine. Recommended for social dogs.', 0);

-- Cats
INSERT OR IGNORE INTO vaccines (id, name, species, description, is_mandatory) VALUES
(6, 'Rabies', 'cat', 'Required for cats in Hong Kong. First vaccination at 3 months.', 1),
(7, 'FVRCP', 'cat', 'Feline Viral Rhinotracheitis, Calicivirus, Panleukopenia. Core vaccine for cats.', 1),
(8, 'FeLV', 'cat', 'Feline Leukemia Virus. Recommended for outdoor cats.', 0);

-- ============================================================================
-- PET VACCINATIONS (records of vaccines given to pets)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pet_vaccinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    vaccine_id INTEGER NOT NULL,
    date_administered TEXT NOT NULL,  -- ISO 8601: YYYY-MM-DD
    next_due_date TEXT,  -- ISO 8601: YYYY-MM-DD
    batch_number TEXT,
    vet_clinic_id INTEGER,
    vet_name TEXT,
    vet_license TEXT,
    certificate_number TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id),
    FOREIGN KEY (vet_clinic_id) REFERENCES vet_clinics(id)
);

-- Index for pet vaccination history
CREATE INDEX IF NOT EXISTS idx_pet_vacc_pet ON pet_vaccinations(pet_id);
CREATE INDEX IF NOT EXISTS idx_pet_vacc_due ON pet_vaccinations(next_due_date);

-- ============================================================================
-- VET CLINICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS vet_clinics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    district TEXT,  -- HK district (Central & Western, Yau Tsim Mong, etc.)
    phone TEXT,
    email TEXT,
    opening_hours TEXT,
    is_24hr INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Index for searching by district
CREATE INDEX IF NOT EXISTS idx_vets_district ON vet_clinics(district);

-- ============================================================================
-- REMINDERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    vaccine_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL CHECK(reminder_type IN ('due_soon', 'overdue', 'upcoming')),
    due_date TEXT NOT NULL,
    sent_at TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'cancelled', 'completed')),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id)
);

-- Index for finding pending reminders
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_date);

-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES (1, 'Initial schema with pets, vaccines, pet_vaccinations, vet_clinics, reminders');

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Pet vaccination status summary
CREATE VIEW IF NOT EXISTS v_pet_vaccination_summary AS
SELECT 
    p.id as pet_id,
    p.name as pet_name,
    p.species,
    v.id as vaccine_id,
    v.name as vaccine_name,
    v.is_mandatory,
    pv.date_administered,
    pv.next_due_date,
    CASE 
        WHEN pv.next_due_date IS NULL THEN 'unknown'
        WHEN pv.next_due_date < date('now') THEN 'overdue'
        WHEN pv.next_due_date <= date('now', '+30 days') THEN 'due_soon'
        ELSE 'up_to_date'
    END as status
FROM pets p
CROSS JOIN vaccines v
LEFT JOIN pet_vaccinations pv ON p.id = pv.pet_id AND v.id = pv.vaccine_id
WHERE v.species = p.species OR v.species = 'both';

-- View: Upcoming reminders
CREATE VIEW IF NOT EXISTS v_upcoming_reminders AS
SELECT 
    r.id as reminder_id,
    p.name as pet_name,
    p.species,
    v.name as vaccine_name,
    r.due_date,
    r.status,
    r.reminder_type
FROM reminders r
JOIN pets p ON r.pet_id = p.id
JOIN vaccines v ON r.vaccine_id = v.id
WHERE r.status = 'pending'
ORDER BY r.due_date;

-- Trigger: Update updated_at timestamp on pets
CREATE TRIGGER IF NOT EXISTS update_pets_timestamp 
AFTER UPDATE ON pets 
BEGIN 
    UPDATE pets SET updated_at = datetime('now') WHERE id = NEW.id; 
END;
