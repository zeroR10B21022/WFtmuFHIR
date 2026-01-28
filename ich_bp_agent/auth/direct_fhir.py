"""
Direct FHIR Access (No OAuth Required)
For use with open FHIR servers like Taiwan HAPI that don't require authentication
"""
import streamlit as st
import httpx
from typing import Optional, List, Dict, Any


def connect_direct_fhir(fhir_base_url: str) -> bool:
    """
    Connect directly to FHIR server without OAuth

    Args:
        fhir_base_url: Base URL of FHIR server

    Returns:
        True if connection successful
    """
    try:
        # Test connection with capability statement
        response = httpx.get(
            f"{fhir_base_url}/metadata",
            headers={"Accept": "application/fhir+json"},
            timeout=10.0
        )
        response.raise_for_status()

        # Store in session
        st.session_state.fhir_base_url = fhir_base_url
        st.session_state.authenticated = True
        st.session_state.direct_fhir = True  # Flag for direct access

        return True

    except Exception as e:
        st.error(f"Failed to connect to FHIR server: {e}")
        return False


def search_patients_direct(fhir_base_url: str, name: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
    """
    Search for patients on FHIR server

    Args:
        fhir_base_url: Base URL of FHIR server
        name: Optional name to search for
        count: Number of results to return

    Returns:
        List of patient resources
    """
    try:
        # Build search URL
        url = f"{fhir_base_url}/Patient?_count={count}"
        if name:
            url += f"&name={name}"

        response = httpx.get(
            url,
            headers={"Accept": "application/fhir+json"},
            timeout=10.0
        )
        response.raise_for_status()

        bundle = response.json()
        if "entry" in bundle:
            return [entry["resource"] for entry in bundle["entry"]]
        return []

    except Exception as e:
        st.error(f"Failed to search patients: {e}")
        return []


def get_patient_direct(fhir_base_url: str, patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Get patient by ID

    Args:
        fhir_base_url: Base URL of FHIR server
        patient_id: Patient ID

    Returns:
        Patient resource or None
    """
    try:
        response = httpx.get(
            f"{fhir_base_url}/Patient/{patient_id}",
            headers={"Accept": "application/fhir+json"},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        st.error(f"Failed to get patient: {e}")
        return None


def search_observations_direct(
    fhir_base_url: str,
    patient_id: str,
    code: Optional[str] = None,
    count: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for observations (e.g., blood pressure)

    Args:
        fhir_base_url: Base URL of FHIR server
        patient_id: Patient ID
        code: Optional LOINC code (e.g., "85354-9" for BP)
        count: Number of results to return

    Returns:
        List of observation resources
    """
    try:
        url = f"{fhir_base_url}/Observation?patient={patient_id}&_sort=-date&_count={count}"
        if code:
            url += f"&code={code}"

        response = httpx.get(
            url,
            headers={"Accept": "application/fhir+json"},
            timeout=10.0
        )
        response.raise_for_status()

        bundle = response.json()
        if "entry" in bundle:
            return [entry["resource"] for entry in bundle["entry"]]
        return []

    except Exception as e:
        st.error(f"Failed to search observations: {e}")
        return []


def create_observation_direct(
    fhir_base_url: str,
    patient_id: str,
    systolic: int,
    diastolic: int,
    date_time: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a blood pressure observation

    Args:
        fhir_base_url: Base URL of FHIR server
        patient_id: Patient ID
        systolic: Systolic BP value
        diastolic: Diastolic BP value
        date_time: Optional datetime string (ISO format)

    Returns:
        Created observation resource or None
    """
    try:
        from datetime import datetime

        if not date_time:
            date_time = datetime.now().isoformat()

        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure panel"
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": date_time,
            "component": [
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": systolic,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                },
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": diastolic,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                }
            ]
        }

        response = httpx.post(
            f"{fhir_base_url}/Observation",
            json=observation,
            headers={
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            },
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        st.error(f"Failed to create observation: {e}")
        return None
