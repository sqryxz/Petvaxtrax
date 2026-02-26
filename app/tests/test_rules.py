"""
Unit tests for HK Vaccination Rules Engine.

Tests the rules engine functionality including compliance checking,
import requirements, and timeline calculations.
"""

import pytest
from datetime import datetime, timedelta

from app.core.rules import (
    RequirementStatus,
    ImportCountryGroup,
    ImportRequirements,
    ComplianceResult,
    get_resident_requirements,
    determine_import_group,
    get_import_requirements,
    calculate_import_timeline,
    check_compliance,
    get_next_due_date,
    format_compliance_summary,
)
from app.core.dates import PetType, Scenario


class TestResidentRequirements:
    """Tests for resident pet requirements."""
    
    def test_resident_dog_mandatory_vaccines(self):
        """Resident dogs require rabies and microchip."""
        reqs = get_resident_requirements(PetType.DOG, include_recommended=False)
        vax_names = [r["name"] for r in reqs]
        
        assert "Rabies" in vax_names
        assert "Microchip" in vax_names
    
    def test_resident_dog_with_recommended(self):
        """Resident dogs can have recommended vaccines."""
        reqs = get_resident_requirements(PetType.DOG, include_recommended=True)
        vax_names = [r["name"] for r in reqs]
        
        assert "Rabies" in vax_names
        assert "DHPP/DAPP" in vax_names
        assert "Leptospirosis" in vax_names
    
    def test_resident_cat_no_mandatory(self):
        """Resident cats have no mandatory vaccines in HK."""
        reqs = get_resident_requirements(PetType.CAT, include_recommended=False)
        assert len(reqs) == 0
    
    def test_resident_cat_recommended(self):
        """Resident cats can have recommended vaccines."""
        reqs = get_resident_requirements(PetType.CAT, include_recommended=True)
        vax_names = [r["name"] for r in reqs]
        
        assert "FVRCP" in vax_names
        assert "FeLV" in vax_names


class TestImportGroupDetermination:
    """Tests for import group determination."""
    
    def test_group_i_countries(self):
        """Group I countries are rabies-free."""
        for country in ["Australia", "Japan", "New Zealand", "United Kingdom"]:
            assert determine_import_group(country) == ImportCountryGroup.GROUP_I
    
    def test_group_ii_countries(self):
        """Group II countries are rabies-controlled."""
        for country in ["USA", "Canada", "Germany", "France"]:
            assert determine_import_group(country) == ImportCountryGroup.GROUP_II
    
    def test_group_iiia_countries(self):
        """Group IIIA countries have rabies."""
        for country in ["Thailand", "Malaysia", "Hungary"]:
            assert determine_import_group(country) == ImportCountryGroup.GROUP_IIIA
    
    def test_mainland_china(self):
        """Mainland China has special 30-day arrangement."""
        for country in ["China", "Mainland China", "PRC"]:
            assert determine_import_group(country) == ImportCountryGroup.MAINLAND_CHINA
    
    def test_unknown_country_group_iiib(self):
        """Unknown countries default to Group IIIB."""
        assert determine_import_group("Brazil") == ImportCountryGroup.GROUP_IIIB
        assert determine_import_group("India") == ImportCountryGroup.GROUP_IIIB


