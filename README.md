# PetVaxHK — Pet Vaccine Tracker for Hong Kong

A local-first desktop application for tracking pet vaccinations and compliance with Hong Kong AFCD regulations. Supports dogs and cats.

## Features

- **Pet Management** — Add, edit, delete pets (dogs/cats) with details like microchip ID, DOB, breed, owner info
- **Vaccine Tracking** — Record vaccinations with auto-calculated due dates
- **Smart Reminders** — Overdue alerts, due-soon notifications (30 days)
- **Compliance Checking** — Check compliance with HK AFCD regulations
- **Export** — JSON and CSV export formats
- **Web Interface** — User-friendly Flask web UI
- **Bilingual** — English and Traditional Chinese (EN/ZH)

## Installation

### Requirements

- Python 3.10+
- SQLite3

### Steps

```bash
# Clone the repo
git clone https://github.com/sqryxz/Petvaxtrax.git
cd Petvaxtrax

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[web]"

# Initialize database (first run)
python3 -m app.cli pet list
```

## Quick Start

```bash
# Add a pet
python3 -m app.cli pet add

# Add a vaccine record
python3 -m app.cli vaccine add

# Check compliance
python3 -m app.cli compliance

# Generate reminders
python3 -m app.cli reminder generate

# View reminders
python3 -m app.cli reminder show
```

## Command Line

### Pet Management

```bash
# List all pets
python3 -m app.cli pet list

# Add a pet
python3 -m app.cli pet add

# Edit a pet
python3 -m app.cli pet edit <pet_id>

# Delete a pet
python3 -m app.cli pet delete <pet_id>
```

### Vaccination Records

```bash
# List all vaccinations
python3 -m app.cli vaccine list

# Add a vaccination
python3 -m app.cli vaccine add

# Edit a vaccination
python3 -m app.cli vaccine edit <vaccine_id>

# Delete a vaccination
python3 -m app.cli vaccine delete <vaccine_id>
```

### Reminders

```bash
# Show upcoming reminders
python3 -m app.cli reminder show

# List all reminders
python3 -m app.cli reminder list

# Generate reminders
python3 -m app.cli reminder generate

# Mark reminder as done
python3 -m app.cli reminder mark <reminder_id>
```

### Compliance

```bash
# Basic compliance check
python3 -m app.cli compliance

# Detailed report
python3 -m app.cli compliance --detailed

# Check specific pet
python3 -m app.cli compliance --pet <pet_id>
```

### Export

```bash
# Export as JSON
python3 -m app.cli export --format json --output my_pets.json

# Export as CSV
python3 -m app.cli export --format csv --output my_pets.csv
```

## Web Application

Start the web server:

```bash
python3 run_web.py
```

Then open http://localhost:5000 in your browser.

### Web Features

- Dashboard with overview
- Pet management (CRUD)
- Vaccination management (CRUD)
- Reminders dashboard
- Vet clinic directory
- Compliance dashboard
- Settings (language, timezone)
- About page

## Hong Kong Vaccination Rules

### Dogs (Residents)

| Vaccine | First Dose | Booster |
|---------|-----------|---------|
| Rabies | After 3 months | Yearly |
| DHPP | From 6-8 weeks | Yearly |

- Dog license must be renewed yearly
- Rabies vaccine required for license renewal

### Import Requirements

- **Group I countries**: No quarantine
- **Group II countries**: 120 days quarantine
- **Group III countries**: 180 days quarantine
- Rabies vaccine must be given within 120 days before arrival

### Cats

| Vaccine | First Dose | Booster |
|---------|-----------|---------|
| Rabies | After 3 months | Yearly |
| FVRCP | From 6-8 weeks | Yearly |

- Import: Group I no quarantine, Group II/III require quarantine
- Rabies within 120 days before arrival

## Data Storage

- Database: `outputs/pets.db` (SQLite)
- Export files: `outputs/exports/`
- Research data: `outputs/research/`

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_cli.py

# With coverage
pytest --cov=app
```

## License

MIT License

## Support

For issues, please open a GitHub issue.
