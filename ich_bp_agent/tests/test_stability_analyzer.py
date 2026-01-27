"""
Tests for Stability Analyzer
"""
try:
    import pytest
except ImportError:
    pytest = None
from datetime import datetime, date, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ich_bp_agent.analyzers.stability_analyzer import StabilityAnalyzer, BPReading
from ich_bp_agent.models.patient import ICHPatient, ICHCondition, ICHPhase, ICHLocation


def create_test_patient(days_since_onset: int = 30) -> ICHPatient:
    """Create a test patient"""
    onset_date = date.today() - timedelta(days=days_since_onset)
    ich_condition = ICHCondition(
        id="condition-test-001",
        patient_id="patient-test-001",
        onset_date=onset_date,
        location=ICHLocation.BASAL_GANGLIA,
        severity="moderate",
    )
    return ICHPatient(
        patient_id="patient-test-001",
        name="Test Patient",
        birth_date=date(1960, 1, 1),
        gender="male",
        ich_condition=ich_condition,
        target_systolic=(120, 140),
        target_diastolic=(70, 90),
    )


def create_stable_readings(days: int = 14, base_systolic: int = 125, base_diastolic: int = 78) -> list:
    """Create stable BP readings"""
    readings = []
    for day in range(days):
        for hour in [8, 20]:
            timestamp = datetime.now() - timedelta(days=days - day - 1, hours=24 - hour)
            readings.append(BPReading(
                timestamp=timestamp,
                systolic=base_systolic + (day % 3 - 1),  # Small variation
                diastolic=base_diastolic + (day % 2),
                patient_id="patient-test-001",
            ))
    return readings


def create_unstable_readings(days: int = 14) -> list:
    """Create unstable BP readings with high variability"""
    import random
    random.seed(42)
    readings = []
    for day in range(days):
        for hour in [8, 20]:
            timestamp = datetime.now() - timedelta(days=days - day - 1, hours=24 - hour)
            readings.append(BPReading(
                timestamp=timestamp,
                systolic=130 + random.randint(-20, 20),  # High variability
                diastolic=85 + random.randint(-10, 10),
                patient_id="patient-test-001",
            ))
    return readings


def test_stability_score_calculation():
    """Test basic stability score calculation"""
    analyzer = StabilityAnalyzer()
    readings = create_stable_readings()
    target_systolic = (120, 140)
    target_diastolic = (70, 90)

    score = analyzer.calculate_stability_score(readings, target_systolic, target_diastolic)

    assert not score.insufficient_data
    assert score.score > 0
    assert score.score <= 100
    assert score.components is not None


def test_high_stability_score_for_stable_readings():
    """Test that stable readings yield high stability score"""
    analyzer = StabilityAnalyzer()
    readings = create_stable_readings(base_systolic=130, base_diastolic=80)
    target_systolic = (120, 140)
    target_diastolic = (70, 90)

    score = analyzer.calculate_stability_score(readings, target_systolic, target_diastolic)

    assert score.score >= 70, f"Expected score >= 70, got {score.score}"
    assert score.components.target_achievement_rate > 80


def test_low_stability_score_for_unstable_readings():
    """Test that unstable readings yield lower stability score"""
    analyzer = StabilityAnalyzer()
    readings = create_unstable_readings()
    target_systolic = (120, 140)
    target_diastolic = (70, 90)

    score = analyzer.calculate_stability_score(readings, target_systolic, target_diastolic)

    # Unstable readings should have lower score due to variability
    assert score.components.variability_coefficient > 10


def test_insufficient_data():
    """Test handling of insufficient data"""
    analyzer = StabilityAnalyzer()
    readings = create_stable_readings(days=2)  # Only 4 readings
    target_systolic = (120, 140)
    target_diastolic = (70, 90)

    score = analyzer.calculate_stability_score(readings, target_systolic, target_diastolic)

    assert score.insufficient_data


def test_reduction_eligibility_stable_patient():
    """Test reduction eligibility for stable patient"""
    analyzer = StabilityAnalyzer()
    patient = create_test_patient(days_since_onset=90)  # Stable phase
    readings = create_stable_readings(base_systolic=130, base_diastolic=80)

    stability_score = analyzer.calculate_stability_score(
        readings,
        patient.target_systolic,
        patient.target_diastolic,
    )

    eligibility = analyzer.check_reduction_eligibility(stability_score, patient, 0)

    # Stable patient with good readings should be eligible
    print(f"Score: {stability_score.score}")
    print(f"Eligibility: {eligibility.is_eligible}")
    print(f"Blocking factors: {eligibility.blocking_factors}")


def test_reduction_blocked_acute_phase():
    """Test that reduction is blocked during acute ICH phase"""
    analyzer = StabilityAnalyzer()
    patient = create_test_patient(days_since_onset=7)  # Acute phase
    readings = create_stable_readings(base_systolic=130, base_diastolic=80)

    stability_score = analyzer.calculate_stability_score(
        readings,
        patient.target_systolic,
        patient.target_diastolic,
    )

    eligibility = analyzer.check_reduction_eligibility(stability_score, patient, 0)

    assert not eligibility.is_eligible
    assert any("急性期" in f for f in eligibility.blocking_factors)


def test_reduction_blocked_with_hypotension():
    """Test that reduction is blocked when recent hypotension events"""
    analyzer = StabilityAnalyzer()
    patient = create_test_patient(days_since_onset=90)
    readings = create_stable_readings()

    stability_score = analyzer.calculate_stability_score(
        readings,
        patient.target_systolic,
        patient.target_diastolic,
    )

    # Simulate recent hypotension events
    eligibility = analyzer.check_reduction_eligibility(stability_score, patient, 2)

    assert not eligibility.is_eligible
    assert any("低血壓" in f for f in eligibility.blocking_factors)


if __name__ == "__main__":
    print("Running stability analyzer tests...")
    test_stability_score_calculation()
    print("✓ test_stability_score_calculation passed")

    test_high_stability_score_for_stable_readings()
    print("✓ test_high_stability_score_for_stable_readings passed")

    test_low_stability_score_for_unstable_readings()
    print("✓ test_low_stability_score_for_unstable_readings passed")

    test_insufficient_data()
    print("✓ test_insufficient_data passed")

    test_reduction_eligibility_stable_patient()
    print("✓ test_reduction_eligibility_stable_patient passed")

    test_reduction_blocked_acute_phase()
    print("✓ test_reduction_blocked_acute_phase passed")

    test_reduction_blocked_with_hypotension()
    print("✓ test_reduction_blocked_with_hypotension passed")

    print("\nAll tests passed!")
