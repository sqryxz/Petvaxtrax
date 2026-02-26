"""
Date calculation utilities for PetVaxHK.

Provides date calculations for vaccination schedules, import requirements,
and compliance tracking based on HK AFCD regulations.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class PetType(Enum):
    DOG = "dog"
    CAT = "cat"


class Scenario(Enum):
    HK_RESIDENT = "hk_resident"
    IMPORT = "import"


class ImportGroup(Enum):
    """AFCD import groups for rabies risk categorization."""
    GROUP_I = "Group_I"        # Low risk - no quarantine
    GROUP_II = "Group_II"      # Moderate risk - 4 months quarantine
    GROUP_IIIA = "Group_IIIA"  # Higher risk - 120 days
    GROUP_IIIB = "Group_IIIB"  # Highest risk - 120 days
    MAINLAND_CHINA = "Mainland_China"


@dataclass
class VaccinationSchedule:
    """Represents a vaccination schedule with due dates."""
    vaccine_name: str
    doses: list[datetime]
    next_due: Optional[datetime]
    frequency_days: Optional[int]  # None for one-time, otherwise recurrence interval


@dataclass
class DateCalculationResult:
    """Result of a date calculation operation."""
    success: bool
    dates: dict[str, Optional[datetime]]
    errors: list[str]
    warnings: list[str]


def calculate_rabies_due_date(
    last_vaccination_date: datetime,
    is_boosters: bool = True
) -> datetime:
    """
    Calculate the due date for rabies vaccination.
    
    For resident dogs in HK:
    - First vaccination: due at 5 months of age (or 30 days after if older)
    - Boosters: every 3 years (approximately 1095 days, accounting for leap years)
    
    Args:
        last_vaccination_date: Date of last rabies vaccination
        is_boosters: Whether this is a booster (True) or first vaccination (False)
    
    Returns:
        Due date for next vaccination
    """
    if is_boosters:
        # Booster due every 3 years - use replace to handle leap years correctly
        return last_vaccination_date.replace(
            year=last_vaccination_date.year + 3
        )
    else:
        # First vaccination - due at 5 months for license
        return last_vaccination_date + timedelta(days=30)


def calculate_dhpp_first_series(start_date: datetime) -> list[datetime]:
    """
    Calculate DHPPi (core dog vaccine) first series due dates.
    
    Standard protocol: 3 vaccines at 8, 12, and 16 weeks of age.
    
    Args:
        start_date: Date of first vaccination (usually at ~8 weeks)
    
    Returns:
        List of due dates for each dose
    """
    doses = []
    # 8 weeks = 56 days, 12 weeks = 84 days, 16 weeks = 112 days
    for weeks in [8, 12, 16]:
        doses.append(start_date + timedelta(weeks=weeks))
    return doses


def calculate_annual_booster_due(
    last_booster_date: datetime,
    vaccine_type: str = "dhpp"
) -> datetime:
    """
    Calculate due date for annual booster vaccination.
    
    Args:
        last_booster_date: Date of last booster
        vaccine_type: Type of vaccine (dhpp, leptospirosis, bordetella, etc.)
    
    Returns:
        Due date for next booster (exactly 1 year)
    """
    # Standard annual booster - use replace for exact year
    return last_booster_date.replace(
        year=last_booster_date.year + 1
    )


def calculate_import_timing_requirements(
    arrival_date: datetime,
    import_group: ImportGroup
) -> DateCalculationResult:
    """
    Calculate all relevant timing requirements for importing a pet.
    
    Based on AFCD requirements for each import group.
    
    Args:
        arrival_date: Planned arrival date in Hong Kong
        import_group: AFCD import group (risk category)
    
    Returns:
        DateCalculationResult with all relevant dates
    """
    result = DateCalculationResult(
        success=True,
        dates={},
        errors=[],
        warnings=[]
    )
    
    # Rabies vaccination must be given 30 days to 12 months before arrival
    result.dates["rabies_vaccination_earliest"] = arrival_date - timedelta(days=365)
    result.dates["rabies_vaccination_latest"] = arrival_date - timedelta(days=30)
    
    # RNATT (Rabies Neutralizing Antibody Titre Test) - must be done before vaccination
    # Typically needs to be done at least 30 days after vaccination
    result.dates["rnatt_earliest"] = arrival_date - timedelta(days=395)  # 30 days after earliest vax
    result.dates["rnatt_deadline"] = arrival_date - timedelta(days=60)  # Allow time for results
    
    # Special Permit application - recommend at least 2 months before
    result.dates["special_permit_earliest"] = arrival_date - timedelta(days=60)
    result.dates["special_permit_deadline"] = arrival_date - timedelta(days=14)
    
    # Health certificate - must be issued within 14 days of travel
    result.dates["health_certificate_earliest"] = arrival_date - timedelta(days=14)
    result.dates["health_certificate_latest"] = arrival_date - timedelta(days=1)
    
    # Quarantine periods by group
    quarantine_days = {
        ImportGroup.GROUP_I: 0,
        ImportGroup.GROUP_II: 120,  # 4 months
        ImportGroup.GROUP_IIIA: 120,
        ImportGroup.GROUP_IIIB: 120,
        ImportGroup.MAINLAND_CHINA: 180,  # 6 months
    }
    
    result.dates["quarantine_days"] = quarantine_days.get(import_group, 0)
    
    if quarantine_days.get(import_group, 0) > 0:
        result.dates["quarantine_release"] = arrival_date + timedelta(days=quarantine_days[import_group])
    
    return result


def calculate_license_renewal_due(license_issue_date: datetime) -> datetime:
    """
    Calculate dog license renewal due date.
    
    HK dog licenses are valid for 3 years and must be renewed with rabies vaccination.
    
    Args:
        license_issue_date: Date when license was issued/renewed
    
    Returns:
        Renewal due date
    """
    # 3 years - use replace to handle leap years correctly
    return license_issue_date.replace(
        year=license_issue_date.year + 3
    )


def calculate_compliance_status(
    pet_birth_date: Optional[datetime],
    last_rabies_date: Optional[datetime],
    last_dhpp_date: Optional[datetime],
    license_issue_date: Optional[datetime],
    scenario: Scenario = Scenario.HK_RESIDENT
) -> dict[str, dict]:
    """
    Calculate overall compliance status for a pet.
    
    Args:
        pet_birth_date: Pet's date of birth
        last_rabies_date: Date of last rabies vaccination
        last_dhpp_date: Date of last DHPP vaccination
        license_issue_date: Date of license issue/renewal
        scenario: Whether pet is resident or being imported
    
    Returns:
        Dict with compliance status for each requirement
    """
    now = datetime.now()
    status = {}
    
    # Rabies compliance
    if last_rabies_date:
        rabies_due = calculate_rabies_due_date(last_rabies_date)
        days_until_due = (rabies_due - now).days
        status["rabies"] = {
            "compliant": days_until_due > 0,
            "last_vaccination": last_rabies_date.isoformat(),
            "next_due": rabies_due.isoformat(),
            "days_until_due": days_until_due,
            "status": "ok" if days_until_due > 30 else ("due_soon" if days_until_due > 0 else "overdue")
        }
    else:
        status["rabies"] = {
            "compliant": False,
            "last_vaccination": None,
            "next_due": None,
            "days_until_due": None,
            "status": "not_done"
        }
    
    # License compliance
    if license_issue_date:
        license_due = calculate_license_renewal_due(license_issue_date)
        days_until_license_due = (license_due - now).days
        status["license"] = {
            "compliant": days_until_license_due > 0,
            "last_renewal": license_issue_date.isoformat(),
            "next_due": license_due.isoformat(),
            "days_until_due": days_until_license_due,
            "status": "ok" if days_until_license_due > 60 else ("due_soon" if days_until_license_due > 0 else "overdue")
        }
    else:
        status["license"] = {
            "compliant": False,
            "last_renewal": None,
            "next_due": None,
            "days_until_due": None,
            "status": "not_done"
        }
    
    # DHPP compliance (for dogs)
    if last_dhpp_date:
        dhpp_due = calculate_annual_booster_due(last_dhpp_date)
        days_until_dhpp = (dhpp_due - now).days
        status["dhpp"] = {
            "compliant": days_until_dhpp > 0,
            "last_vaccination": last_dhpp_date.isoformat(),
            "next_due": dhpp_due.isoformat(),
            "days_until_due": days_until_dhpp,
            "status": "ok" if days_until_dhpp > 30 else ("due_soon" if days_until_dhpp > 0 else "overdue")
        }
    else:
        status["dhpp"] = {
            "compliant": False,
            "last_vaccination": None,
            "next_due": None,
            "days_until_due": None,
            "status": "not_done"
        }
    
    return status


def format_days_until(days: int) -> str:
    """Format days until a date in human-readable form."""
    if days < 0:
        return f"{-days} days overdue"
    elif days == 0:
        return "Due today"
    elif days == 1:
        return "Due tomorrow"
    elif days < 30:
        return f"Due in {days} days"
    elif days < 60:
        return "Due in 1 month"
    elif days < 365:
        months = days // 30
        return f"Due in {months} months"
    else:
        years = days // 365
        return f"Due in {years} year{'s' if years > 1 else ''}"


if __name__ == "__main__":
    # Simple test/demo
    now = datetime.now()
    
    print("=== PetVaxHK Date Utilities Demo ===\n")
    
    # Example: Resident dog compliance check
    print("Resident Dog Compliance:")
    status = calculate_compliance_status(
        pet_birth_date=now - timedelta(days=400),
        last_rabies_date=now - timedelta(days=400),
        last_dhpp_date=now - timedelta(days=300),
        license_issue_date=now - timedelta(days=400),
    )
    for req, data in status.items():
        print(f"  {req.upper()}: {data['status']}")
        if data.get('days_until_due') is not None:
            print(f"    {format_days_until(data['days_until_due'])}")
    
    print("\nImport Timing (Group II):")
    result = calculate_import_timing_requirements(
        arrival_date=now + timedelta(days=180),
        import_group=ImportGroup.GROUP_II
    )
    for key, date in result.dates.items():
        if isinstance(date, datetime):
            print(f"  {key}: {date.strftime('%Y-%m-%d')}")
        else:
            print(f"  {key}: {date}")
