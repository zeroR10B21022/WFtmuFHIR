"""
Safety Guardrails for ICH Blood Pressure Management

Prevents dangerous actions and provides emergency alerts:
- Blocks reduction during acute ICH phase
- Alerts for hypertensive emergency (SBP > 180 or DBP > 120)
- Alerts for severe hypotension (SBP < 80)
- Warns about recent hypotensive episodes
"""
from datetime import datetime, timedelta
from typing import List, Optional

from ..models import (
    SafetyViolation,
    SafetyLevel,
    ValidationResult,
    RecommendationType,
    MedicationRecommendation,
)
from ..models.patient import ICHPatient, ICHPhase
from ..models.medication import Medication
from ..analyzers.stability_analyzer import BPReading
from ..config import ich_config


class SafetyGuardrails:
    """
    Safety mechanisms for ICH BP management

    Checks performed:
    1. Emergency thresholds (SBP > 180, DBP > 120, SBP < 80)
    2. ICH acute phase restrictions
    3. Recent hypotension events
    4. Maximum dose limits
    5. Minimum adjustment intervals

    Violation levels:
    - INFO: Informational, no action blocked
    - WARNING: Caution advised, action allowed with physician approval
    - BLOCK: Action blocked, requires physician override
    - EMERGENCY: Immediate medical attention needed
    """

    def __init__(self):
        self.config = ich_config

    def validate_current_bp(
        self,
        reading: BPReading,
    ) -> ValidationResult:
        """
        Validate a single BP reading for emergency conditions

        Args:
            reading: Current BP reading

        Returns:
            ValidationResult with any violations
        """
        violations = []

        # Check for hypertensive emergency
        if reading.systolic > self.config.hypertensive_emergency_systolic:
            violations.append(SafetyViolation(
                level=SafetyLevel.EMERGENCY,
                code="HYPERTENSIVE_EMERGENCY_SYSTOLIC",
                message=f"Hypertensive emergency: SBP {reading.systolic} mmHg > {self.config.hypertensive_emergency_systolic}",
                message_chinese=f"高血壓危象：收縮壓 {reading.systolic} mmHg 超過 {self.config.hypertensive_emergency_systolic} mmHg，請立即就醫",
                details={"systolic": reading.systolic, "threshold": self.config.hypertensive_emergency_systolic},
            ))

        if reading.diastolic > self.config.hypertensive_emergency_diastolic:
            violations.append(SafetyViolation(
                level=SafetyLevel.EMERGENCY,
                code="HYPERTENSIVE_EMERGENCY_DIASTOLIC",
                message=f"Hypertensive emergency: DBP {reading.diastolic} mmHg > {self.config.hypertensive_emergency_diastolic}",
                message_chinese=f"高血壓危象：舒張壓 {reading.diastolic} mmHg 超過 {self.config.hypertensive_emergency_diastolic} mmHg，請立即就醫",
                details={"diastolic": reading.diastolic, "threshold": self.config.hypertensive_emergency_diastolic},
            ))

        # Check for severe hypotension
        if reading.systolic < self.config.severe_hypotension_systolic:
            violations.append(SafetyViolation(
                level=SafetyLevel.EMERGENCY,
                code="SEVERE_HYPOTENSION",
                message=f"Severe hypotension: SBP {reading.systolic} mmHg < {self.config.severe_hypotension_systolic}",
                message_chinese=f"嚴重低血壓：收縮壓 {reading.systolic} mmHg 低於 {self.config.severe_hypotension_systolic} mmHg，請立即就醫",
                details={"systolic": reading.systolic, "threshold": self.config.severe_hypotension_systolic},
            ))

        # Check for symptomatic hypotension threshold
        elif reading.systolic < self.config.symptomatic_hypotension_systolic:
            violations.append(SafetyViolation(
                level=SafetyLevel.WARNING,
                code="SYMPTOMATIC_HYPOTENSION_RISK",
                message=f"Hypotension risk: SBP {reading.systolic} mmHg < {self.config.symptomatic_hypotension_systolic}",
                message_chinese=f"低血壓風險：收縮壓 {reading.systolic} mmHg 偏低，請注意頭暈等症狀",
                details={"systolic": reading.systolic, "threshold": self.config.symptomatic_hypotension_systolic},
            ))

        return ValidationResult(
            is_valid=not any(v.level in {SafetyLevel.EMERGENCY, SafetyLevel.BLOCK} for v in violations),
            violations=violations,
        )

    def validate_recommendation(
        self,
        recommendation: MedicationRecommendation,
        patient: ICHPatient,
        medication: Medication,
        recent_readings: List[BPReading],
    ) -> ValidationResult:
        """
        Validate a medication recommendation against safety rules

        Args:
            recommendation: Proposed recommendation
            patient: ICH patient
            medication: Current medication
            recent_readings: Recent BP readings (last 7 days)

        Returns:
            ValidationResult with any violations
        """
        violations = []

        # Check latest reading for emergency
        if recent_readings:
            latest = max(recent_readings, key=lambda x: x.timestamp)
            bp_validation = self.validate_current_bp(latest)
            violations.extend(bp_validation.violations)

        # For dose reduction, apply stricter checks
        if recommendation.type == RecommendationType.REDUCE_DOSE:
            # Check acute phase
            if patient.ich_phase == ICHPhase.ACUTE:
                violations.append(SafetyViolation(
                    level=SafetyLevel.BLOCK,
                    code="ACUTE_PHASE_REDUCTION",
                    message=f"Cannot reduce medication during acute ICH phase (day {patient.ich_condition.days_since_onset})",
                    message_chinese=f"腦出血急性期（發病第 {patient.ich_condition.days_since_onset} 天）不可減量，需等待至少 {self.config.acute_phase_days} 天",
                    details={
                        "days_since_onset": patient.ich_condition.days_since_onset,
                        "acute_phase_days": self.config.acute_phase_days,
                    },
                ))

            # Check for recent hypotension
            hypotension_readings = [
                r for r in recent_readings
                if r.systolic < self.config.symptomatic_hypotension_systolic
            ]
            if hypotension_readings:
                violations.append(SafetyViolation(
                    level=SafetyLevel.BLOCK,
                    code="RECENT_HYPOTENSION",
                    message=f"Recent hypotensive episodes ({len(hypotension_readings)}) detected",
                    message_chinese=f"近期有 {len(hypotension_readings)} 次低血壓事件，不建議減量",
                    details={
                        "hypotension_count": len(hypotension_readings),
                        "readings": [
                            {"timestamp": r.timestamp.isoformat(), "systolic": r.systolic}
                            for r in hypotension_readings
                        ],
                    },
                ))

            # Check if already at minimum dose
            if medication.is_at_minimum_dose():
                violations.append(SafetyViolation(
                    level=SafetyLevel.BLOCK,
                    code="MINIMUM_DOSE_REACHED",
                    message=f"Already at minimum dose ({medication.current_dose})",
                    message_chinese=f"已達最低劑量 ({medication.current_dose})，無法再減量",
                    details={"current_dose": medication.current_dose},
                ))

            # Warn about subacute phase
            if patient.ich_phase == ICHPhase.SUBACUTE:
                violations.append(SafetyViolation(
                    level=SafetyLevel.WARNING,
                    code="SUBACUTE_PHASE_CAUTION",
                    message="Subacute ICH phase - dose reduction requires extra caution",
                    message_chinese=f"腦出血亞急性期（發病第 {patient.ich_condition.days_since_onset} 天），減量需謹慎評估",
                    details={"days_since_onset": patient.ich_condition.days_since_onset},
                ))

        # For dose increase
        elif recommendation.type == RecommendationType.INCREASE_DOSE:
            if medication.is_at_maximum_dose():
                violations.append(SafetyViolation(
                    level=SafetyLevel.BLOCK,
                    code="MAXIMUM_DOSE_REACHED",
                    message=f"Already at maximum dose ({medication.current_dose})",
                    message_chinese=f"已達最高劑量 ({medication.current_dose})，無法再增量",
                    details={"current_dose": medication.current_dose},
                ))

        return ValidationResult(
            is_valid=not any(v.level in {SafetyLevel.EMERGENCY, SafetyLevel.BLOCK} for v in violations),
            violations=violations,
        )

    def check_recent_hypotension(
        self,
        readings: List[BPReading],
        days: int = 7,
    ) -> int:
        """
        Count hypotensive episodes in recent days

        Args:
            readings: BP readings
            days: Lookback period

        Returns:
            Number of hypotensive episodes
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in readings if r.timestamp >= cutoff]

        count = sum(
            1 for r in recent
            if r.systolic < self.config.symptomatic_hypotension_systolic
        )

        return count

    def get_alert_level(self, reading: BPReading) -> str:
        """
        Get alert level for a BP reading

        Returns:
            "emergency", "warning", "caution", or "normal"
        """
        if reading.systolic > self.config.hypertensive_emergency_systolic or \
           reading.diastolic > self.config.hypertensive_emergency_diastolic or \
           reading.systolic < self.config.severe_hypotension_systolic:
            return "emergency"

        if reading.systolic < self.config.symptomatic_hypotension_systolic:
            return "warning"

        if reading.systolic > 150 or reading.diastolic > 100:
            return "caution"

        return "normal"

    def get_alert_message(self, reading: BPReading) -> Optional[str]:
        """
        Get alert message for a BP reading

        Returns:
            Alert message in Chinese, or None if normal
        """
        level = self.get_alert_level(reading)

        if level == "emergency":
            if reading.systolic > self.config.hypertensive_emergency_systolic:
                return f"緊急！收縮壓 {reading.systolic} mmHg 過高，請立即就醫"
            if reading.diastolic > self.config.hypertensive_emergency_diastolic:
                return f"緊急！舒張壓 {reading.diastolic} mmHg 過高，請立即就醫"
            if reading.systolic < self.config.severe_hypotension_systolic:
                return f"緊急！收縮壓 {reading.systolic} mmHg 過低，請立即就醫"

        if level == "warning":
            return f"注意！收縮壓 {reading.systolic} mmHg 偏低，請留意頭暈等症狀"

        if level == "caution":
            if reading.systolic > 150:
                return f"提醒：收縮壓 {reading.systolic} mmHg 偏高，請持續監測"
            if reading.diastolic > 100:
                return f"提醒：舒張壓 {reading.diastolic} mmHg 偏高，請持續監測"

        return None
