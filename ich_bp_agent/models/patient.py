"""
ICH Patient data models
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Tuple
from enum import Enum


class ICHPhase(str, Enum):
    """ICH recovery phases based on time since onset"""
    ACUTE = "acute"           # 0-2 weeks: Strict BP control, no reduction
    SUBACUTE = "subacute"     # 2-12 weeks: Gradual stabilization
    STABLE = "stable"         # > 12 weeks: May consider dose reduction


class ICHLocation(str, Enum):
    """Common ICH locations"""
    BASAL_GANGLIA = "basal_ganglia"
    THALAMIC = "thalamic"
    LOBAR = "lobar"
    PONTINE = "pontine"
    CEREBELLAR = "cerebellar"
    OTHER = "other"


@dataclass
class ICHCondition:
    """
    ICH diagnosis information
    ICD-10: I61.x (Nontraumatic intracerebral hemorrhage)
    """
    id: str
    patient_id: str
    onset_date: date
    location: ICHLocation
    severity: str  # mild, moderate, severe
    icd_code: str = "I61.9"  # Default: unspecified
    notes: Optional[str] = None
    recorded_date: datetime = field(default_factory=datetime.now)

    @property
    def days_since_onset(self) -> int:
        """Calculate days since ICH onset"""
        return (date.today() - self.onset_date).days

    @property
    def current_phase(self) -> ICHPhase:
        """Determine current ICH phase based on days since onset"""
        days = self.days_since_onset
        if days <= 14:
            return ICHPhase.ACUTE
        elif days <= 84:  # 12 weeks
            return ICHPhase.SUBACUTE
        else:
            return ICHPhase.STABLE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "onset_date": self.onset_date.isoformat(),
            "location": self.location.value,
            "severity": self.severity,
            "icd_code": self.icd_code,
            "notes": self.notes,
            "days_since_onset": self.days_since_onset,
            "current_phase": self.current_phase.value,
        }


@dataclass
class ICHPatient:
    """
    ICH patient with personalized BP targets and medication info
    """
    patient_id: str
    name: str
    birth_date: date
    gender: str

    # ICH-specific information
    ich_condition: ICHCondition

    # Personalized BP targets (set by physician)
    target_systolic: Tuple[int, int] = (120, 140)  # (min, max)
    target_diastolic: Tuple[int, int] = (70, 90)   # (min, max)

    # Contact information
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    # Care team
    physician_id: Optional[str] = None
    physician_name: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def age(self) -> int:
        """Calculate patient age"""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def ich_phase(self) -> ICHPhase:
        """Get current ICH phase from condition"""
        return self.ich_condition.current_phase

    def is_bp_on_target(self, systolic: int, diastolic: int) -> bool:
        """Check if given BP reading is within target range"""
        sys_ok = self.target_systolic[0] <= systolic <= self.target_systolic[1]
        dia_ok = self.target_diastolic[0] <= diastolic <= self.target_diastolic[1]
        return sys_ok and dia_ok

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "birth_date": self.birth_date.isoformat(),
            "age": self.age,
            "gender": self.gender,
            "ich_condition": self.ich_condition.to_dict(),
            "ich_phase": self.ich_phase.value,
            "target_systolic": self.target_systolic,
            "target_diastolic": self.target_diastolic,
            "physician_name": self.physician_name,
        }

    def to_fhir(self) -> dict:
        """Convert to FHIR Patient resource (TW Core IG)"""
        return {
            "resourceType": "Patient",
            "id": self.patient_id,
            "meta": {
                "profile": [
                    "https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Patient-twcore"
                ]
            },
            "active": True,
            "name": [{"use": "usual", "text": self.name}],
            "gender": self.gender,
            "birthDate": self.birth_date.isoformat(),
            "telecom": [
                {"system": "phone", "value": self.phone, "use": "mobile"}
            ] if self.phone else [],
        }