class TestImportRequirements:
    """Tests for import requirements calculation."""
    
    def test_group_i_no_quarantine(self):
        """Group I has no quarantine."""
        req = get_import_requirements("Australia", PetType.DOG)
        
        assert req.quarantine_days == 0
        assert req.rabies_required is False
        assert req.rabies_titer_required is False
    
    def test_group_ii_no_quarantine(self):
        """Group II has no quarantine but requires rabies."""
        req = get_import_requirements("USA", PetType.DOG)
        
        assert req.quarantine_days == 0
        assert req.rabies_required is True
        assert req.rabies_titer_required is False
    
    def test_group_iiia_quarantine_30_days(self):
        """Group IIIA requires 30-day quarantine."""
        req = get_import_requirements("Thailand", PetType.DOG)
        
        assert req.quarantine_days == 30
        assert req.rabies_required is True
        assert req.rabies_titer_required is True
    
    def test_mainland_china_quarantine_30_days(self):
        """Mainland China has 30-day quarantine."""
        req = get_import_requirements("Mainland China", PetType.DOG)
        
        assert req.quarantine_days == 30
        assert req.rabies_required is True
    
    def test_group_iiib_quarantine_120_days(self):
        """Group IIIB requires 120-day quarantine."""
        req = get_import_requirements("Brazil", PetType.DOG)
        
        assert req.quarantine_days == 120
        assert req.rabies_required is True
        assert req.rabies_titer_required is True
    
    def test_import_requires_permit_and_health_cert(self):
        """All imports require permit and health certificate."""
        req = get_import_requirements("Australia", PetType.DOG)
        
        assert req.import_permit_required is True
        assert req.health_certificate_required is True
    
    def test_import_dog_vaccines(self):
        """Import dogs require specific vaccines."""
        req = get_import_requirements("USA", PetType.DOG)
        
        assert "Rabies" in req.required_vaccines
        assert "DHPP/DAPP" in req.required_vaccines
        assert "Microchip" in req.required_vaccines
    
    def test_import_cat_vaccines(self):
        """Import cats require specific vaccines."""
        req = get_import_requirements("USA", PetType.CAT)
        
        assert "FVRCP" in req.required_vaccines
        assert "Feline Panleukopenia" in req.required_vaccines


class TestImportTimeline:
    """Tests for import timeline calculation."""
    
    def test_rabies_timing_window(self):
        """Rabies must be 30-365 days before arrival."""
        arrival = datetime(2026, 6, 1)
        timeline = calculate_import_timeline(arrival, ImportCountryGroup.GROUP_II)
        
        # Rabies earliest: arrival - 365 days
        assert timeline["rabies_vaccination_earliest"] == arrival - timedelta(days=365)
        # Rabies latest: arrival - 30 days
        assert timeline["rabies_vaccination_latest"] == arrival - timedelta(days=30)
    
    def test_health_certificate_timing(self):
        """Health certificate must be within 14 days of travel."""
        arrival = datetime(2026, 6, 1)
        timeline = calculate_import_timeline(arrival, ImportCountryGroup.GROUP_II)
        
        assert timeline["health_certificate_earliest"] == arrival - timedelta(days=14)
        assert timeline["health_certificate_latest"] == arrival - timedelta(days=1)
    
    def test_quarantine_release_for_group_iiia(self):
        """Group IIIA quarantine release date is calculated."""
        arrival = datetime(2026, 6, 1)
        timeline = calculate_import_timeline(arrival, ImportCountryGroup.GROUP_IIIA)
        
        assert timeline["quarantine_release"] == arrival + timedelta(days=30)
    
    def test_no_quarantine_for_group_i(self):
        """Group I has no quarantine release date."""
        arrival = datetime(2026, 6, 1)
        timeline = calculate_import_timeline(arrival, ImportCountryGroup.GROUP_I)
        
        assert "quarantine_release" not in timeline


