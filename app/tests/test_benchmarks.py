"""
Performance Benchmark Tests for PetVaxHK.

Benchmarks critical operations: date calculations, reminder generation,
rules engine, and database operations.
"""

import pytest
import time
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Callable, Any
from dataclasses import dataclass

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.dates import (
    calculate_rabies_due_date,
    calculate_dhpp_first_series,
    calculate_annual_booster_due,
    calculate_import_timing_requirements,
    calculate_license_renewal_due,
    calculate_compliance_status,
    PetType as DatesPetType,
    Scenario,
    ImportGroup,
)
from app.core.reminders import ReminderEngine, ReminderConfig, ReminderType
from app.core.rules import (
    check_compliance,
    get_import_requirements,
    format_compliance_summary,
    get_resident_requirements,
    ImportCountryGroup,
    PetType as RulesPetType,
)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_us: float  # microseconds per iteration
    min_time_us: float
    max_time_us: float
    ops_per_second: float


def benchmark_function(func: Callable, iterations: int = 1000, *args, **kwargs) -> BenchmarkResult:
    """Benchmark a function over multiple iterations."""
    times = []
    
    # Warm-up run
    func(*args, **kwargs)
    
    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)  # Convert to microseconds
    
    total_time = sum(times)
    return BenchmarkResult(
        name=func.__name__,
        iterations=iterations,
        total_time_ms=total_time / 1000,
        avg_time_us=total_time / iterations,
        min_time_us=min(times),
        max_time_us=max(times),
        ops_per_second=iterations / (total_time / 1_000_000),
    )


def print_benchmark(result: BenchmarkResult) -> str:
    """Format benchmark result as string."""
    return (
        f"{result.name}:\n"
        f"  Iterations: {result.iterations:,}\n"
        f"  Total: {result.total_time_ms:.2f}ms\n"
        f"  Avg: {result.avg_time_us:.2f}µs/op\n"
        f"  Min/Max: {result.min_time_us:.2f}/{result.max_time_us:.2f}µs\n"
        f"  Throughput: {result.ops_per_second:,.0f} ops/sec\n"
    )


class TestDateCalculationsBenchmark:
    """Benchmarks for date calculation functions."""
    
    def test_calculate_rabies_due_date(self):
        """Benchmark rabies due date calculation."""
        base_date = datetime(2024, 1, 15)
        
        result = benchmark_function(
            calculate_rabies_due_date,
            iterations=10000,
            last_vaccination_date=base_date,
            is_boosters=True
        )
        
        print(f"\n=== Date Calculations Benchmark ===")
        print(print_benchmark(result))
        
        # Assert performance - should be under 100µs average
        assert result.avg_time_us < 100, f" rabies_due_date too slow: {result.avg_time_us:.2f}µs"
    
    def test_calculate_dhpp_first_series(self):
        """Benchmark DHPP first series calculation."""
        base_date = datetime(2024, 1, 15)
        
        result = benchmark_function(
            calculate_dhpp_first_series,
            iterations=10000,
            start_date=base_date
        )
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 100, f"dhpp_first_series too slow: {result.avg_time_us:.2f}µs"
    
    def test_calculate_annual_booster_due(self):
        """Benchmark annual booster due date calculation."""
        base_date = datetime(2024, 1, 15)
        
        result = benchmark_function(
            calculate_annual_booster_due,
            iterations=10000,
            last_booster_date=base_date
        )
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 100, f"annual_booster_due too slow: {result.avg_time_us:.2f}µs"
    
    def test_calculate_import_timing_requirements(self):
        """Benchmark import timing requirements calculation."""
        arrival_date = datetime(2024, 6, 15)
        
        result = benchmark_function(
            calculate_import_timing_requirements,
            iterations=5000,
            arrival_date=arrival_date,
            import_group=ImportGroup.GROUP_II
        )
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 500, f"import_timing too slow: {result.avg_time_us:.2f}µs"
    
    def test_calculate_compliance_status(self):
        """Benchmark compliance status calculation."""
        now = datetime.now()
        
        result = benchmark_function(
            calculate_compliance_status,
            iterations=5000,
            pet_birth_date=now - timedelta(days=400),
            last_rabies_date=now - timedelta(days=100),
            last_dhpp_date=now - timedelta(days=200),
            license_issue_date=now - timedelta(days=100),
            scenario=Scenario.HK_RESIDENT
        )
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 500, f"compliance_status too slow: {result.avg_time_us:.2f}µs"


