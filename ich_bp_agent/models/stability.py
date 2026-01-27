"""
Stability Score and Recommendation models for ICH Blood Pressure Management
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TrendDirection(str, Enum):
    """Blood pressure trend direction"""
    IMPROVING = "improving"      # BP trending down toward target
    STABLE = "stable"            # BP stable within target
    WORSENING = "worsening"      # BP trending up or becoming erratic
    INSUFFICIENT_DATA = "insufficient_data"


class RecommendationType(str, Enum):
    """Types of medication recommendations"""
    REDUCE_DOSE = "reduce_dose"
    MAINTAIN_CURRENT = "maintain_current"
    INCREASE_DOSE = "increase_dose"
    CLINIC_VISIT = "clinic_visit"
    URGENT_REVIEW = "urgent_review"
    EMERGENCY = "emergency"


class SafetyLevel(str, Enum):
    """Safety violation levels"""
    INFO = "info"
    WARNING = "warning"
    BLOCK = "block"
    EMERGENCY = "emergency"


@dataclass
class StabilityComponents:
    """
    Individual components of the stability score

    Total possible: 100 points
    - Target achievement: 40 points
    - Variability (CV): 30 points
    - Hypotension safety: 20 points
    - Trend stability: 10 points
    """
    # Target achievement (0-40 points)
    target_achievement_rate: float  # Percentage of readings on target
    target_achievement_score: float

    # Variability (0-30 points)
    variability_coefficient: float  # CV% of systolic BP
    variability_score: float

    # Hypotension safety (0-20 points)
    hypotension_events: int
    hypotension_score: float

    # Trend (0-10 points)
    trend_direction: TrendDirection
    trend_score: float

    # Additional metrics
    consecutive_days_on_target: int
    readings_analyzed: int
    mean_systolic: float
    mean_diastolic: float
    std_systolic: float

    def to_dict(self) -> dict:
        return {
            "target_achievement_rate": round(self.target_achievement_rate, 1),
            "target_achievement_score": round(self.target_achievement_score, 1),
            "variability_coefficient": round(self.variability_coefficient, 2),
            "variability_score": round(self.variability_score, 1),
            "hypotension_events": self.hypotension_events,
            "hypotension_score": round(self.hypotension_score, 1),
            "trend_direction": self.trend_direction.value,
            "trend_score": round(self.trend_score, 1),
            "consecutive_days_on_target": self.consecutive_days_on_target,
            "readings_analyzed": self.readings_analyzed,
            "mean_systolic": round(self.mean_systolic, 1),
            "mean_diastolic": round(self.mean_diastolic, 1),
            "std_systolic": round(self.std_systolic, 2),
        }


@dataclass
class StabilityScore:
    """
    Overall stability score for an ICH patient

    Score interpretation:
    - >= 80: Excellent - eligible for dose reduction
    - 60-79: Good - maintain current dose
    - 40-59: Fair - recommend clinic visit
    - < 40: Poor - urgent review needed
    """
    patient_id: str
    calculated_at: datetime
    score: float  # 0-100
    components: StabilityComponents
    period_start: datetime
    period_end: datetime

    # Flags
    insufficient_data: bool = False
    error_message: Optional[str] = None

    @property
    def category(self) -> str:
        """Get score category"""
        if self.insufficient_data:
            return "insufficient_data"
        if self.score >= 80:
            return "excellent"
        elif self.score >= 60:
            return "good"
        elif self.score >= 40:
            return "fair"
        else:
            return "poor"

    @property
    def category_chinese(self) -> str:
        """Get score category in Chinese"""
        mapping = {
            "insufficient_data": "資料不足",
            "excellent": "優良",
            "good": "良好",
            "fair": "普通",
            "poor": "需注意",
        }
        return mapping.get(self.category, "未知")

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "calculated_at": self.calculated_at.isoformat(),
            "score": round(self.score, 1),
            "category": self.category,
            "category_chinese": self.category_chinese,
            "components": self.components.to_dict() if self.components else None,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "insufficient_data": self.insufficient_data,
        }


@dataclass
class ReductionEligibility:
    """
    Eligibility assessment for medication dose reduction

    Criteria:
    1. Stability Score >= 80
    2. Consecutive days on target >= 14
    3. No hypotension events in past 7 days
    4. CV < 15%
    5. ICH phase is STABLE (not ACUTE)
    """
    is_eligible: bool
    reasons: List[str]  # Why eligible or not
    blocking_factors: List[str]  # Factors preventing reduction
    warnings: List[str]  # Non-blocking concerns
    stability_score: float
    consecutive_days: int
    cv_percentage: float
    hypotension_events_7d: int
    ich_phase: str

    def to_dict(self) -> dict:
        return {
            "is_eligible": self.is_eligible,
            "reasons": self.reasons,
            "blocking_factors": self.blocking_factors,
            "warnings": self.warnings,
            "stability_score": round(self.stability_score, 1),
            "consecutive_days": self.consecutive_days,
            "cv_percentage": round(self.cv_percentage, 2),
            "hypotension_events_7d": self.hypotension_events_7d,
            "ich_phase": self.ich_phase,
        }


@dataclass
class SafetyViolation:
    """A safety guardrail violation or warning"""
    level: SafetyLevel
    code: str
    message: str
    message_chinese: str
    details: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "code": self.code,
            "message": self.message,
            "message_chinese": self.message_chinese,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ValidationResult:
    """Result of safety guardrail validation"""
    is_valid: bool
    violations: List[SafetyViolation]

    @property
    def has_blocking_violations(self) -> bool:
        return any(v.level in {SafetyLevel.BLOCK, SafetyLevel.EMERGENCY}
                   for v in self.violations)

    @property
    def has_emergency(self) -> bool:
        return any(v.level == SafetyLevel.EMERGENCY for v in self.violations)

    @property
    def warnings(self) -> List[SafetyViolation]:
        return [v for v in self.violations if v.level == SafetyLevel.WARNING]

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "has_emergency": self.has_emergency,
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class MedicationRecommendation:
    """
    Medication adjustment recommendation

    Generated by the medication advisor based on:
    - Stability score
    - Safety guardrails
    - Current medication status
    """
    type: RecommendationType
    medication_name: str
    current_dose: str
    recommended_dose: Optional[str]
    rationale: str
    rationale_chinese: str
    warnings: List[str]
    follow_up_days: int
    requires_physician_approval: bool
    confidence: float  # 0-1, how confident in this recommendation
    generated_at: datetime = field(default_factory=datetime.now)

    # Supporting data
    stability_score: Optional[float] = None
    safety_validation: Optional[ValidationResult] = None

    @property
    def type_chinese(self) -> str:
        """Get recommendation type in Chinese"""
        mapping = {
            RecommendationType.REDUCE_DOSE: "建議減量",
            RecommendationType.MAINTAIN_CURRENT: "建議維持",
            RecommendationType.INCREASE_DOSE: "建議增量",
            RecommendationType.CLINIC_VISIT: "建議回診",
            RecommendationType.URGENT_REVIEW: "需緊急評估",
            RecommendationType.EMERGENCY: "緊急狀況",
        }
        return mapping.get(self.type, "未知")

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "type_chinese": self.type_chinese,
            "medication_name": self.medication_name,
            "current_dose": self.current_dose,
            "recommended_dose": self.recommended_dose,
            "rationale": self.rationale,
            "rationale_chinese": self.rationale_chinese,
            "warnings": self.warnings,
            "follow_up_days": self.follow_up_days,
            "requires_physician_approval": self.requires_physician_approval,
            "confidence": round(self.confidence, 2),
            "generated_at": self.generated_at.isoformat(),
            "stability_score": self.stability_score,
        }
