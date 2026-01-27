"""
SMART on FHIR Integration for Streamlit
Uses fhirclient library for OAuth flow
"""
import streamlit as st
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from typing import Optional
from ..config import smart_config


def get_smart_client() -> Optional[client.FHIRClient]:
    """
    Get or create SMART FHIR client for Streamlit app

    Handles OAuth flow with query parameters from SMART launch
    """
    # Initialize session state
    if 'smart_client' not in st.session_state:
        st.session_state.smart_client = None

    # Check for OAuth callback with code
    query_params = st.query_params

    # Configure SMART client
    settings = {
        'app_id': smart_config.client_id or 'ich_bp_app',
        'api_base': smart_config.fhir_base_url,
        'redirect_uri': smart_config.redirect_uri,
    }

    # Create client
    smart = client.FHIRClient(settings=settings)

    # Check if we have authorization code in query params
    if 'code' in query_params:
        # Exchange code for token
        try:
            # fhirclient handles token exchange automatically
            smart.handle_callback(st.query_params.to_dict())
            st.session_state.smart_client = smart
            st.session_state.authenticated = True

            # Clear query params
            st.query_params.clear()

        except Exception as e:
            st.error(f"OAuth callback error: {e}")
            return None

    # Check if we already have a client
    if st.session_state.smart_client:
        return st.session_state.smart_client

    return smart


def start_smart_auth():
    """
    Start SMART on FHIR OAuth flow

    Redirects user to authorization URL
    """
    smart = get_smart_client()

    if smart:
        # Get authorization URL
        auth_url = smart.authorize_url

        if auth_url:
            # Show link to user
            st.markdown(f"### Please authorize the app")
            st.markdown(f"[Click here to login with FHIR server]({auth_url})")
            st.info("After logging in, you will be redirected back to this app.")

            # Or auto-redirect
            st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                       unsafe_allow_html=True)
        else:
            st.error("Could not generate authorization URL")


def get_patient_data():
    """
    Get current patient data from SMART context

    Returns patient resource or None
    """
    smart = st.session_state.get('smart_client')

    if not smart or not smart.ready:
        return None

    try:
        # Get patient ID from SMART context
        patient_id = smart.patient_id

        if patient_id:
            # Read patient resource
            patient = Patient.read(patient_id, smart.server)
            return patient

    except Exception as e:
        st.error(f"Error loading patient: {e}")
        return None


def search_observations(patient_id: str, code: str = "85354-9", count: int = 100):
    """
    Search for observations (e.g., blood pressure)

    Args:
        patient_id: Patient ID
        code: LOINC code (default: 85354-9 for BP panel)
        count: Max number of results

    Returns list of Observation resources
    """
    smart = st.session_state.get('smart_client')

    if not smart or not smart.ready:
        return []

    try:
        # Search observations
        search = Observation.where(struct={
            'patient': patient_id,
            'code': code,
            '_sort': '-date',
            '_count': count
        })

        observations = search.perform_resources(smart.server)
        return observations

    except Exception as e:
        st.error(f"Error searching observations: {e}")
        return []


def is_authenticated() -> bool:
    """Check if user is authenticated with SMART server"""
    smart = st.session_state.get('smart_client')
    return smart is not None and smart.ready if smart else False
