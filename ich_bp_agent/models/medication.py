"""
Medication data models for ICH Blood Pressure Management
Supports Norvasc (Amlodipine) and Exforge (Valsartan/Amlodipine)
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Tuple, Union
from enum import Enum


class MedicationClass(str, Enum):
    """Antihypertensive drug classes"""
    CCB = "ccb"                    # Calcium Channel Blocker
    ARB = "arb"                    # Angiotensin II Receptor Blocker
    ARB_CCB_COMBO = "arb_ccb"      # Combination ARB + CCB
    ACE_INHIBITOR = "acei"
    BETA_BLOCKER = "bb"
    DIURETIC = "diuretic"
    OTHER = "other"


class DoseChangeReason(str, Enum):
    """Reasons for dose adjustment"""
    INITIAL_PRESCRIPTION = "initial"
    BP_WELL_CONTROLLED = "well_controlled"      # Reduction
    BP_ABOVE_TARGET = "above_target"            # Increase
    HYPOTENSION_EVENT = "hypotension"           # Reduction
    SIDE_EFFECTS = "side_effects"               # Change/reduction
    PHYSICIAN_DECISION = "physician_decision"
    PATIENT_REQUEST = "patient_request"


@dataclass
class DoseChange:
    """Record of a dose adjustment"""
    id: str
    medication_id: str
    change_date: date
    previous_dose: str
    new_dose: str
    reason: DoseChangeReason
    ordered_by: Optional[str] = None  # Physician ID
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "medication_id": self.medication_id,
            "change_date": self.change_date.isoformat(),
            "previous_dose": self.previous_dose,
            "new_dose": self.new_dose,
            "reason": self.reason.value,
            "ordered_by": self.ordered_by,
            "notes": self.notes,
        }


@dataclass
class Medication:
    """
    Medication record for antihypertensive drugs

    Supported medications:
    - Norvasc (脈優): Amlodipine 2.5mg, 5mg, 10mg
    - Exforge (易安穩): Valsartan/Amlodipine 80/5mg, 160/5mg, 160/10mg
    """
    id: str
    patient_id: str
    name: str               # "Norvasc" or "Exforge"
    generic_name: str       # "Amlodipine" or "Valsartan/Amlodipine"
    drug_class: MedicationClass
    current_dose: str       # "5mg" or "160/10mg"
    frequency: str          # "QD", "BID", etc.
    timing: str             # "morning", "evening", "morning and evening"
    start_date: date
    is_active: bool = True
    dose_history: List[DoseChange] = field(default_factory=list)
    notes: Optional[str] = None

    # RxNorm codes for FHIR compatibility
    rxnorm_code: Optional[str] = None

    @property
    def dose_numeric(self) -> Union[float, Tuple[int, int]]:
        """Extract numeric dose value"""
        dose_str = self.current_dose.lower().replace("mg", "").strip()
        if "/" in dose_str:
            # Combo drug like Exforge
            parts = dose_str.split("/")
            return (int(parts[0]), int(parts[1]))
        else:
            return float(dose_str)

    @property
    def days_on_current_dose(self) -> int:
        """Days since last dose change"""
        if self.dose_history:
            last_change = max(self.dose_history, key=lambda x: x.change_date)
            return (date.today() - last_change.change_date).days
        return (date.today() - self.start_date).days

    def get_next_reduction_dose(self) -> Optional[str]:
        """Get the next lower dose step"""
        if self.name.lower() == "norvasc":
            doses = ["2.5mg", "5mg", "10mg"]
            current_idx = None
            for i, d in enumerate(doses):
                if d == self.current_dose:
                    current_idx = i
                    break
            if current_idx and current_idx > 0:
                return doses[current_idx - 1]
            return None  # Already at minimum

        elif self.name.lower() == "exforge":
            doses = ["80/5mg", "160/5mg", "160/10mg"]
            current_idx = None
            for i, d in enumerate(doses):
                if d == self.current_dose:
                    current_idx = i
                    break
            if current_idx and current_idx > 0:
                return doses[current_idx - 1]
            return None

        return None

    def get_next_increase_dose(self) -> Optional[str]:
        """Get the next higher dose step"""
        if self.name.lower() == "norvasc":
            doses = ["2.5mg", "5mg", "10mg"]
            current_idx = None
            for i, d in enumerate(doses):
                if d == self.current_dose:
                    current_idx = i
                    break
            if current_idx is not None and current_idx < len(doses) - 1:
                return doses[current_idx + 1]
            return None

        elif self.name.lower() == "exforge":
            doses = ["80/5mg", "160/5mg", "160/10mg"]
            current_idx = None
            for i, d in enumerate(doses):
                if d == self.current_dose:
                    current_idx = i
                    break
            if current_idx is not None and current_idx < len(doses) - 1:
                return doses[current_idx + 1]
            return None

        return None

    def is_at_minimum_dose(self) -> bool:
        """Check if at minimum dose"""
        return self.get_next_reduction_dose() is None

    def is_at_maximum_dose(self) -> bool:
        """Check if at maximum dose"""
        return self.get_next_increase_dose() is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "name": self.name,
            "generic_name": self.generic_name,
            "drug_class": self.drug_class.value,
            "current_dose": self.current_dose,
            "frequency": self.frequency,
            "timing": self.timing,
            "start_date": self.start_date.isoformat(),
            "is_active": self.is_active,
            "days_on_current_dose": self.days_on_current_dose,
            "dose_history": [d.to_dict() for d in self.dose_history],
        }

    def to_fhir_medication_request(self) -> dict:
        """Convert to FHIR MedicationRequest resource"""
        return {
            "resourceType": "MedicationRequest",
            "id": self.id,
            "status": "active" if self.is_active else "stopped",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": self.rxnorm_code or "",
                        "display": f"{self.generic_name}"
                    }
                ],
                "text": f"{self.name} ({self.generic_name})"
            },
            "subject": {
                "reference": f"Patient/{self.patient_id}"
            },
            "dosageInstruction": [
                {
                    "timing": {
                        "code": {
                            "text": self.frequency
                        }
                    },
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": self.dose_numeric if isinstance(self.dose_numeric, float) else None,
                                "unit": "mg"
                            }
                        }
                    ]
                }
            ]
        }


@dataclass
class MedicationHistory:
    """Complete medication history for a patient"""
    patient_id: str
    medications: List[Medication] = field(default_factory=list)

    @property
    def active_medications(self) -> List[Medication]:
        """Get currently active medications"""
        return [m for m in self.medications if m.is_active]

    @property
    def antihypertensive_medications(self) -> List[Medication]:
        """Get active antihypertensive medications"""
        ah_classes = {MedicationClass.CCB, MedicationClass.ARB,
                      MedicationClass.ARB_CCB_COMBO, MedicationClass.ACE_INHIBITOR,
                      MedicationClass.BETA_BLOCKER, MedicationClass.DIURETIC}
        return [m for m in self.active_medications if m.drug_class in ah_classes]

    def get_medication_by_name(self, name: str) -> Optional[Medication]:
        """Find medication by name (case-insensitive)"""
        name_lower = name.lower()
        for med in self.medications:
            if med.name.lower() == name_lower:
                return med
        return None

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "medications": [m.to_dict() for m in self.medications],
            "active_count": len(self.active_medications),
        }


# Predefined medication templates
def create_norvasc(patient_id: str, dose: str = "5mg", med_id: str = None) -> Medication:
    """Create a Norvasc (Amlodipine) medication record"""
    return Medication(
        id=med_id or f"med-norvasc-{patient_id}",
        patient_id=patient_id,
        name="Norvasc",
        generic_name="Amlodipine",
        drug_class=MedicationClass.CCB,
        current_dose=dose,
        frequency="QD",
        timing="morning",
        start_date=date.today(),
        rxnorm_code="329528",  # Amlodipine 5 MG Oral Tablet
    )


def create_exforge(patient_id: str, dose: str = "160/5mg", med_id: str = None) -> Medication:
    """Create an Exforge (Valsartan/Amlodipine) medication record"""
    return Medication(
        id=med_id or f"med-exforge-{patient_id}",
        patient_id=patient_id,
        name="Exforge",
        generic_name="Valsartan/Amlodipine",
        drug_class=MedicationClass.ARB_CCB_COMBO,
        current_dose=dose,
        frequency="QD",
        timing="morning",
        start_date=date.today(),
        rxnorm_code="603148",  # Valsartan 160 MG / Amlodipine 5 MG Oral Tablet
    )
