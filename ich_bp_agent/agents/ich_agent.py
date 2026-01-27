"""
ICH Blood Pressure Management Agent
Main orchestrator for the application
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import json

from ..models.patient import ICHPatient, ICHPhase
from ..models.medication import Medication
from ..models.stability import (
    StabilityScore,
    ReductionEligibility,
    MedicationRecommendation,
    ValidationResult,
)
from ..analyzers.stability_analyzer import StabilityAnalyzer, BPReading, parse_bp_from_fhir
from ..analyzers.medication_advisor import MedicationAdvisor
from ..safety.guardrails import SafetyGuardrails
from ..config import ich_config


class ICHBPAgent:
    """
    Main orchestrator for ICH Blood Pressure Management

    Coordinates between:
    - Stability analyzer
    - Medication advisor
    - Safety guardrails

    Usage:
        agent = ICHBPAgent()
        agent.load_patient(patient)
        agent.add_bp_reading(reading)
        report = agent.generate_report()
    """

    def __init__(self):
        self.stability_analyzer = StabilityAnalyzer()
        self.medication_advisor = MedicationAdvisor()
        self.safety_guardrails = SafetyGuardrails()

        self._patient: Optional[ICHPatient] = None
        self._bp_readings: List[BPReading] = []
        self._medications: List[Medication] = []

    def load_patient(self, patient: ICHPatient):
        """Load patient data"""
        self._patient = patient

    def set_medications(self, medications: List[Medication]):
        """Set patient medications"""
        self._medications = medications

    def add_bp_reading(self, reading: BPReading):
        """Add a new BP reading"""
        self._bp_readings.append(reading)
        # Sort by timestamp
        self._bp_readings.sort(key=lambda x: x.timestamp)

    def load_bp_readings(self, readings: List[BPReading]):
        """Load multiple BP readings"""
        self._bp_readings = sorted(readings, key=lambda x: x.timestamp)

    def load_fhir_observations(self, observations: List[dict]):
        """Load BP readings from FHIR Observation resources"""
        for obs in observations:
            reading = parse_bp_from_fhir(obs)
            if reading:
                self._bp_readings.append(reading)
        self._bp_readings.sort(key=lambda x: x.timestamp)

    def get_stability_score(self) -> StabilityScore:
        """Calculate current stability score"""
        if not self._patient:
            raise ValueError("No patient loaded")

        return self.stability_analyzer.calculate_stability_score(
            self._bp_readings,
            self._patient.target_systolic,
            self._patient.target_diastolic,
        )

    def get_reduction_eligibility(self) -> ReductionEligibility:
        """Check medication reduction eligibility"""
        if not self._patient:
            raise ValueError("No patient loaded")

        stability_score = self.get_stability_score()
        recent_hypotension = self.safety_guardrails.check_recent_hypotension(
            self._bp_readings, days=7
        )

        return self.stability_analyzer.check_reduction_eligibility(
            stability_score,
            self._patient,
            recent_hypotension,
        )

    def get_recommendation(
        self,
        medication: Optional[Medication] = None,
    ) -> MedicationRecommendation:
        """Get medication adjustment recommendation"""
        if not self._patient:
            raise ValueError("No patient loaded")

        if medication is None:
            if not self._medications:
                raise ValueError("No medications loaded")
            medication = self._medications[0]

        stability_score = self.get_stability_score()
        eligibility = self.get_reduction_eligibility()

        # Validate against safety guardrails
        safety_validation = self.safety_guardrails.validate_recommendation(
            MedicationRecommendation(
                type=RecommendationType.REDUCE_DOSE if eligibility.is_eligible else RecommendationType.MAINTAIN_CURRENT,
                medication_name=medication.name,
                current_dose=medication.current_dose,
                recommended_dose=medication.get_next_reduction_dose(),
                rationale="",
                rationale_chinese="",
                warnings=[],
                follow_up_days=14,
                requires_physician_approval=True,
                confidence=0.0,
            ),
            self._patient,
            medication,
            self._bp_readings,
        )

        return self.medication_advisor.generate_recommendation(
            self._patient,
            medication,
            stability_score,
            eligibility,
            safety_validation,
        )

    def check_current_bp_safety(self) -> Optional[ValidationResult]:
        """Check latest BP reading for safety concerns"""
        if not self._bp_readings:
            return None

        latest = max(self._bp_readings, key=lambda x: x.timestamp)
        return self.safety_guardrails.validate_current_bp(latest)

    def generate_report(self) -> Dict:
        """Generate comprehensive patient report"""
        if not self._patient:
            raise ValueError("No patient loaded")

        stability_score = self.get_stability_score()
        eligibility = self.get_reduction_eligibility()

        # Get recommendations for each medication
        recommendations = []
        for med in self._medications:
            rec = self.get_recommendation(med)
            recommendations.append(rec.to_dict())

        # Safety check
        safety_check = self.check_current_bp_safety()

        # Latest readings
        recent_readings = sorted(self._bp_readings, key=lambda x: x.timestamp)[-10:]

        return {
            "report_generated": datetime.now().isoformat(),
            "patient": self._patient.to_dict(),
            "stability_score": stability_score.to_dict(),
            "reduction_eligibility": eligibility.to_dict(),
            "medications": [m.to_dict() for m in self._medications],
            "recommendations": recommendations,
            "safety_status": safety_check.to_dict() if safety_check else None,
            "recent_readings": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "systolic": r.systolic,
                    "diastolic": r.diastolic,
                }
                for r in recent_readings
            ],
            "statistics": {
                "total_readings": len(self._bp_readings),
                "analysis_period_days": ich_config.stability_window_days,
            },
        }

    def export_report(self, output_path: str):
        """Export report to JSON file"""
        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return output_path


# Need to import this for the recommendation validation
from ..models.stability import RecommendationType
