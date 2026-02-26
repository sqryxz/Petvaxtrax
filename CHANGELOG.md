# PetVaxHK Release Notes

## Version 1.0.0 (2026-02-26)

### 🎉 Initial Release

PetVaxHK is a local-first pet vaccine tracker designed specifically for Hong Kong pet owners. It helps you track vaccinations, manage compliance with Hong Kong regulations, and never miss a vaccine due date.

### ✨ Features

#### Core Functionality
- **Pet Management**: Add, edit, delete, and view pets (dogs and cats)
- **Vaccine Tracking**: Track vaccination history with automatic due date calculations
- **Reminder System**: Automatic reminders for upcoming and overdue vaccinations
- **Compliance Checking**: Verify your pet meets HK vaccination requirements
- **Vet Clinic Directory**: Store and manage your vet clinic information

#### Hong Kong Specific
- Full support for HK dog vaccination requirements (AFCD)
- Full support for HK cat vaccination requirements
- Rabies vaccination rules and timelines
- Import/Quarantine requirement guidance
- Traditional Chinese (中文) interface support

#### Data Management
- **JSON Export/Import**: Backup and restore your data
- **CSV Export**: Export data for spreadsheets
- **Database Backup/Restore**: Full database backup functionality

#### Multi-Platform
- **Command-Line Interface (CLI)**: Full-featured terminal application
- **Web Application**: User-friendly web interface with Flask

### 📋 Requirements Covered

#### Dogs (Resident)
- Rabies vaccination (every 3 years after initial)
- DHPP / Distemper (annual booster)
- Kennel Cough (annual, optional but recommended)

#### Dogs (Import)
- Rabies antibody test (FAVN test)
- 120-day wait period from blood draw
- Microchip required before vaccination

#### Cats (Resident)
- FVRCP (Feline Viral Rhinotracheitis, Calicivirus, Panleukopenia)
- FeLV (Feline Leukemia, recommended)

#### Cats (Import)
- Rabies vaccination
- Microchip
- Quarantine requirements vary by country group

### 🛠️ Technical Details

- **Database**: SQLite (local-first, no cloud required)
- **Python**: 3.10+
- **Dependencies**: Flask, SQLAlchemy, click, pytest
- **Tests**: 123+ unit and integration tests

### 📦 Distribution

- CLI tool for power users
- Web app for visual interface
- Sample data included for demo/testing
- Comprehensive documentation (README, INSTALL, API, FAQ)

### 🔧 Installation

See `INSTALL.md` for detailed installation instructions.

### 📚 Documentation

- `README.md` - User guide
- `INSTALL.md` - Installation guide
- `API.md` - API reference
- `FAQ.md` - Troubleshooting
- `CHANGELOG.md` - This file

---

*For questions or support, please refer to the documentation or contact your veterinarian.*
