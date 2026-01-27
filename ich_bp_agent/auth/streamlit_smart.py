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
import requests
import urllib3
from urllib.parse import quote
from ..config import smart_config

# Disable SSL warnings for sandbox/test servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_smart_client() -> Optional[client.FHIRClient]:
    """
    Get or create SMART FHIR client for Streamlit app

    Handles both EHR Launch (with iss & launch params) and OAuth callback
    """
    # Initialize session state
    if 'smart_client' not in st.session_state:
        st.session_state.smart_client = None

    # Check for OAuth callback with code
    query_params = st.query_params

    # Check for EHR Launch parameters
    iss = query_params.get('iss')
    launch = query_params.get('launch')

    # Configure SMART client
    if iss:
        # EHR Launch: use iss from launch parameter
        settings = {
            'app_id': smart_config.client_id or 'ich_bp_app',
            'api_base': iss,  # Use ISS from launch
            'redirect_uri': smart_config.redirect_uri,
        }
        st.info(f"🚀 EHR Launch detected: {iss}")
    else:
        # Standalone launch: use configured FHIR base URL
        settings = {
            'app_id': smart_config.client_id or 'ich_bp_app',
            'api_base': smart_config.fhir_base_url,
            'redirect_uri': smart_config.redirect_uri,
        }

    # Create client
    smart = client.FHIRClient(settings=settings)

    # Disable SSL verification for sandbox/test servers
    # WARNING: Only use this for development/testing, not production!
    if smart.server:
        session = requests.Session()
        session.verify = False
        smart.server.session = session

    # If we have launch parameters, prepare to authorize
    if iss and launch:
        # Save launch params to session
        st.session_state.launch_iss = iss
        st.session_state.launch_token = launch
        # Don't clear query params yet, fhirclient needs them

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
        # Check if this is an EHR launch (has launch parameters in session)
        is_ehr_launch = hasattr(st.session_state, 'launch_iss') and st.session_state.launch_iss

        # Try to get authorization URL
        try:
            auth_url = smart.authorize_url

            if auth_url:
                # If EHR Launch, manually add the launch parameter to the URL
                if is_ehr_launch and hasattr(st.session_state, 'launch_token'):
                    launch_token = st.session_state.launch_token

                    # Debug: Show the launch token
                    with st.expander("🔍 Debug: Launch Token"):
                        st.code(f"Raw launch token: {launch_token}")
                        st.code(f"Launch token length: {len(launch_token)}")
                        st.code(f"Launch token (repr): {repr(launch_token)}")

                    # URL-encode the launch parameter
                    encoded_launch = quote(launch_token, safe='')

                    # Add launch parameter to auth URL
                    separator = '&' if '?' in auth_url else '?'
                    auth_url = f"{auth_url}{separator}launch={encoded_launch}"
                    st.info(f"🔍 Added URL-encoded launch parameter to authorization URL")

                if is_ehr_launch:
                    # EHR Launch: auto-redirect immediately
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                               unsafe_allow_html=True)
                else:
                    # Standalone Launch: show debug info and link
                    st.info(f"🔍 FHIR Base URL: {smart.server.base_uri}")
                    st.info(f"🔍 App ID: {smart.app_id}")
                    st.info(f"🔍 Redirect URI: {smart.redirect}")

                    st.markdown(f"### Please authorize the app")
                    st.markdown(f"[Click here to login with FHIR server]({auth_url})")
                    st.info("After logging in, you will be redirected back to this app.")

                    # Auto-redirect
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
        # Disable SSL verification for sandbox/test servers
        response = httpx.get(metadata_url, timeout=10.0, verify=False)
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
