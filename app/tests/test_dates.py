"""Core date calculation tests for PetVaxHK."""

import pytest
from datetime import datetime, timedelta
from app.core.dates import (
    calculate_rabies_due_date,
    calculate_dhpp_first_series,
    calculate_annual_booster_due,
    calculate_import_timing_requirements,
    calculate_license_renewal_due,
    calculate_compliance_status,
    ImportGroup,
    Scenario,
    format_days_until,
)


class TestRabiesCalculation:
    """Tests for rabies vaccination date calculations."""
    
    def test_rabies_booster_every_3_years(self):
        """Booster due every 3 years (1095 days)."""
        last_vax = datetime(2024, 1, 15)
        due = calculate_rabies_due_date(last_vax, is_boosters=True)
        assert due == datetime(2027, 1, 15)
    
    def test_rabies_first_vaccination_30_days(self):
        """First rabies vaccination due within 30 days."""
        last_vax = datetime(2024, 1, 15)
        due = calculate_rabies_due_date(last_vax, is_boosters=False)
        assert due == datetime(2024, 2, 14)


class TestDHPPSeries:
    """Tests for DHPP first series calculations."""
    
    def test_dhpp_three_doses(self):
        """DHPP first series has 3 doses at 8, 12, 16 weeks."""
        start = datetime(2024, 1, 15)
        doses = calculate_dhpp_first_series(start)
        
        assert len(doses) == 3
        assert doses[0] == datetime(2024, 3, 11)  # 8 weeks
        assert doses[1] == datetime(2024, 4, 8)  # 12 weeks
        assert doses[2] == datetime(2024, 5, 6)  # 16 weeks


class TestAnnualBooster:
    """Tests for annual booster calculations."""
    
    def test_annual_booster_365_days(self):
        """Annual booster due in 365 days."""
        last_booster = datetime(2024, 1, 15)
        due = calculate_annual_booster_due(last_booster)
        assert due == datetime(2025, 1, 15)


class TestImportTiming:
    """Tests for import timing calculations."""
    
    def test_group_i_no_quarantine(self):
        """Group I countries have no quarantine."""
        arrival = datetime(2024, 6, 1)
        result = calculate_import_timing_requirements(arrival, ImportGroup.GROUP_I)
        
        assert result.dates["quarantine_days"] == 0
        assert "quarantine_release" not in result.dates
    
    def test_group_ii_quarantine_120_days(self):
        """Group II requires 120 days quarantine."""
        arrival = datetime(2024, 6, 1)
        result = calculate_import_timing_requirements(arrival, ImportGroup.GROUP_II)
        
        assert result.dates["quarantine_days"] == 120
        assert result.dates["quarantine_release"] == datetime(2024, 9, 29)
    
    def test_rabies_vaccination_window(self):
        """Rabies must be 30-365 days before arrival."""
        arrival = datetime(2024, 6, 1)
        result = calculate_import_timing_requirements(arrival, ImportGroup.GROUP_I)
        
        assert result.dates["rabies_vaccination_earliest"] == datetime(2023, 6, 2)
        assert result.dates["rabies_vaccination_latest"] == datetime(2024, 5, 2)


class TestLicenseRenewal:
    """Tests for license renewal calculations."""
    
    def test_license_3_year_renewal(self):
        """License renewal due every 3 years."""
        issue = datetime(2024, 1, 15)
        due = calculate_license_renewal_due(issue)
        assert due == datetime(2027, 1, 15)


class TestComplianceStatus:
    """Tests for compliance status calculations."""
    
    def test_compliant_rabies(self):
        """Pet with recent rabies is compliant."""
        now = datetime.now()
        status = calculate_compliance_status(
            pet_birth_date=now - timedelta(days=400),
            last_rabies_date=now - timedelta(days=100),
            last_dhpp_date=now - timedelta(days=100),
            license_issue_date=now - timedelta(days=100),
        )
        
        assert status["rabies"]["compliant"] is True
        assert status["rabies"]["status"] == "ok"
    
    def test_overdue_rabies(self):
        """Pet with overdue rabies is non-compliant."""
        now = datetime.now()
        status = calculate_compliance_status(
            pet_birth_date=now - timedelta(days=400),
            last_rabies_date=now - timedelta(days=1100),  # ~3 years ago
            last_dhpp_date=now - timedelta(days=100),
            license_issue_date=now - timedelta(days=1100),
        )
        
        assert status["rabies"]["compliant"] is False
        assert status["rabies"]["status"] == "overdue"


class TestFormatting:
    """Tests for date formatting utilities."""
    
    def test_format_days_positive(self):
        """Positive days formatted correctly."""
        assert "Due in 1 month" == format_days_until(30)
    
    def test_format_days_negative(self):
        """Negative days show overdue."""
        assert "5 days overdue" == format_days_until(-5)
    
    def test_format_days_today(self):
        """Zero days shows today."""
        assert "Due today" == format_days_until(0)
    
    def test_format_days_tomorrow(self):
        """One day shows tomorrow."""
        assert "Due tomorrow" == format_days_until(1)
