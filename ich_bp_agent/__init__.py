"""
ICH Blood Pressure Management Agent
SMART on FHIR Application for Post-ICH Antihypertensive Medication Adjustment

This module provides:
- Stability Score calculation for ICH patients
- Medication adjustment recommendations (Norvasc/Exforge)
- Safety guardrails for clinical decision support
- SMART on FHIR integration with Taiwan MOHW Sandbox
"""

from .config import ICHConfig, SMARTConfig
from .models import (
    ICHPatient,
    ICHPhase,
    Medication,
    MedicationClass,
    DoseChange,
    StabilityScore,
    StabilityComponents,
    RecommendationType,
    MedicationRecommendation,
)

__version__ = "0.1.0"
__all__ = [
    "ICHConfig",
    "SMARTConfig",
    "ICHPatient",
    "ICHPhase",
    "Medication",
    "MedicationClass",
    "DoseChange",
    "StabilityScore",
    "StabilityComponents",
    "RecommendationType",
    "MedicationRecommendation",
]
