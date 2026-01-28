"""
Stability Score Analyzer for ICH Blood Pressure Management

Calculates a 0-100 stability score based on:
- Target achievement rate (40 points)
- Blood pressure variability (30 points)
- Hypotension safety (20 points)
- Trend stability (10 points)
"""
from datetime import datetime, timedelta, date
from typing import List, Tuple, Optional
from dataclasses import dataclass
import statistics

from ..models import (
    StabilityScore,
    StabilityComponents,
    ReductionEligibility,
    TrendDirection,
)
from ..models.patient import ICHPatient, ICHPhase
from ..config import ich_config, stability_weights


@dataclass
class BPReading:
    """Simple BP reading for analysis"""
    timestamp: datetime
    systolic: int
    diastolic: int
    patient_id: str = ""
    source: str = "manual"  # "manual", "fhir", "smartwatch", etc.

    @property
    def date(self) -> date:
        return self.timestamp.date()


class StabilityAnalyzer:
    """
    Analyzes blood pressure stability for ICH patients

    The stability score helps determine:
    - When medication dose can be reduced
    - When current dose should be maintained
    - When clinic visit is needed

    Score ranges:
    - >= 80: Excellent - eligible for reduction
    - 60-79: Good - maintain current
    - 40-59: Fair - clinic visit recommended
    - < 40: Poor - urgent review needed
    """

    def __init__(self):
        self.config = ich_config
        self.weights = stability_weights

    def calculate_stability_score(
        self,
        readings: List[BPReading],
        target_systolic: Tuple[int, int],
        target_diastolic: Tuple[int, int],
        window_days: int = None,
    ) -> StabilityScore:
        """
        Calculate the stability score for a patient

        Args:
            readings: List of BP readings
            target_systolic: (min, max) target range for systolic
            target_diastolic: (min, max) target range for diastolic
            window_days: Analysis window (default: 14 days)

        Returns:
            StabilityScore with total score and components
        """
        window_days = window_days or self.config.stability_window_days
        now = datetime.now()
        cutoff = now - timedelta(days=window_days)

        # Filter readings to window (handle both offset-naive and offset-aware datetimes)
        def normalize_timestamp(ts):
            """Remove timezone info for comparison"""
            if ts.tzinfo is not None:
                return ts.replace(tzinfo=None)
            return ts

        window_readings = [r for r in readings if normalize_timestamp(r.timestamp) >= cutoff]

        # Check for insufficient data
        if len(window_readings) < self.config.min_readings_for_analysis:
            return StabilityScore(
                patient_id=readings[0].patient_id if readings else "",
                calculated_at=now,
                score=0,
                components=None,
                period_start=cutoff,
                period_end=now,
                insufficient_data=True,
                error_message=f"需要至少 {self.config.min_readings_for_analysis} 筆血壓資料進行分析",
            )

        # Sort by timestamp
        window_readings.sort(key=lambda x: x.timestamp)

        # Extract systolic values
        systolic_values = [r.systolic for r in window_readings]
        diastolic_values = [r.diastolic for r in window_readings]

        # Calculate each component
        target_score, target_rate = self._calculate_target_achievement(
            window_readings, target_systolic, target_diastolic
        )

        variability_score, cv = self._calculate_variability_score(systolic_values)

        hypotension_score, hypotension_count = self._calculate_hypotension_score(
            window_readings
        )

        trend_score, trend_direction = self._calculate_trend_score(systolic_values)

        # Calculate consecutive days on target
        consecutive_days = self._calculate_consecutive_days(
            window_readings, target_systolic, target_diastolic
        )

        # Total score
        total_score = target_score + variability_score + hypotension_score + trend_score

        # Build components
        components = StabilityComponents(
            target_achievement_rate=target_rate,
            target_achievement_score=target_score,
            variability_coefficient=cv,
            variability_score=variability_score,
            hypotension_events=hypotension_count,
            hypotension_score=hypotension_score,
            trend_direction=trend_direction,
            trend_score=trend_score,
            consecutive_days_on_target=consecutive_days,
            readings_analyzed=len(window_readings),
            mean_systolic=statistics.mean(systolic_values),
            mean_diastolic=statistics.mean(diastolic_values),
            std_systolic=statistics.stdev(systolic_values) if len(systolic_values) > 1 else 0,
        )

        return StabilityScore(
            patient_id=window_readings[0].patient_id if window_readings else "",
            calculated_at=now,
            score=total_score,
            components=components,
            period_start=window_readings[0].timestamp,
            period_end=window_readings[-1].timestamp,
        )

    def _calculate_target_achievement(
        self,
        readings: List[BPReading],
        target_systolic: Tuple[int, int],
        target_diastolic: Tuple[int, int],
    ) -> Tuple[float, float]:
        """
        Calculate target achievement score (max 40 points)

        Returns: (score, achievement_rate_percentage)
        """
        if not readings:
            return 0.0, 0.0

        on_target_count = 0
        for r in readings:
            sys_ok = target_systolic[0] <= r.systolic <= target_systolic[1]
            dia_ok = target_diastolic[0] <= r.diastolic <= target_diastolic[1]
            if sys_ok and dia_ok:
                on_target_count += 1

        rate = (on_target_count / len(readings)) * 100

        # Score calculation: linear scale
        # 100% achievement = 40 points
        # 50% achievement = 20 points
        # 0% achievement = 0 points
        score = (rate / 100) * self.weights.target_achievement_weight

        return score, rate

    def _calculate_variability_score(
        self,
        systolic_values: List[int],
    ) -> Tuple[float, float]:
        """
        Calculate variability score based on Coefficient of Variation (max 30 points)

        CV = (Standard Deviation / Mean) * 100

        Returns: (score, cv_percentage)
        """
        if len(systolic_values) < 2:
            return self.weights.variability_weight, 0.0

        mean_val = statistics.mean(systolic_values)
        std_val = statistics.stdev(systolic_values)

        if mean_val == 0:
            return 0.0, 0.0

        cv = (std_val / mean_val) * 100

        # Score calculation:
        # CV < 10% (excellent) = 30 points
        # CV 10-20% = linear interpolation
        # CV > 20% (poor) = 0 points
        if cv <= self.weights.cv_excellent:
            score = self.weights.variability_weight
        elif cv >= self.weights.cv_poor:
            score = 0.0
        else:
            # Linear interpolation between excellent and poor
            range_cv = self.weights.cv_poor - self.weights.cv_excellent
            excess_cv = cv - self.weights.cv_excellent
            score = self.weights.variability_weight * (1 - excess_cv / range_cv)

        return score, cv

    def _calculate_hypotension_score(
        self,
        readings: List[BPReading],
    ) -> Tuple[float, int]:
        """
        Calculate hypotension safety score (max 20 points)

        Deduct points for each hypotensive episode (SBP < 90)

        Returns: (score, hypotension_event_count)
        """
        hypotension_count = 0
        for r in readings:
            if r.systolic < self.config.symptomatic_hypotension_systolic:
                hypotension_count += 1

        # Deduct points per event
        penalty = hypotension_count * self.weights.hypotension_penalty_per_event
        score = max(0, self.weights.hypotension_safety_weight - penalty)

        return score, hypotension_count

    def _calculate_trend_score(
        self,
        systolic_values: List[int],
    ) -> Tuple[float, TrendDirection]:
        """
        Calculate trend stability score (max 10 points)

        Uses linear regression to determine trend direction

        Returns: (score, trend_direction)
        """
        n = len(systolic_values)
        if n < 3:
            return self.weights.trend_stability_weight / 2, TrendDirection.INSUFFICIENT_DATA

        # Simple linear regression
        x_mean = (n - 1) / 2
        y_mean = sum(systolic_values) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(systolic_values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return self.weights.trend_stability_weight, TrendDirection.STABLE

        slope = numerator / denominator

        # Determine direction based on slope
        # Slope < -0.5: improving (BP going down)
        # Slope between -0.5 and 0.5: stable
        # Slope > 0.5: worsening (BP going up)
        if slope < -0.5:
            direction = TrendDirection.IMPROVING
            score = self.weights.trend_stability_weight
        elif slope <= 0.5:
            direction = TrendDirection.STABLE
            score = self.weights.trend_stability_weight
        else:
            direction = TrendDirection.WORSENING
            # Reduce score for worsening trend
            score = self.weights.trend_stability_weight * 0.5

        return score, direction

    def _calculate_consecutive_days(
        self,
        readings: List[BPReading],
        target_systolic: Tuple[int, int],
        target_diastolic: Tuple[int, int],
    ) -> int:
        """
        Calculate consecutive days where all readings were on target

        Counts backwards from most recent reading
        """
        if not readings:
            return 0

        # Group readings by date
        readings_by_date = {}
        for r in readings:
            d = r.date
            if d not in readings_by_date:
                readings_by_date[d] = []
            readings_by_date[d].append(r)

        # Sort dates descending (most recent first)
        sorted_dates = sorted(readings_by_date.keys(), reverse=True)

        consecutive = 0
        for d in sorted_dates:
            day_readings = readings_by_date[d]
            # Check if ALL readings for this day are on target
            all_on_target = all(
                target_systolic[0] <= r.systolic <= target_systolic[1] and
                target_diastolic[0] <= r.diastolic <= target_diastolic[1]
                for r in day_readings
            )
            if all_on_target:
                consecutive += 1
            else:
                break

        return consecutive

    def check_reduction_eligibility(
        self,
        stability_score: StabilityScore,
        patient: ICHPatient,
        recent_hypotension_events: int = 0,
    ) -> ReductionEligibility:
        """
        Check if patient is eligible for medication dose reduction

        Criteria:
        1. Stability Score >= 80
        2. Consecutive days on target >= 14
        3. No hypotension events in past 7 days
        4. CV < 15%
        5. ICH phase is STABLE (not ACUTE)

        Returns:
            ReductionEligibility with eligibility status and reasons
        """
        is_eligible = True
        reasons = []
        blocking_factors = []
        warnings = []

        # Check stability score
        if stability_score.insufficient_data:
            is_eligible = False
            blocking_factors.append("資料不足，無法評估穩定度")
        elif stability_score.score < self.config.stability_excellent:
            is_eligible = False
            blocking_factors.append(
                f"穩定度分數 {stability_score.score:.1f} 低於減量門檻 ({self.config.stability_excellent})"
            )
        else:
            reasons.append(f"穩定度分數 {stability_score.score:.1f} 達到減量標準")

        # Check consecutive days
        if stability_score.components:
            consecutive = stability_score.components.consecutive_days_on_target
            if consecutive < self.config.consecutive_days_required:
                is_eligible = False
                blocking_factors.append(
                    f"連續達標天數 {consecutive} 天，未達 {self.config.consecutive_days_required} 天要求"
                )
            else:
                reasons.append(f"已連續 {consecutive} 天血壓達標")

            # Check CV
            cv = stability_score.components.variability_coefficient
            if cv > self.config.max_cv_for_reduction:
                is_eligible = False
                blocking_factors.append(
                    f"血壓變異係數 {cv:.1f}% 超過門檻 ({self.config.max_cv_for_reduction}%)"
                )
            else:
                reasons.append(f"血壓變異係數 {cv:.1f}% 在可接受範圍")

            # Check hypotension
            if stability_score.components.hypotension_events > 0:
                is_eligible = False
                blocking_factors.append(
                    f"過去 {self.config.stability_window_days} 天有 {stability_score.components.hypotension_events} 次低血壓事件"
                )

        # Check ICH phase
        if patient.ich_phase == ICHPhase.ACUTE:
            is_eligible = False
            blocking_factors.append(
                f"腦出血急性期（發病 {patient.ich_condition.days_since_onset} 天），不建議減量"
            )
        elif patient.ich_phase == ICHPhase.SUBACUTE:
            warnings.append("腦出血亞急性期，減量需謹慎評估")
        else:
            reasons.append("已進入腦出血穩定期")

        # Check recent hypotension (within 7 days)
        if recent_hypotension_events > 0:
            is_eligible = False
            blocking_factors.append(f"近 7 天有 {recent_hypotension_events} 次低血壓事件")

        return ReductionEligibility(
            is_eligible=is_eligible,
            reasons=reasons,
            blocking_factors=blocking_factors,
            warnings=warnings,
            stability_score=stability_score.score if not stability_score.insufficient_data else 0,
            consecutive_days=stability_score.components.consecutive_days_on_target if stability_score.components else 0,
            cv_percentage=stability_score.components.variability_coefficient if stability_score.components else 0,
            hypotension_events_7d=recent_hypotension_events,
            ich_phase=patient.ich_phase.value,
        )


def parse_bp_from_fhir(observation: dict) -> Optional[BPReading]:
    """
    Parse a FHIR Observation resource to BPReading

    Supports Blood Pressure Panel (LOINC 85354-9)
    """
    if observation.get("resourceType") != "Observation":
        return None

    code = observation.get("code", {}).get("coding", [{}])[0].get("code", "")
    if code != "85354-9":  # Blood pressure panel
        return None

    systolic = None
    diastolic = None

    for component in observation.get("component", []):
        comp_code = component.get("code", {}).get("coding", [{}])[0].get("code", "")
        value = component.get("valueQuantity", {}).get("value")

        if comp_code == "8480-6":  # Systolic
            systolic = int(value) if value else None
        elif comp_code == "8462-4":  # Diastolic
            diastolic = int(value) if value else None

    if systolic is None or diastolic is None:
        return None

    # Parse timestamp
    effective = observation.get("effectiveDateTime", "")
    try:
        if "+" in effective:
            timestamp = datetime.fromisoformat(effective)
        else:
            timestamp = datetime.fromisoformat(effective.replace("Z", "+00:00"))
    except Exception:
        timestamp = datetime.now()

    # Get patient ID
    patient_ref = observation.get("subject", {}).get("reference", "")
    patient_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref

    return BPReading(
        timestamp=timestamp,
        systolic=systolic,
        diastolic=diastolic,
        patient_id=patient_id,
        source="fhir"
    )
