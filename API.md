# PetVaxHK API Reference

Complete API reference for PetVaxHK - a local-first pet vaccine tracker for Hong Kong.

---

## Table of Contents

- [CLI Commands](#cli-commands)
- [Web Routes](#web-routes)
- [Python API](#python-api)
- [Data Models](#data-models)
- [Configuration](#configuration)

---

## CLI Commands

### Pet Management

```bash
# Add a new pet (interactive)
petvax pet add

# List all pets
petvax pet list

# Edit a pet
petvax pet edit

# Delete a pet
petvax pet delete
```

### Vaccine Management

```bash
# Add vaccination record (interactive)
petvax vaccine add

# List all vaccination records
petvax vaccine list

# Edit vaccination record
petvax vaccine edit

# Delete vaccination record
petvax vaccine delete
```

### Reminders

```bash
# Show upcoming reminders (default 30 days)
petvax reminder show
petvax reminder show -d 60

# Generate new reminders from vaccination records
petvax reminder generate

# List all reminders with optional filters
petvax reminder list
petvax reminder list -s pending
petvax reminder list -t due_soon

# Mark reminder as sent/completed
petvax reminder mark <id> sent|completed

# Cancel a reminder
petvax reminder cancel <id>

# Delete a reminder permanently
petvax reminder delete <id>
```

### Compliance

```bash
# Check compliance for all pets (brief)
petvax compliance

# Detailed compliance report
petvax compliance --detailed

# Check specific pet
petvax compliance --pet <id>
petvax compliance -p <id> --detailed
```

### Export

```bash
# Export to JSON
petvax export -f json
petvax export -f json -o my_pets.json

# Export to CSV
petvax export -f csv
petvax export -f csv -o output_dir/
```

---

## Web Routes

### Pages

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard with pets and upcoming reminders |
| `/pets` | GET | List all pets |
| `/pets/add` | GET, POST | Add new pet form |
| `/pets/<id>` | GET | View pet details with vaccination history |
| `/pets/<id>/edit` | GET, POST | Edit pet form |
| `/pets/<id>/delete` | POST | Delete pet |
| `/vaccines` | GET | List all vaccine types |
| `/vaccines/add` | GET, POST | Add new vaccine type |
| `/vaccines/<id>` | GET | View vaccine details |
| `/vaccines/<id>/edit` | GET, POST | Edit vaccine form |
| `/vaccines/<id>/delete` | POST | Delete vaccine |
| `/vaccinations/add` | GET, POST | Record new vaccination |
| `/vaccinations/<id>/edit` | GET, POST | Edit vaccination record |
| `/vaccinations/<id>/delete` | POST | Delete vaccination record |
| `/reminders` | GET | Reminders dashboard with stats |
| `/reminders/generate` | POST | Generate reminders |
| `/reminders/<id>/complete` | POST | Mark reminder completed |
| `/clinics` | GET | List vet clinics with search/filter |
| `/clinics/add` | GET, POST | Add new clinic |
| `/clinics/<id>` | GET | View clinic details |
| `/clinics/<id>/edit` | GET, POST | Edit clinic |
| `/clinics/<id>/delete` | POST | Delete clinic |
| `/compliance` | GET | Compliance dashboard |
| `/compliance/<id>` | GET | Detailed compliance for pet |
| `/settings` | GET | Settings page |
| `/settings/update` | POST | Update settings |
| `/about` | GET | About page |
| `/health` | GET | Health check endpoint |

### Query Parameters

- `/reminders?status=pending&type=due_soon` - Filter reminders
- `/clinics?q=search&district=Central` - Search and filter clinics

---

## Python API

### Core Modules

#### `app.core.rules` - HK Vaccination Rules Engine

```python
from app.core.rules import (
    # Enums
    RequirementStatus,
    ImportCountryGroup,
    Scenario,
    PetType,
    
    # Data Classes
    VaccinationRequirement,
    ComplianceResult,
    ImportRequirements,
    
    # Functions
    check_compliance,
    get_resident_requirements,
    get_import_requirements,
    determine_import_group,
    calculate_import_timeline,
    get_next_due_date,
    format_compliance_summary,
)
```

##### Enums

**`RequirementStatus`**
- `COMPLIANT` - Vaccination up to date
- `DUE_SOON` - Within 30 days of due date
- `OVERDUE` - Past due date
- `NOT_DONE` - Never administered
- `NOT_APPLICABLE` - Not required for this scenario

**`ImportCountryGroup`**
- `GROUP_I` - Rabies-free countries (no quarantine)
- `GROUP_II` - Rabies-controlled (no quarantine)
- `GROUP_IIIA` - Higher risk (30 days quarantine)
- `GROUP_IIIB` - Highest risk (120 days quarantine)
- `MAINLAND_CHINA` - Special arrangement (30 days)

**`PetType`**
- `DOG`
- `CAT`

**`Scenario`**
- `HK_RESIDENT` - Resident pet in Hong Kong
- `IMPORT` - Pet being imported to Hong Kong

##### Functions

```python
# Check compliance for a pet
result = check_compliance(
    pet_id=1,
    pet_name="Max",
    scenario=Scenario.HK_RESIDENT,
    pet_type=PetType.DOG,
    vaccinations=[
        {"vaccine_name": "Rabies", 
         "date_administered": datetime(2024, 6, 1), 
         "next_due_date": datetime(2027, 6, 1)}
    ],
    license_expiry_date=datetime(2027, 6, 1),
    microchip_date=datetime(2024, 5, 1)
)

print(result.is_compliant)  # True/False
print(result.overall_status)  # RequirementStatus

# Format compliance as text
print(format_compliance_summary(result))

# Get requirements for resident pet
requirements = get_resident_requirements(PetType.DOG, include_recommended=True)

# Get import requirements
import_req = get_import_requirements("Australia", PetType.DOG)
print(import_req.quarantine_days)  # 0
print(import_req.required_vaccines)  # ['Rabies', 'DHPP/DAPP', 'Microchip']

# Determine import group
group = determine_import_group("USA")  # ImportCountryGroup.GROUP_II

# Calculate import timeline
timeline = calculate_import_timeline(
    arrival_date=datetime(2026, 3, 15),
    import_group=ImportCountryGroup.GROUP_II
)
# Returns dict of action -> due date

# Calculate next due date
next_due = get_next_due_date(
    vaccine_name="Rabies",
    date_administered=datetime(2024, 6, 1),
    pet_type=PetType.DOG,
    scenario=Scenario.HK_RESIDENT
)
```

#### `app.core.dates` - Date Calculations

```python
from app.core.dates import (
    # Enums
    PetType,
    Scenario,
    ImportGroup,
    
    # Data Classes
    VaccinationSchedule,
    DateCalculationResult,
    
    # Functions
    calculate_rabies_due_date,
    calculate_dhpp_first_series,
    calculate_annual_booster_due,
    calculate_import_timing_requirements,
    calculate_license_renewal_due,
    calculate_compliance_status,
    format_days_until,
)
```

##### Functions

```python
# Rabies due date
due = calculate_rabies_due_date(
    last_vaccination_date=datetime(2024, 6, 1),
    is_boosters=True  # True for boosters, False for first vax
)
# Returns: datetime(2027, 6, 1) - 3 years later

# DHPP first series (puppy shots)
doses = calculate_dhpp_first_series(start_date=datetime(2024, 3, 1))
# Returns: [8-week, 12-week, 16-week] due dates

# Annual booster
due = calculate_annual_booster_due(
    last_booster_date=datetime(2024, 6, 1),
    vaccine_type="dhpp"
)
# Returns: datetime(2025, 6, 1)

# Import timing requirements
result = calculate_import_timing_requirements(
    arrival_date=datetime(2026, 3, 15),
    import_group=ImportGroup.GROUP_II
)
# Returns DateCalculationResult with:
# - rabies_vaccination_earliest/latest
# - rnatt_earliest/deadline
# - special_permit_earliest/deadline
# - health_certificate_earliest/latest
# - quarantine_days, quarantine_release

# License renewal
renewal_due = calculate_license_renewal_due(
    license_issue_date=datetime(2024, 6, 1)
)
# Returns: datetime(2027, 6, 1) - 3 years

# Full compliance status
status = calculate_compliance_status(
    pet_birth_date=datetime(2023, 1, 1),
    last_rabies_date=datetime(2024, 6, 1),
    last_dhpp_date=datetime(2024, 6, 1),
    license_issue_date=datetime(2024, 6, 1),
    scenario=Scenario.HK_RESIDENT
)
# Returns dict with status for rabies, license, dhpp

# Format days until
print(format_days_until(30))   # "Due in 30 days"
print(format_days_until(-5))  # "5 days overdue"
```

#### `app.core.reminders` - Reminder Engine

```python
from app.core.reminders import (
    # Enums
    ReminderType,
    ReminderStatus,
    
    # Data Classes
    Reminder,
    ReminderConfig,
    
    # Engine
    ReminderEngine,
    
    # Utilities
    format_reminder_message,
)
```

##### Classes

**`ReminderConfig`**
```python
config = ReminderConfig(
    db_path="outputs/pets.db",
    due_soon_days=30,        # Remind when within 30 days
    overdue_days=0,          # Remind when overdue
    upcoming_days=60,        # Future reminder lead time
    max_lookahead_days=90   # Max future reminder
)
```

**`ReminderEngine`**
```python
config = ReminderConfig(db_path="outputs/pets.db")

with ReminderEngine(config) as engine:
    # Generate reminders
    stats = engine.generate_reminders()
    # Returns: {'created': N, 'skipped': N, 'errors': N}
    
    # Get pending reminders
    reminders = engine.get_pending_reminders(days_ahead=30)
    # Returns: List[Reminder]
    
    # Mark as sent/completed
    engine.mark_sent(reminder_id)
    engine.mark_completed(reminder_id)
    
    # Cancel reminder
    engine.cancel_reminder(reminder_id)
```

**`Reminder` Data Class**
```python
@dataclass
class Reminder:
    id: Optional[int]
    pet_id: int
    vaccine_id: int
    reminder_type: ReminderType  # DUE_SOON, OVERDUE, UPCOMING
    due_date: str                # YYYY-MM-DD
    status: ReminderStatus       # PENDING, SENT, COMPLETED, CANCELLED
    created_at: Optional[str]
    pet_name: Optional[str]      # Join data
    vaccine_name: Optional[str]  # Join data
```

**`ReminderType`**
- `DUE_SOON` - Within configured days
- `OVERDUE` - Past due date
- `UPCOMING` - Future reminder

**`ReminderStatus`**
- `PENDING` - Not yet acted on
- `SENT` - Notification sent
- `COMPLETED` - Action taken (vaccination received)
- `CANCELLED` - Cancelled

#### `app.core.io` - Data Import/Export

```python
from app.core.io import (
    get_db_connection,
    get_db_path,
    init_db,
    export_json,
    export_csv,
    import_json,
    import_csv,
    backup_db,
    restore_db,
)
```

##### Functions

```python
# Database connection
conn = get_db_connection()
# Returns: sqlite3.Connection

db_path = get_db_path()
# Returns: Path to database

# Initialize database
init_db()
# Creates tables if they don't exist

# Export data
data = export_json()
# Returns: dict with all tables

files = export_csv()
# Returns: dict of {table_name: file_path}

# Import data
import_json(data, strategy="merge")  # merge, replace
import_csv("import.csv", table="pets")

# Backup/restore
backup_db("backup_2026-02-26.db")
restore_db("backup_2026-02-26.db")
```

---

## Data Models

### Database Schema

#### `pets` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Pet name |
| species | TEXT | 'dog' or 'cat' |
| breed | TEXT | Breed (optional) |
| date_of_birth | TEXT | DOB YYYY-MM-DD (optional) |
| color | TEXT | Color (optional) |
| microchip_id | TEXT | Microchip number (optional) |
| gender | TEXT | male/female/unknown |
| neutered | INTEGER | 0 or 1 |
| owner_name | TEXT | Owner name |
| owner_phone | TEXT | Phone (optional) |
| owner_email | TEXT | Email (optional) |
| notes | TEXT | Notes (optional) |
| created_at | TEXT | Timestamp |

#### `vaccines` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Vaccine name |
| code | TEXT | Short code |
| species | TEXT | dog/cat/both |
| description | TEXT | Description |
| is_mandatory | INTEGER | 0 or 1 |
| valid_months | INTEGER | Validity period |

#### `pet_vaccinations` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| pet_id | INTEGER | FK to pets |
| vaccine_id | INTEGER | FK to vaccines |
| date_administered | TEXT | Date given |
| next_due_date | TEXT | Next due date |
| batch_number | TEXT | Vaccine batch |
| vet_clinic_id | INTEGER | FK to vet_clinics |
| vet_name | TEXT | Vet name |
| vet_license | TEXT | Vet license |
| certificate_number | TEXT | Cert number |
| notes | TEXT | Notes |
| created_at | TEXT | Timestamp |

#### `vet_clinics` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Clinic name |
| address | TEXT | Address |
| phone | TEXT | Phone |
| email | TEXT | Email |
| district | TEXT | HK district |
| created_at | TEXT | Timestamp |

#### `reminders` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| pet_id | INTEGER | FK to pets |
| vaccine_id | INTEGER | FK to vaccines |
| reminder_type | TEXT | due_soon/overdue/upcoming |
| due_date | TEXT | Due date YYYY-MM-DD |
| status | TEXT | pending/sent/completed/cancelled |
| created_at | TEXT | Timestamp |
| sent_at | TEXT | When sent |

---

## Configuration

### Database Path

Default: `outputs/pets.db`

Set via environment variable or modify in `app/core/io.py`:

```python
DB_PATH = os.environ.get("PETVAX_DB_PATH", "outputs/pets.db")
```

### Web Server

Default: `http://localhost:5000`

Run with:
```bash
python run_web.py
# Or with custom host/port
python run_web.py --host 0.0.0.0 --port 8080
```

### Reminder Settings

Configure in `ReminderConfig`:

- `due_soon_days`: Days before due date to remind (default: 30)
- `overdue_days`: Days after due date to flag (default: 0)
- `upcoming_days`: Future reminder lead time (default: 60)
- `max_lookahead_days`: Maximum future reminder (default: 90)

---

## Error Handling

All functions raise appropriate exceptions:

- `ValueError` - Invalid input (invalid date format, invalid enum value)
- `sqlite3.Error` - Database errors
- `FileNotFoundError` - Missing files

Always wrap API calls in try/except:

```python
try:
    result = check_compliance(...)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Examples

### CLI: Add Pet and Vaccination

```bash
# Add a pet
$ petvax pet add
Pet name: Max
Species (dog/cat): dog
Breed (optional): Golden Retriever
Date of birth (YYYY-MM-DD, optional): 2023-01-15
Color (optional): Golden
Microchip ID (optional): 900123456789012
Gender (male/female/unknown, optional): male
Neutered (y/n): y
Owner name: John Smith
Owner phone (optional): 6123 4567
Owner email (optional): john@example.com
Notes (optional):

✓ Pet 'Max' added successfully! (ID: 1)

# Add vaccination
$ petvax vaccine add
Select a pet to add vaccination record for:
  [1] Max (dog)

Enter pet ID: 1

Adding vaccination for: Max (dog)
...
```

### Python: Check Compliance

```python
from datetime import datetime
from app.core.rules import (
    check_compliance, Scenario, PetType, 
    format_compliance_summary
)

result = check_compliance(
    pet_id=1,
    pet_name="Max",
    scenario=Scenario.HK_RESIDENT,
    pet_type=PetType.DOG,
    vaccinations=[
        {
            "vaccine_name": "Rabies",
            "date_administered": datetime(2024, 6, 1),
            "next_due_date": datetime(2027, 6, 1)
        },
        {
            "vaccine_name": "DHPP/DAPP",
            "date_administered": datetime(2024, 6, 1),
            "next_due_date": datetime(2025, 6, 1)
        }
    ]
)

print(format_compliance_summary(result))
```

### Python: Generate Reminders

```python
from app.core.reminders import ReminderEngine, ReminderConfig

config = ReminderConfig(db_path="outputs/pets.db")

with ReminderEngine(config) as engine:
    # Generate new reminders
    stats = engine.generate_reminders()
    print(f"Created: {stats['created']}, Skipped: {stats['skipped']}")
    
    # Get upcoming reminders
    reminders = engine.get_pending_reminders(days_ahead=30)
    for r in reminders:
        print(f"{r.pet_name}: {r.vaccine_name} due {r.due_date}")
```

---

## Support

- GitHub: https://github.com/petvax/petvaxhk
- Issues: https://github.com/petvax/petvaxhk/issues
- License: MIT