class TestRulesEngineBenchmark:
    """Benchmarks for rules engine functions."""
    
    def test_get_resident_requirements(self):
        """Benchmark getting resident vaccination requirements."""
        
        result = benchmark_function(
            get_resident_requirements,
            iterations=5000,
            pet_type=RulesPetType.DOG
        )
        
        print(f"\n=== Rules Engine Benchmark ===")
        print(print_benchmark(result))
        
        assert result.avg_time_us < 1000, f"get_resident_requirements too slow: {result.avg_time_us:.2f}µs"
    
    def test_get_import_requirements(self):
        """Benchmark getting import requirements."""
        
        result = benchmark_function(
            get_import_requirements,
            iterations=5000,
            country="Taiwan",
            pet_type=RulesPetType.DOG
        )
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 1000, f"get_import_requirements too slow: {result.avg_time_us:.2f}µs"
    
    def test_check_compliance(self):
        """Benchmark compliance checking."""
        
        # Create sample vaccinations list - use datetime objects
        now = datetime.now()
        
        def make_check_compliance_call():
            vaccinations = [
                {"vaccine_name": "Rabies", "date_administered": now - timedelta(days=100), "next_due_date": now + timedelta(days=265)},
                {"vaccine_name": "DHPP", "date_administered": now - timedelta(days=200), "next_due_date": now + timedelta(days=165)},
            ]
            return check_compliance(
                pet_id=1,
                pet_name="TestDog",
                scenario=Scenario.HK_RESIDENT,
                pet_type=RulesPetType.DOG,
                vaccinations=vaccinations,
            )
        
        result = benchmark_function(make_check_compliance_call, iterations=3000)
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 5000, f"check_compliance too slow: {result.avg_time_us:.2f}µs"


