"""
Medication Advisor for ICH Blood Pressure Management

Provides dose adjustment recommendations based on:
- Stability score
- Current medication
- Safety guardrails
- ICH phase
"""
from datetime import datetime
from typing import Optional, List

from ..models import (
    StabilityScore,
    ReductionEligibility,
    RecommendationType,
    MedicationRecommendation,
    ValidationResult,
)
from ..models.patient import ICHPatient, ICHPhase
from ..models.medication import Medication, MedicationClass
from ..config import ich_config, medication_config


class MedicationAdvisor:
    """
    Provides medication adjustment recommendations for ICH patients

    Supported medications:
    - Norvasc (Amlodipine): CCB, doses 2.5mg, 5mg, 10mg
    - Exforge (Valsartan/Amlodipine): ARB+CCB, doses 80/5mg, 160/5mg, 160/10mg

    Recommendation types:
    - REDUCE_DOSE: Patient stable, can reduce
    - MAINTAIN_CURRENT: Keep current dose
    - INCREASE_DOSE: BP not controlled (rare, requires physician)
    - CLINIC_VISIT: Need in-person evaluation
    - URGENT_REVIEW: Significant concern
    - EMERGENCY: Immediate attention needed
    """

    def __init__(self):
        self.config = ich_config
        self.med_config = medication_config

    def generate_recommendation(
        self,
        patient: ICHPatient,
        medication: Medication,
        stability_score: StabilityScore,
        eligibility: ReductionEligibility,
        safety_validation: Optional[ValidationResult] = None,
    ) -> MedicationRecommendation:
        """
        Generate medication adjustment recommendation

        Args:
            patient: ICH patient
            medication: Current medication
            stability_score: Calculated stability score
            eligibility: Reduction eligibility assessment
            safety_validation: Safety guardrail validation result

        Returns:
            MedicationRecommendation with action and rationale
        """
        # Check for emergency first
        if safety_validation and safety_validation.has_emergency:
            return self._emergency_recommendation(medication, safety_validation)

        # Check for safety blocks
        if safety_validation and safety_validation.has_blocking_violations:
            return self._blocked_recommendation(medication, safety_validation)

        # Check if data is insufficient
        if stability_score.insufficient_data:
            return self._insufficient_data_recommendation(medication)

        # Determine recommendation based on stability score
        score = stability_score.score

        if score >= self.config.stability_excellent and eligibility.is_eligible:
            return self._reduction_recommendation(patient, medication, stability_score, eligibility)

        elif score >= self.config.stability_good:
            return self._maintenance_recommendation(patient, medication, stability_score)

        elif score >= self.config.stability_fair:
            return self._clinic_visit_recommendation(patient, medication, stability_score)

        else:
            return self._urgent_review_recommendation(patient, medication, stability_score)

    def _reduction_recommendation(
        self,
        patient: ICHPatient,
        medication: Medication,
        stability_score: StabilityScore,
        eligibility: ReductionEligibility,
    ) -> MedicationRecommendation:
        """Generate dose reduction recommendation"""
        next_dose = medication.get_next_reduction_dose()

        if next_dose is None:
            # Already at minimum dose
            return MedicationRecommendation(
                type=RecommendationType.MAINTAIN_CURRENT,
                medication_name=medication.name,
                current_dose=medication.current_dose,
                recommended_dose=None,
                rationale="Patient already at minimum dose, maintaining current treatment",
                rationale_chinese=f"病人已使用最低劑量 ({medication.current_dose})，建議維持目前治療",
                warnings=["已達最低劑量，無法再減量"],
                follow_up_days=14,
                requires_physician_approval=False,
                confidence=0.9,
                stability_score=stability_score.score,
            )

        # Check days on current dose
        if medication.days_on_current_dose < self.med_config.min_days_between_adjustments:
            return MedicationRecommendation(
                type=RecommendationType.MAINTAIN_CURRENT,
                medication_name=medication.name,
                current_dose=medication.current_dose,
                recommended_dose=None,
                rationale=f"Too soon since last adjustment ({medication.days_on_current_dose} days)",
                rationale_chinese=f"距離上次調整僅 {medication.days_on_current_dose} 天，建議再觀察 {self.med_config.min_days_between_adjustments - medication.days_on_current_dose} 天",
                warnings=["調整間隔過短"],
                follow_up_days=self.med_config.min_days_between_adjustments - medication.days_on_current_dose,
                requires_physician_approval=False,
                confidence=0.85,
                stability_score=stability_score.score,
            )

        # Generate reduction recommendation
        warnings = []
        if patient.ich_phase == ICHPhase.SUBACUTE:
            warnings.append("腦出血亞急性期，減量需謹慎")

        return MedicationRecommendation(
            type=RecommendationType.REDUCE_DOSE,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=next_dose,
            rationale=f"Stability score {stability_score.score:.0f}/100, {eligibility.consecutive_days} consecutive days on target",
            rationale_chinese=f"穩定度分數 {stability_score.score:.0f}/100 達標，連續 {eligibility.consecutive_days} 天血壓達標，建議減量",
            warnings=warnings + eligibility.warnings,
            follow_up_days=self.med_config.post_reduction_monitoring_days,
            requires_physician_approval=True,  # Always require physician approval for reduction
            confidence=0.85,
            stability_score=stability_score.score,
        )

    def _maintenance_recommendation(
        self,
        patient: ICHPatient,
        medication: Medication,
        stability_score: StabilityScore,
    ) -> MedicationRecommendation:
        """Generate maintenance recommendation"""
        components = stability_score.components

        reasons = []
        if components:
            if components.target_achievement_rate < 80:
                reasons.append(f"目標達成率 {components.target_achievement_rate:.0f}%")
            if components.variability_coefficient > 12:
                reasons.append(f"血壓變異性 {components.variability_coefficient:.1f}%")

        reason_text = "、".join(reasons) if reasons else "血壓控制尚可"

        return MedicationRecommendation(
            type=RecommendationType.MAINTAIN_CURRENT,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale=f"Stability score {stability_score.score:.0f}/100, maintain current dose",
            rationale_chinese=f"穩定度分數 {stability_score.score:.0f}/100，{reason_text}，建議維持目前劑量",
            warnings=[],
            follow_up_days=14,
            requires_physician_approval=False,
            confidence=0.9,
            stability_score=stability_score.score,
        )

    def _clinic_visit_recommendation(
        self,
        patient: ICHPatient,
        medication: Medication,
        stability_score: StabilityScore,
    ) -> MedicationRecommendation:
        """Generate clinic visit recommendation"""
        components = stability_score.components
        concerns = []

        if components:
            if components.target_achievement_rate < 60:
                concerns.append(f"血壓達標率偏低 ({components.target_achievement_rate:.0f}%)")
            if components.hypotension_events > 0:
                concerns.append(f"有 {components.hypotension_events} 次低血壓事件")
            if components.variability_coefficient > 15:
                concerns.append(f"血壓波動較大 (CV {components.variability_coefficient:.1f}%)")

        concern_text = "；".join(concerns) if concerns else "血壓控制不理想"

        return MedicationRecommendation(
            type=RecommendationType.CLINIC_VISIT,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale=f"Stability score {stability_score.score:.0f}/100, clinical evaluation recommended",
            rationale_chinese=f"穩定度分數 {stability_score.score:.0f}/100，{concern_text}，建議回診評估",
            warnings=concerns,
            follow_up_days=7,
            requires_physician_approval=True,
            confidence=0.8,
            stability_score=stability_score.score,
        )

    def _urgent_review_recommendation(
        self,
        patient: ICHPatient,
        medication: Medication,
        stability_score: StabilityScore,
    ) -> MedicationRecommendation:
        """Generate urgent review recommendation"""
        return MedicationRecommendation(
            type=RecommendationType.URGENT_REVIEW,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale=f"Stability score {stability_score.score:.0f}/100, urgent clinical review needed",
            rationale_chinese=f"穩定度分數 {stability_score.score:.0f}/100 偏低，血壓控制不佳，需緊急評估用藥方案",
            warnings=["血壓控制不佳", "建議盡速回診"],
            follow_up_days=3,
            requires_physician_approval=True,
            confidence=0.75,
            stability_score=stability_score.score,
        )

    def _emergency_recommendation(
        self,
        medication: Medication,
        safety_validation: ValidationResult,
    ) -> MedicationRecommendation:
        """Generate emergency recommendation"""
        emergency_violations = [v for v in safety_validation.violations if v.level.value == "emergency"]
        messages = [v.message_chinese for v in emergency_violations]

        return MedicationRecommendation(
            type=RecommendationType.EMERGENCY,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale="Emergency safety condition detected",
            rationale_chinese="偵測到緊急狀況：" + "；".join(messages),
            warnings=messages,
            follow_up_days=0,
            requires_physician_approval=True,
            confidence=1.0,
            safety_validation=safety_validation,
        )

    def _blocked_recommendation(
        self,
        medication: Medication,
        safety_validation: ValidationResult,
    ) -> MedicationRecommendation:
        """Generate recommendation when blocked by safety guardrails"""
        blocking_violations = [v for v in safety_validation.violations if v.level.value == "block"]
        messages = [v.message_chinese for v in blocking_violations]

        return MedicationRecommendation(
            type=RecommendationType.MAINTAIN_CURRENT,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale="Action blocked by safety guardrails",
            rationale_chinese="安全護欄阻擋：" + "；".join(messages),
            warnings=messages,
            follow_up_days=7,
            requires_physician_approval=True,
            confidence=0.95,
            safety_validation=safety_validation,
        )

    def _insufficient_data_recommendation(
        self,
        medication: Medication,
    ) -> MedicationRecommendation:
        """Generate recommendation when data is insufficient"""
        return MedicationRecommendation(
            type=RecommendationType.MAINTAIN_CURRENT,
            medication_name=medication.name,
            current_dose=medication.current_dose,
            recommended_dose=None,
            rationale="Insufficient data for stability assessment",
            rationale_chinese=f"血壓資料不足，無法評估穩定度，建議維持目前劑量並持續記錄血壓",
            warnings=["請每日測量血壓至少兩次（早晚各一次）"],
            follow_up_days=7,
            requires_physician_approval=False,
            confidence=0.5,
        )

    def get_dose_steps(self, medication_name: str) -> List[str]:
        """Get available dose steps for a medication"""
        name = medication_name.lower()
        if name == "norvasc":
            return ["2.5mg", "5mg", "10mg"]
        elif name == "exforge":
            return ["80/5mg", "160/5mg", "160/10mg"]
        return []
