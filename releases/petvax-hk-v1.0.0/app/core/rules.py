"""
HK Vaccination Rules Engine for PetVaxHK.

Implements AFCD (Agriculture, Fisheries and Conservation Department) regulations
for Hong Kong pet vaccination requirements. Supports both resident and import scenarios.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from .dates import ImportGroup, PetType, Scenario


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class RequirementStatus(Enum):
    """Compliance status for a vaccination requirement."""
    COMPLIANT = "compliant"
    DUE_SOON = "due_soon"      # Within 30 days
    OVERDUE = "overdue"
    NOT_DONE = "not_done"
    NOT_APPLICABLE = "not_applicable"


class ImportCountryGroup(Enum):
    """AFCD country/region groups for import requirements."""
    GROUP_I = "Group_I"           # Rabies-free, no quarantine
    GROUP_II = "Group_II"         # Rabies-controlled, no quarantine
    GROUP_IIIA = "Group_IIIA"     # Rabies-infected (30 days quarantine)
    GROUP_IIIB = "Group_IIIB"     # Other countries (120 days quarantine)
    MAINLAND_CHINA = "Mainland_China"  # 30 days quarantine (updated June 2025)


@dataclass
class VaccinationRequirement:
    """A single vaccination requirement."""
    vaccine_name: str
    is_mandatory: bool
    status: RequirementStatus
    last_administered: Optional[datetime] = None
    next_due: Optional[datetime] = None
    days_until_due: Optional[int] = None
    notes: str = ""
    frequency_days: Optional[int] = None  # None = one-time, otherwise recurrence


@dataclass
class ComplianceResult:
    """Overall compliance check result for a pet."""
    pet_id: int
    pet_name: str
    scenario: Scenario
    is_compliant: bool
    overall_status: RequirementStatus
    requirements: list[VaccinationRequirement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    import_group: Optional[ImportCountryGroup] = None
    quarantine_days: Optional[int] = None


@dataclass
class ImportRequirements:
    """Import requirements for bringing a pet into Hong Kong."""
    import_group: ImportCountryGroup
    quarantine_days: int
    rabies_required: bool
    rabies_titer_required: bool
    microchip_required: bool
    import_permit_required: bool
    health_certificate_required: bool
    residency_months: Optional[int] = None
    rabies_timing_earliest_days: int = 30
    rabies_timing_latest_days: int = 365
    required_vaccines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ============================================================================
# RULE DEFINITIONS
# ============================================================================

# Resident Dog Requirements (HK)
RESIDENT_DOG_MANDATORY_VACCINES = [
    {"name": "Rabies", "frequency_days": 1095, "notes": "Every 3 years with license renewal"},  # 3 years
    {"name": "Microchip", "frequency_days": None, "notes": "Required before rabies vaccination"},
]

RESIDENT_DOG_RECOMMENDED_VACCINES = [
    {"name": "DHPP/DAPP", "frequency_days": 365, "notes": "Annual booster recommended"},
    {"name": "Leptospirosis", "frequency_days": 365, "notes": "Annual booster recommended"},
    {"name": "Bordetella", "frequency_days": 180, "notes": "Every 6-12 months for social dogs"},
]

# Resident Cat Requirements (HK)
RESIDENT_CAT_MANDATORY_VACCINES = [
    # Note: No mandatory vaccination for resident cats in HK under AFCD
]

RESIDENT_CAT_RECOMMENDED_VACCINES = [
    {"name": "FVRCP", "frequency_days": 365, "notes": "Annual booster recommended"},
    {"name": "FeLV", "frequency_days": 365, "notes": "Recommended for outdoor cats"},
    {"name": "Rabies", "frequency_days": 365, "notes": "Recommended, especially for outdoor cats"},
]

# Import group definitions
IMPORT_GROUP_COUNTRY_MAP = {
    # Group I - Rabies-free countries
    ImportCountryGroup.GROUP_I: {
        "countries": ["Australia", "Fiji", "Hawaii", "Ireland", "Japan", "New Zealand", "United Kingdom"],
        "quarantine_days": 0,
        "rabies_required": False,
        "rabies_titer_required": False,
        "residency_months": 6,
    },
    # Group II - Rabies-controlled countries
    ImportCountryGroup.GROUP_II: {
        "countries": ["Austria", "Bahamas", "Bahrain", "Belgium", "Bermuda", "Canada", "Cyprus", 
                      "Denmark", "France", "Germany", "Iceland", "Italy", "Luxembourg", "Malta",
                      "Netherlands", "Norway", "Singapore", "South Korea", "Spain", "Sweden",
                      "Switzerland", "Taiwan", "USA"],
        "quarantine_days": 0,
        "rabies_required": True,
        "rabies_titer_required": False,
        "residency_months": 4,
    },
    # Group IIIA - Rabies-infected (includes Mainland China)
    ImportCountryGroup.GROUP_IIIA: {
        "countries": ["Mainland China", "Hungary", "Lithuania", "Macao SAR", "Malaysia", "Thailand"],
        "quarantine_days": 30,
        "rabies_required": True,
        "rabies_titer_required": True,
        "residency_months": 4,
    },
    # Group IIIB - Other countries
    ImportCountryGroup.GROUP_IIIB: {
        "countries": [],  # All other countries
        "quarantine_days": 120,
        "rabies_required": True,
        "rabies_titer_required": True,
        "residency_months": None,
    },
    # Mainland China (special arrangement)
    ImportCountryGroup.MAINLAND_CHINA: {
        "countries": ["China", "Mainland China"],
        "quarantine_days": 30,
        "rabies_required": True,
        "rabies_titer_required": True,
        "residency_months": 4,
    },
}


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_resident_requirements(
    pet_type: PetType,
    include_recommended: bool = True
) -> list[dict]:
    """
    Get vaccination requirements for resident pets in Hong Kong.
    
    Args:
        pet_type: Dog or cat
        include_recommended: Whether to include recommended (non-mandatory) vaccines
    
    Returns:
        List of vaccine requirement dicts
    """
    if pet_type == PetType.DOG:
        reqs = RESIDENT_DOG_MANDATORY_VACCINES.copy()
        if include_recommended:
            reqs.extend(RESIDENT_DOG_RECOMMENDED_VACCINES)
    else:  # CAT
        reqs = []
        if include_recommended:
            reqs.extend(RESIDENT_CAT_RECOMMENDED_VACCINES)
    
    return reqs


def determine_import_group(country: str) -> ImportCountryGroup:
    """
    Determine AFCD import group for a given country/region.
    
    Args:
        country: Country name
    
    Returns:
        ImportCountryGroup enum value
    """
    country_lower = country.lower()
    
    # Check special cases first
    if country_lower in ["china", "mainland china", "prc"]:
        return ImportCountryGroup.MAINLAND_CHINA
    
    # Check each group
    for group, info in IMPORT_GROUP_COUNTRY_MAP.items():
        for c in info["countries"]:
            if country_lower == c.lower():
                return group
    
    # Default to Group IIIB (highest risk)
    return ImportCountryGroup.GROUP_IIIB


def get_import_requirements(
    country: str,
    pet_type: PetType
) -> ImportRequirements:
    """
    Get import requirements for a pet from a specific country.
    
    Args:
        country: Origin country
        pet_type: Dog or cat
    
    Returns:
        ImportRequirements object with all needed info
    """
    group = determine_import_group(country)
    group_info = IMPORT_GROUP_COUNTRY_MAP[group]
    
    # Build required vaccines list
    required_vaccines = []
    if group_info["rabies_required"]:
        required_vaccines.append("Rabies")
    
    if pet_type == PetType.DOG:
        required_vaccines.extend(["DHPP/DAPP", "Microchip"])
    else:  # CAT
        required_vaccines.extend(["FVRCP", "Feline Panleukopenia"])
        if group_info["rabies_required"]:
            required_vaccines.append("Rabies")
    
    # Build notes
    notes = []
    if group_info["quarantine_days"] > 0:
        notes.append(f"Quarantine required: {group_info['quarantine_days']} days at owner expense")
    if group_info["rabies_titer_required"]:
        notes.append("RNATT (Rabies Neutralising Antibody Titre Test) required, titer ≥ 0.5 IU/ml")
    if group_info["residency_months"]:
        notes.append(f"Pet must have resided in origin country for {group_info['residency_months']} months")
    
    return ImportRequirements(
        import_group=group,
        quarantine_days=group_info["quarantine_days"],
        rabies_required=group_info["rabies_required"],
        rabies_titer_required=group_info["rabies_titer_required"],
        microchip_required=True,
        import_permit_required=True,
        health_certificate_required=True,
        residency_months=group_info["residency_months"],
        required_vaccines=required_vaccines,
        notes=notes
    )


def calculate_import_timeline(
    arrival_date: datetime,
    import_group: ImportCountryGroup
) -> dict[str, datetime]:
    """
    Calculate timeline for import preparation.
    
    Args:
        arrival_date: Planned arrival date in Hong Kong
        import_group: AFCD import group
    
    Returns:
        Dict of action name -> due date
    """
    timeline = {}
    
    # Rabies vaccination: 30 days to 12 months before arrival
    timeline["rabies_vaccination_earliest"] = arrival_date - timedelta(days=365)
    timeline["rabies_vaccination_latest"] = arrival_date - timedelta(days=30)
    
    # RNATT (if required): at least 30 days after rabies vaccination
    timeline["rnatt_earliest"] = timeline["rabies_vaccination_earliest"] + timedelta(days=30)
    timeline["rnatt_deadline"] = arrival_date - timedelta(days=60)
    
    # Import permit: at least 3 working days before arrival
    timeline["permit_application_deadline"] = arrival_date - timedelta(days=14)
    
    # Health certificate: within 14 days of travel
    timeline["health_certificate_earliest"] = arrival_date - timedelta(days=14)
    timeline["health_certificate_latest"] = arrival_date - timedelta(days=1)
    
    # Quarantine check-in (if required)
    if IMPORT_GROUP_COUNTRY_MAP[import_group]["quarantine_days"] > 0:
        quarantine_days = IMPORT_GROUP_COUNTRY_MAP[import_group]["quarantine_days"]
        timeline["quarantine_release"] = arrival_date + timedelta(days=quarantine_days)
    
    return timeline


def check_compliance(
    pet_id: int,
    pet_name: str,
    scenario: Scenario,
    pet_type: PetType,
    vaccinations: list[dict],  # List of {"vaccine_name": str, "date_administered": datetime, "next_due_date": datetime}
    import_country: Optional[str] = None,
    license_expiry_date: Optional[datetime] = None,
    microchip_date: Optional[datetime] = None
) -> ComplianceResult:
    """
    Check overall compliance for a pet.
    
    Args:
        pet_id: Database ID of pet
        pet_name: Name of pet
        scenario: HK_RESIDENT or IMPORT
        pet_type: Dog or cat
        vaccinations: List of vaccination records
        import_country: Country of origin (for IMPORT scenario)
        license_expiry_date: Dog license expiry date
        microchip_date: Date microchip was implanted
    
    Returns:
        ComplianceResult with detailed status
    """
    now = datetime.now()
    result = ComplianceResult(
        pet_id=pet_id,
        pet_name=pet_name,
        scenario=scenario,
        is_compliant=True,
        overall_status=RequirementStatus.COMPLIANT,
    )
    
    # Build vaccine lookup
    vax_lookup = {v["vaccine_name"]: v for v in vaccinations}
    
    if scenario == Scenario.HK_RESIDENT:
        # Get requirements for resident
        requirements = get_resident_requirements(pet_type, include_recommended=False)
        
        for req in requirements:
            vax_name = req["name"]
            freq_days = req["frequency_days"]
            
            # Special handling for Microchip
            if vax_name == "Microchip":
                if microchip_date:
                    # Microchip is one-time, so compliant if done
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=RequirementStatus.COMPLIANT,
                        last_administered=microchip_date,
                        notes=req["notes"]
                    ))
                else:
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=RequirementStatus.NOT_DONE,
                        notes=req["notes"]
                    ))
                    result.is_compliant = False
                continue
            
            # Check if vaccination exists
            if vax_name in vax_lookup:
                vax = vax_lookup[vax_name]
                last_date = vax.get("date_administered")
                next_due = vax.get("next_due_date")
                
                if last_date and next_due:
                    days_until = (next_due - now).days
                    status = RequirementStatus.COMPLIANT
                    if days_until < 0:
                        status = RequirementStatus.OVERDUE
                        result.is_compliant = False
                    elif days_until <= 30:
                        status = RequirementStatus.DUE_SOON
                    
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=status,
                        last_administered=last_date,
                        next_due=next_due,
                        days_until_due=days_until,
                        notes=req["notes"],
                        frequency_days=freq_days
                    ))
                else:
                    # Has record but no next due date
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=RequirementStatus.NOT_DONE,
                        last_administered=last_date,
                        notes=req["notes"] + " - Next due date not set"
                    ))
                    result.is_compliant = False
            else:
                # Not vaccinated
                result.requirements.append(VaccinationRequirement(
                    vaccine_name=vax_name,
                    is_mandatory=True,
                    status=RequirementStatus.NOT_DONE,
                    notes=req["notes"]
                ))
                result.is_compliant = False
        
        # Check dog license (only for dogs)
        if pet_type == PetType.DOG and license_expiry_date:
            days_until = (license_expiry_date - now).days
            status = RequirementStatus.COMPLIANT
            if days_until < 0:
                status = RequirementStatus.OVERDUE
                result.is_compliant = False
            elif days_until <= 60:
                status = RequirementStatus.DUE_SOON
            
            result.requirements.append(VaccinationRequirement(
                vaccine_name="Dog License",
                is_mandatory=True,
                status=status,
                next_due=license_expiry_date,
                days_until_due=days_until,
                notes="3-year license, must renew with rabies vaccination"
            ))
    
    elif scenario == Scenario.IMPORT and import_country:
        # Import scenario
        import_req = get_import_requirements(import_country, pet_type)
        result.import_group = import_req.import_group
        result.quarantine_days = import_req.quarantine_days
        
        # Check each required vaccine
        for vax_name in import_req.required_vaccines:
            if vax_name in vax_lookup:
                vax = vax_lookup[vax_name]
                last_date = vax.get("date_administered")
                next_due = vax.get("next_due_date")
                
                if last_date and next_due:
                    days_until = (next_due - now).days
                    status = RequirementStatus.COMPLIANT
                    if days_until < 0:
                        status = RequirementStatus.OVERDUE
                        result.is_compliant = False
                    elif days_until <= 30:
                        status = RequirementStatus.DUE_SOON
                    
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=status,
                        last_administered=last_date,
                        next_due=next_due,
                        days_until_due=days_until,
                        notes=f"Required for import from {import_country}"
                    ))
                else:
                    result.requirements.append(VaccinationRequirement(
                        vaccine_name=vax_name,
                        is_mandatory=True,
                        status=RequirementStatus.NOT_DONE,
                        last_administered=last_date,
                        notes=f"Required for import from {import_country}"
                    ))
                    result.is_compliant = False
            else:
                result.requirements.append(VaccinationRequirement(
                    vaccine_name=vax_name,
                    is_mandatory=True,
                    status=RequirementStatus.NOT_DONE,
                    notes=f"Required for import from {import_country}"
                ))
                result.is_compliant = False
        
        # Add import-specific warnings
        if import_req.quarantine_days > 0:
            result.warnings.append(
                f"Quarantine of {import_req.quarantine_days} days required upon arrival"
            )
    
    # Determine overall status
    if result.is_compliant:
        # Check if any due soon
        due_soon = any(r.status == RequirementStatus.DUE_SOON for r in result.requirements)
        result.overall_status = RequirementStatus.DUE_SOON if due_soon else RequirementStatus.COMPLIANT
    else:
        # Check if any overdue
        overdue = any(r.status == RequirementStatus.OVERDUE for r in result.requirements)
        result.overall_status = RequirementStatus.OVERDUE if overdue else RequirementStatus.NOT_DONE
    
    return result


def get_next_due_date(
    vaccine_name: str,
    date_administered: datetime,
    pet_type: PetType,
    scenario: Scenario = Scenario.HK_RESIDENT,
    import_country: Optional[str] = None
) -> Optional[datetime]:
    """
    Calculate next due date for a vaccination.
    
    Args:
        vaccine_name: Name of the vaccine
        date_administered: Date the vaccine was given
        pet_type: Dog or cat
        scenario: Resident or import
        import_country: Origin country (for import scenario)
    
    Returns:
        Next due date, or None if one-time
    """
    # Rabies: 3 years for residents
    if vaccine_name == "Rabies" and scenario == Scenario.HK_RESIDENT:
        return date_administered.replace(year=date_administered.year + 3)
    
    # DHPP/DAPP: annual
    if vaccine_name in ["DHPP/DAPP", "DAPP"]:
        return date_administered.replace(year=date_administered.year + 1)
    
    # FVRCP: annual
    if vaccine_name == "FVRCP":
        return date_administered.replace(year=date_administered.year + 1)
    
    # Leptospirosis: annual
    if vaccine_name == "Leptospirosis":
        return date_administered.replace(year=date_administered.year + 1)
    
    # Bordetella: 6-12 months
    if vaccine_name == "Bordetella":
        return date_administered + timedelta(days=365)
    
    # FeLV: annual
    if vaccine_name == "FeLV":
        return date_administered.replace(year=date_administered.year + 1)
    
    # Import rabies timing (30 days to 12 months)
    if vaccine_name == "Rabies" and scenario == Scenario.IMPORT:
        # For import, the "next due" is the latest allowed date (12 months)
        return date_administered + timedelta(days=365)
    
    # Microchip is one-time
    if vaccine_name == "Microchip":
        return None
    
    # Default to 1 year
    return date_administered.replace(year=date_administered.year + 1)


def format_compliance_summary(result: ComplianceResult) -> str:
    """
    Format a compliance result as human-readable text.
    
    Args:
        result: ComplianceResult from check_compliance()
    
    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"=== Compliance Check: {result.pet_name} ===")
    lines.append(f"Scenario: {result.scenario.value}")
    if result.import_group:
        lines.append(f"Import Group: {result.import_group.value}")
        if result.quarantine_days:
            lines.append(f"Quarantine: {result.quarantine_days} days")
    lines.append(f"Overall Status: {result.overall_status.value}")
    lines.append(f"Compliant: {'Yes' if result.is_compliant else 'No'}")
    lines.append("")
    lines.append("Requirements:")
    
    for req in result.requirements:
        status_icon = {
            RequirementStatus.COMPLIANT: "✓",
            RequirementStatus.DUE_SOON: "⚠",
            RequirementStatus.OVERDUE: "✗",
            RequirementStatus.NOT_DONE: "○",
            RequirementStatus.NOT_APPLICABLE: "-",
        }.get(req.status, "?")
        
        line = f"  {status_icon} {req.vaccine_name}: {req.status.value}"
        if req.days_until_due is not None:
            if req.days_until_due >= 0:
                line += f" (due in {req.days_until_due} days)"
            else:
                line += f" ({-req.days_until_due} days overdue)"
        lines.append(line)
        if req.notes:
            lines.append(f"      {req.notes}")
    
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in result.warnings:
            lines.append(f"  ⚠ {w}")
    
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for e in result.errors:
            lines.append(f"  ✗ {e}")
    
    return "\n".join(lines)