class TestComplianceCheck:
    """Tests for compliance checking."""
    
    def test_compliant_resident_dog(self):
        """A fully vaccinated resident dog is compliant."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            pet_type=PetType.DOG,
            vaccinations=[
                {
                    "vaccine_name": "Rabies",
                    "date_administered": now - timedelta(days=365),
                    "next_due_date": now + timedelta(days=730),  # ~2 years from now
                }
            ],
            license_expiry_date=now + timedelta(days=730),
            microchip_date=now - timedelta(days=400)
        )
        
        assert result.is_compliant is True
        assert result.overall_status == RequirementStatus.COMPLIANT
    
    def test_overdue_resident_dog(self):
        """An overdue resident dog is not compliant."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            pet_type=PetType.DOG,
            vaccinations=[
                {
                    "vaccine_name": "Rabies",
                    "date_administered": now - timedelta(days=1500),  # ~4 years ago
                    "next_due_date": now - timedelta(days=400),  # Overdue
                }
            ],
            license_expiry_date=now - timedelta(days=400),
            microchip_date=now - timedelta(days=1500)
        )
        
        assert result.is_compliant is False
        assert result.overall_status == RequirementStatus.OVERDUE
    
    def test_missing_rabies_resident_dog(self):
        """Missing rabies makes resident dog non-compliant."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            pet_type=PetType.DOG,
            vaccinations=[],  # No vaccinations
            license_expiry_date=now + timedelta(days=730),
            microchip_date=now - timedelta(days=400)
        )
        
        assert result.is_compliant is False
        
        # Find rabies requirement
        rabies_req = next(r for r in result.requirements if r.vaccine_name == "Rabies")
        assert rabies_req.status == RequirementStatus.NOT_DONE
    
    def test_missing_microchip_resident_dog(self):
        """Missing microchip makes resident dog non-compliant."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            pet_type=PetType.DOG,
            vaccinations=[],
            license_expiry_date=now + timedelta(days=730),
            microchip_date=None  # No microchip
        )
        
        # Find microchip requirement
        microchip_req = next(r for r in result.requirements if r.vaccine_name == "Microchip")
        assert microchip_req.status == RequirementStatus.NOT_DONE
    
    def test_due_soon_status(self):
        """A vaccine due within 30 days shows as due_soon."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            pet_type=PetType.DOG,
            vaccinations=[
                {
                    "vaccine_name": "Rabies",
                    "date_administered": now - timedelta(days=1100),
                    "next_due_date": now + timedelta(days=20),  # Due in 20 days
                }
            ],
            license_expiry_date=now + timedelta(days=730),
            microchip_date=now - timedelta(days=1200)
        )
        
        assert result.is_compliant is True
        assert result.overall_status == RequirementStatus.DUE_SOON
    
    def test_import_compliance(self):
        """Import scenario checks specific requirements."""
        now = datetime.now()
        
        result = check_compliance(
            pet_id=1,
            pet_name="Buddy",
            scenario=Scenario.IMPORT,
            pet_type=PetType.DOG,
            vaccinations=[
                {
                    "vaccine_name": "Rabies",
                    "date_administered": now - timedelta(days=180),
                    "next_due_date": now + timedelta(days=185),
                },
                {
                    "vaccine_name": "DHPP/DAPP",
                    "date_administered": now - timedelta(days=180),
                    "next_due_date": now + timedelta(days=185),
                }
            ],
            import_country="USA"
        )
        
        assert result.import_group == ImportCountryGroup.GROUP_II
        assert result.quarantine_days == 0


class TestNextDueDate:
    """Tests for next due date calculation."""
    
    def test_rabies_resident_three_years(self):
        """Resident rabies is due every 3 years."""
        date = datetime(2024, 6, 1)
        next_due = get_next_due_date("Rabies", date, PetType.DOG, Scenario.HK_RESIDENT)
        
        assert next_due == datetime(2027, 6, 1)
    
    def test_dhpp_annual(self):
        """DHPP is due annually."""
        date = datetime(2024, 6, 1)
        next_due = get_next_due_date("DHPP/DAPP", date, PetType.DOG)
        
        assert next_due == datetime(2025, 6, 1)
    
    def test_fvrcp_annual(self):
        """FVRCP is due annually for cats."""
        date = datetime(2024, 6, 1)
        next_due = get_next_due_date("FVRCP", date, PetType.CAT)
        
        assert next_due == datetime(2025, 6, 1)
    
    def test_microchip_one_time(self):
        """Microchip is a one-time requirement."""
        date = datetime(2024, 6, 1)
        next_due = get_next_due_date("Microchip", date, PetType.DOG)
        
        assert next_due is None
    
    def test_import_rabies_one_year(self):
        """Import rabies is valid for 1 year."""
        date = datetime(2024, 6, 1)
        next_due = get_next_due_date("Rabies", date, PetType.DOG, Scenario.IMPORT, "USA")
        
        assert next_due == datetime(2025, 6, 1)


class TestFormatComplianceSummary:
    """Tests for compliance summary formatting."""
    
    def test_format_includes_pet_name(self):
        """Summary includes pet name."""
        result = ComplianceResult(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            is_compliant=True,
            overall_status=RequirementStatus.COMPLIANT,
        )
        
        summary = format_compliance_summary(result)
        assert "Max" in summary
    
    def test_format_includes_status(self):
        """Summary includes overall status."""
        result = ComplianceResult(
            pet_id=1,
            pet_name="Max",
            scenario=Scenario.HK_RESIDENT,
            is_compliant=True,
            overall_status=RequirementStatus.COMPLIANT,
        )
        
        summary = format_compliance_summary(result)
        assert "compliant" in summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
