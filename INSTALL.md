# PetVaxHK Installation & Setup Guide

This guide provides detailed instructions for installing and setting up PetVaxHK.

## Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | 3.10+ | Required |
| SQLite | 3.x | Built into Python |
| pip | Latest | For package installation |
| Git | Any recent | For cloning repository |

### Supported Operating Systems

- macOS 12+ (Apple Silicon & Intel)
- Linux (Ubuntu 20.04+, Debian 11+)
- Windows 10/11 (via WSL2 recommended)

---

## Installation Methods

### Method 1: Fresh Clone (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd petvax

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate
# Windows (CMD):
venv\Scripts\activate.bat

# Install in development mode
pip install -e ".[web]"

# Verify installation
python3 -m app.cli --help
```

### Method 2: Existing Installation Update

```bash
# Navigate to existing installation
cd petvax

# Activate virtual environment
source venv/bin/activate

# Pull latest changes
git pull origin main

# Reinstall dependencies
pip install -e ".[web]"

# Run tests to verify
pytest
```

---

## Initial Setup

### 1. Database Initialization

The database is created automatically on first run:

```bash
python3 -m app.cli pet list
# Output: No pets found. Database initialized.
```

Database location: `outputs/pets.db`

### 2. Verify Research Data

For compliance checks, ensure research data exists:

```bash
ls -la outputs/research/
# Should contain:
# - hk_dog_vaccination_requirements.json
# - hk_cat_vaccination_requirements.json
```

If missing, run:
```bash
python3 -m app.cli compliance --detailed
# This will generate the research files
```

---

## Configuration

### Environment Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `PETVAX_DB_PATH` | `outputs/pets.db` | Database file path |
| `PETVAX_LOG_LEVEL` | `INFO` | Logging level |
| `PETVAX_WEB_HOST` | `127.0.0.1` | Web server host |
| `PETVAX_WEB_PORT` | `5000` | Web server port |

### Configuration File

Create `petvax/config.json` for persistent settings:

```json
{
  "language": "en",
  "timezone": "Asia/Hong_Kong",
  "date_format": "%Y-%m-%d",
  "reminder_days_before": 30,
  "db_path": "outputs/pets.db"
}
```

---

## CLI Usage

### Quick Reference

```bash
# Pet management
python3 -m app.cli pet list
python3 -m app.cli pet add
python3 -m app.cli pet edit <id>
python3 -m app.cli pet delete <id>

# Vaccine management  
python3 -m app.cli vaccine list
python3 -m app.cli vaccine add
python3 -m app.cli vaccine edit <id>
python3 -m app.cli vaccine delete <id>

# Reminders
python3 -m app.cli reminder show
python3 -m app.cli reminder generate

# Compliance
python3 -m app.cli compliance --detailed

# Export
python3 -m app.cli export --format json --output backup.json
```

### Getting Help

```bash
# General help
python3 -m app.cli --help

# Command-specific help
python3 -m app.cli pet --help
python3 -m app.cli vaccine --help
python3 -m app.cli reminder --help
```

---

## Web Application

### Starting the Web Server

```bash
# Using the runner script
python3 run_web.py

# Or directly with Flask
export FLASK_APP=app
python3 -m flask run --host=127.0.0.1 --port=5000
```

### Accessing the Web UI

Open browser to: **http://127.0.0.1:5000**

### Web Features

- Dashboard with pet & reminder overview
- Full CRUD for pets and vaccines
- Reminder management
- Vet clinic directory
- Compliance dashboard
- Settings (language, timezone, notifications)
- Data import/export

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'petvax'"

**Solution:** Install the package in development mode
```bash
pip install -e ".[web]"
```

#### 2. "Database locked" error

**Solution:** Close any other processes accessing the database
```bash
# Check for processes
lsof outputs/pets.db
# Or on Linux
fuser outputs/pets.db
```

#### 3. "SQLite protocol error"

**Solution:** Ensure SQLite3 is properly installed
```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

#### 4. Web server won't start (port in use)

**Solution:** Use a different port
```bash
python3 run_web.py --port=5001
# Or
export PETVAX_WEB_PORT=5001
python3 run_web.py
```

#### 5. Import errors with optional dependencies

**Solution:** Reinstall with web extras
```bash
pip uninstall petvax
pip install -e ".[web]"
```

---

## Development Setup

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest app/tests/test_cli.py

# With coverage
pytest --cov=app --cov-report=term-missing
```

### Code Structure

```
petvax/
├── app/
│   ├── core/          # Business logic
│   │   ├── dates.py   # Date calculations
│   │   ├── rules.py   # HK vaccination rules
│   │   ├── reminders.py
│   │   └── io.py      # Import/export
│   ├── cli.py         # CLI entry point
│   ├── routes.py      # Flask routes
│   ├── models.py      # SQLAlchemy models
│   └── tests/         # Test suite
├── inputs/
│   ├── i18n/          # Language files
│   └── seeds/         # Seed data
├── outputs/
│   ├── research/      # HK vaccination research
│   └── pets.db        # SQLite database
└── run_web.py         # Web server launcher
```

### Adding New Features

1. Add core logic in `app/core/`
2. Add CLI commands in `app/cli.py`
3. Add web routes in `app/routes.py`
4. Add tests in `app/tests/`
5. Update documentation

---

## Data Management

### Backup

```bash
# JSON export (recommended for full backup)
python3 -m app.cli export --format json --output backup_$(date +%Y%m%d).json

# CSV export
python3 -m app.cli export --format csv --output backup_$(date +%Y%m%d)/
```

### Restore

```bash
# Import from JSON
python3 -m app.cli import --format json --input backup.json
```

### Reset Database

```bash
# Warning: This deletes all data!
rm outputs/pets.db
python3 -m app.cli pet list  # Reinitializes database
```

---

## Upgrading

### From Previous Version

```bash
# Backup first
python3 -m app.cli export --format json --output pre_upgrade_backup.json

# Pull latest
git pull origin main

# Run migrations if any
# (Check release notes for migration instructions)

# Reinstall
pip install -e ".[web]"

# Verify
pytest
python3 -m app.cli --help
```

---

## Support

- Check `README.md` for usage documentation
- Review `outputs/research/` for HK vaccination rules
- Run `python3 -m app.cli compliance --detailed` for pet compliance status
