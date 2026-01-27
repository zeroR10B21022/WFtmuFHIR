"""
SMART on FHIR Integration for Streamlit
Uses fhirclient library for OAuth flow
"""
import streamlit as st
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from typing import Optional, Dict
import httpx
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
        # Debug info
        st.info(f"🔍 FHIR Base URL: {smart.server.base_uri}")
        st.info(f"🔍 App ID: {smart.app_id}")
        st.info(f"🔍 Redirect URI: {smart.redirect_uri}")

        # Try to get authorization URL
        try:
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
                st.error("❌ Could not generate authorization URL")
                st.warning("The FHIR server may not support SMART on FHIR OAuth.")

                # Show what we tried
                with st.expander("🔧 Debug Information"):
                    st.write("The fhirclient library couldn't find OAuth endpoints.")
                    st.write(f"Looking for endpoints at: {smart.server.base_uri}/metadata")
                    st.write("The server's capability statement should include OAuth URIs.")

        except Exception as e:
            st.error(f"❌ Error getting authorization URL: {e}")
            st.write(f"Server: {smart.server.base_uri}")


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


def check_smart_support(fhir_base_url: str) -> Dict[str, any]:
    """
    Check if a FHIR server supports SMART on FHIR

    Args:
        fhir_base_url: The FHIR server base URL

    Returns:
        Dictionary with:
        - supported: bool - whether SMART is supported
        - authorize_url: str or None
        - token_url: str or None
        - error: str or None
    """
    try:
        # Fetch capability statement
        metadata_url = f"{fhir_base_url}/metadata"
        response = httpx.get(metadata_url, timeout=10.0)
        response.raise_for_status()

        capability = response.json()

        # Look for OAuth URIs in capability statement
        # SMART OAuth URIs are in rest[0].security.extension
        oauth_uris = None

        if "rest" in capability and len(capability["rest"]) > 0:
            rest = capability["rest"][0]
            if "security" in rest and "extension" in rest["security"]:
                for ext in rest["security"]["extension"]:
                    if ext.get("url") == "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris":
                        oauth_uris = ext.get("extension", [])
                        break

        if oauth_uris:
            # Extract authorize and token URLs
            authorize_url = None
            token_url = None

            for uri in oauth_uris:
                if uri.get("url") == "authorize":
                    authorize_url = uri.get("valueUri")
                elif uri.get("url") == "token":
                    token_url = uri.get("valueUri")

            return {
                "supported": True,
                "authorize_url": authorize_url,
                "token_url": token_url,
                "error": None
            }
        else:
            return {
                "supported": False,
                "authorize_url": None,
                "token_url": None,
                "error": "No SMART OAuth URIs found in capability statement"
            }

    except Exception as e:
        return {
            "supported": False,
            "authorize_url": None,
            "token_url": None,
            "error": str(e)
        }