# ============================================================================
# TEST DATA
# ============================================================================

if __name__ == "__main__":
    # Demo tests
    print("=== HK Vaccination Rules Engine Demo ===\n")
    
    # Test 1: Resident dog compliance
    print("1. Resident Dog Compliance Check:")
    result = check_compliance(
        pet_id=1,
        pet_name="Max",
        scenario=Scenario.HK_RESIDENT,
        pet_type=PetType.DOG,
        vaccinations=[
            {"vaccine_name": "Rabies", "date_administered": datetime(2024, 6, 1), "next_due_date": datetime(2027, 6, 1)},
        ],
        license_expiry_date=datetime(2027, 6, 1),
        microchip_date=datetime(2024, 5, 1)
    )
    print(format_compliance_summary(result))
    print()
    
    # Test 2: Import requirements from Australia (Group I)
    print("2. Import from Australia (Group I):")
    req = get_import_requirements("Australia", PetType.DOG)
    print(f"  Group: {req.import_group.value}")
    print(f"  Quarantine: {req.quarantine_days} days")
    print(f"  Rabies required: {req.rabies_required}")
    print(f"  Required vaccines: {', '.join(req.required_vaccines)}")
    print()
    
    # Test 3: Import requirements from USA (Group II)
    print("3. Import from USA (Group II):")
    req = get_import_requirements("USA", PetType.DOG)
    print(f"  Group: {req.import_group.value}")
    print(f"  Quarantine: {req.quarantine_days} days")
    print(f"  Rabies required: {req.rabies_required}")
    print()
    
    # Test 4: Import timeline
    print("4. Import Timeline (from USA, arriving March 15, 2026):")
    arrival = datetime(2026, 3, 15)
    timeline = calculate_import_timeline(arrival, ImportCountryGroup.GROUP_II)
    for action, date in timeline.items():
        print(f"  {action}: {date.strftime('%Y-%m-%d')}")
    print()
    
    # Test 5: Next due date calculation
    print("5. Next Due Date Calculation:")
    test_date = datetime(2025, 1, 15)
    print(f"  Rabies (resident): {get_next_due_date('Rabies', test_date, PetType.DOG, Scenario.HK_RESIDENT)}")
    print(f"  DHPP/DAPP: {get_next_due_date('DHPP/DAPP', test_date, PetType.DOG)}")
    print(f"  Rabies (import): {get_next_due_date('Rabies', test_date, PetType.DOG, Scenario.IMPORT, 'USA')}")