class TestDatabaseBenchmark:
    """Benchmarks for database operations."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a test database."""
        db_path = tmp_path / "test_benchmark.db"
        
        # Create database schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                date_of_birth TEXT,
                microchip_number TEXT,
                owner_name TEXT,
                owner_phone TEXT,
                owner_email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vaccines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                is_mandatory INTEGER DEFAULT 0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_vaccinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER NOT NULL,
                vaccine_id INTEGER NOT NULL,
                date_administered TEXT NOT NULL,
                next_due_date TEXT,
                vet_clinic_id INTEGER,
                batch_number TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pet_id) REFERENCES pets(id),
                FOREIGN KEY (vaccine_id) REFERENCES vaccines(id)
            )
        """)
        
        # Insert test data - 100 pets
        species_list = ['dog', 'cat']
        for i in range(100):
            cursor.execute(
                "INSERT INTO pets (name, species, breed) VALUES (?, ?, ?)",
                (f"Pet{i}", species_list[i % 2], "Breed")
            )
        
        # Insert vaccines
        vaccines = [
            ("Rabies", "dog", 1),
            ("Rabies", "cat", 1),
            ("DHPP", "dog", 1),
            ("FVRCP", "cat", 1),
        ]
        for name, species, mandatory in vaccines:
            cursor.execute(
                "INSERT INTO vaccines (name, species, is_mandatory) VALUES (?, ?, ?)",
                (name, species, mandatory)
            )
        
        # Insert vaccination records
        now = datetime.now().isoformat()
        for pet_id in range(1, 101):
            for vaccine_id in range(1, 5):
                cursor.execute(
                    "INSERT INTO pet_vaccinations (pet_id, vaccine_id, date_administered, next_due_date) VALUES (?, ?, ?, ?)",
                    (pet_id, vaccine_id, now, now)
                )
        
        conn.commit()
        conn.close()
        
        yield str(db_path)
        
        # Cleanup
        os.unlink(db_path)
    
    def test_simple_query(self, test_db):
        """Benchmark simple SELECT query."""
        
        def query_pets():
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pets")
            cursor.fetchall()
            conn.close()
        
        result = benchmark_function(query_pets, iterations=1000)
        
        print(f"\n=== Database Benchmark ===")
        print(print_benchmark(result))
        
        assert result.avg_time_us < 10000, f"simple query too slow: {result.avg_time_us:.2f}µs"
    
    def test_join_query(self, test_db):
        """Benchmark JOIN query."""
        
        def join_query():
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.name, v.name, pv.date_administered
                FROM pets p
                JOIN pet_vaccinations pv ON p.id = pv.pet_id
                JOIN vaccines v ON pv.vaccine_id = v.id
                LIMIT 100
            """)
            cursor.fetchall()
            conn.close()
        
        result = benchmark_function(join_query, iterations=1000)
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 20000, f"join query too slow: {result.avg_time_us:.2f}µs"
    
    def test_aggregation_query(self, test_db):
        """Benchmark aggregation query."""
        
        def agg_query():
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT species, COUNT(*) as count
                FROM pets
                GROUP BY species
            """)
            cursor.fetchall()
            conn.close()
        
        result = benchmark_function(agg_query, iterations=1000)
        
        print(print_benchmark(result))
        
        assert result.avg_time_us < 10000, f"aggregation query too slow: {result.avg_time_us:.2f}µs"


class TestOverallPerformance:
    """Overall performance benchmarks."""
    
    def test_full_compliance_check_workflow(self):
        """Benchmark complete compliance check workflow."""
        
        now = datetime.now()
        
        def full_workflow():
            # Get resident requirements
            reqs = get_resident_requirements(RulesPetType.DOG)
            
            # Create sample vaccinations - use datetime objects
            vaccinations = [
                {"vaccine_name": "Rabies", "date_administered": now - timedelta(days=100), "next_due_date": now + timedelta(days=265)},
                {"vaccine_name": "DHPP", "date_administered": now - timedelta(days=200), "next_due_date": now + timedelta(days=165)},
            ]
            
            # Check compliance
            compliance = check_compliance(
                pet_id=1,
                pet_name="TestDog",
                scenario=Scenario.HK_RESIDENT,
                pet_type=RulesPetType.DOG,
                vaccinations=vaccinations,
            )
            
            # Format summary - only takes the compliance result
            summary = format_compliance_summary(compliance)
        
        result = benchmark_function(full_workflow, iterations=2000)
        
        print(f"\n=== Overall Performance ===")
        print(print_benchmark(result))
        
        assert result.avg_time_us < 5000, f"full workflow too slow: {result.avg_time_us:.2f}µs"


if __name__ == "__main__":
    # Run benchmarks and print results
    print("=" * 60)
    print("PetVaxHK Performance Benchmark Suite")
    print("=" * 60)
    
    # Date calculations
    print("\n### Date Calculations ###")
    test = TestDateCalculationsBenchmark()
    test.test_calculate_rabies_due_date()
    test.test_calculate_dhpp_first_series()
    test.test_calculate_annual_booster_due()
    test.test_calculate_import_timing_requirements()
    test.test_calculate_compliance_status()
    
    # Rules engine
    print("\n### Rules Engine ###")
    test_rules = TestRulesEngineBenchmark()
    test_rules.test_get_resident_requirements()
    test_rules.test_get_import_requirements()
    test_rules.test_check_compliance()
    
    # Overall
    print("\n### Overall Performance ###")
    test_overall = TestOverallPerformance()
    test_overall.test_full_compliance_check_workflow()
    
    print("\n" + "=" * 60)
    print("All benchmarks completed!")
    print("=" * 60)
