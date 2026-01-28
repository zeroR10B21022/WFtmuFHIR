"""
Configuration for ICH Blood Pressure Management Agent
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict, Tuple, List, Optional
from enum import Enum
import os
from pathlib import Path

# Check if running on Streamlit Cloud
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class ICHPhase(str, Enum):
    """ICH recovery phases"""
    ACUTE = "acute"           # 0-2 weeks post-ICH
    SUBACUTE = "subacute"     # 2-12 weeks post-ICH
    STABLE = "stable"         # > 12 weeks post-ICH


class ICHConfig(BaseSettings):
    """
    ICH-specific configuration for blood pressure management
    """
    # Default target BP ranges (can be overridden per patient)
    default_target_systolic: Tuple[int, int] = (120, 140)
    default_target_diastolic: Tuple[int, int] = (70, 90)

    # Stability score thresholds
    stability_excellent: int = 80  # Score >= 80: eligible for reduction
    stability_good: int = 60       # Score 60-79: maintain current dose
    stability_fair: int = 40       # Score 40-59: clinic visit recommended
    # Score < 40: urgent review needed

    # Analysis windows
    stability_window_days: int = 14  # Days for stability calculation
    trend_window_days: int = 7       # Days for trend analysis
    min_readings_for_analysis: int = 7  # Minimum BP readings required

    # Reduction eligibility criteria
    consecutive_days_required: int = 14  # Days on target before reduction
    max_cv_for_reduction: float = 15.0   # Maximum CV% for reduction eligibility
    hypotension_lookback_days: int = 7   # Days to check for hypotension events

    # Alert thresholds
    hypertensive_emergency_systolic: int = 180
    hypertensive_emergency_diastolic: int = 120
    severe_hypotension_systolic: int = 80
    symptomatic_hypotension_systolic: int = 90

    # Phase durations (days from ICH onset)
    acute_phase_days: int = 14
    subacute_phase_days: int = 84  # 12 weeks

    model_config = SettingsConfigDict(
        env_prefix="ICH_BP_",
        extra="ignore"
    )


class MedicationConfig(BaseSettings):
    """
    Medication-specific configuration for Norvasc and Exforge
    """
    # Norvasc (Amlodipine) - CCB
    norvasc_doses: List[float] = [2.5, 5.0, 10.0]  # mg
    norvasc_min_dose: float = 2.5
    norvasc_max_dose: float = 10.0

    # Exforge (Valsartan/Amlodipine) - ARB + CCB combo
    # Format: (valsartan_mg, amlodipine_mg)
    exforge_doses: List[Tuple[int, int]] = [(80, 5), (160, 5), (160, 10)]
    exforge_min_dose: Tuple[int, int] = (80, 5)
    exforge_max_dose: Tuple[int, int] = (160, 10)

    # Dose adjustment rules
    min_days_between_adjustments: int = 14  # Wait at least 2 weeks
    post_reduction_monitoring_days: int = 7  # Close monitoring after reduction

    model_config = SettingsConfigDict(
        env_prefix="ICH_MED_",
        extra="ignore"
    )


class SMARTConfig(BaseSettings):
    """
    SMART on FHIR configuration for Taiwan MOHW Sandbox

    Reads from Streamlit Cloud secrets if available, otherwise falls back to .env
    """
    # FHIR Server
    fhir_base_url: str = "https://hapi.fhir.tw/fhir"

    # OAuth 2.0 settings
    client_id: str = ""  # Set via environment variable or .env file
    client_secret: Optional[str] = None  # For confidential clients
    redirect_uri: str = "http://localhost:8501/callback"

    # SMART scopes for Provider Standalone Launch
    # Taiwan MOHW pattern: NO "launch/patient" or "launch" scopes
    # User selects patient during OAuth flow
    scopes: List[str] = [
        "openid",
        "fhirUser",
        "patient/Patient.read",
        "patient/Observation.read",
        "patient/Observation.write",
        "patient/MedicationRequest.read",
        "patient/MedicationAdministration.read",
        "patient/Condition.read",
    ]

    # Token settings
    token_refresh_margin_seconds: int = 300  # Refresh 5 min before expiry

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_prefix="SMART_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        # Check for Streamlit Cloud secrets first
        if HAS_STREAMLIT and hasattr(st, 'secrets') and 'smart' in st.secrets:
            secrets = st.secrets.smart
            kwargs.setdefault('fhir_base_url', secrets.get('SMART_FHIR_BASE_URL', kwargs.get('fhir_base_url')))
            kwargs.setdefault('client_id', secrets.get('SMART_CLIENT_ID', kwargs.get('client_id', '')))
            kwargs.setdefault('redirect_uri', secrets.get('SMART_REDIRECT_URI', kwargs.get('redirect_uri')))
        super().__init__(**kwargs)


class StabilityScoreWeights(BaseSettings):
    """
    Weights for stability score components (total = 100)
    """
    target_achievement_weight: int = 40
    variability_weight: int = 30
    hypotension_safety_weight: int = 20
    trend_stability_weight: int = 10

    # Variability thresholds
    cv_excellent: float = 10.0  # CV < 10% = full points
    cv_poor: float = 20.0       # CV > 20% = 0 points

    # Hypotension penalty
    hypotension_penalty_per_event: int = 5  # Points deducted per event

    model_config = SettingsConfigDict(
        env_prefix="STABILITY_",
        extra="ignore"
    )


# Global configuration instances
ich_config = ICHConfig()
medication_config = MedicationConfig()
smart_config = SMARTConfig()
stability_weights = StabilityScoreWeights()
