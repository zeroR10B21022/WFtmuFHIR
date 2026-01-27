"""
SMART on FHIR Integration for Streamlit
Uses manual OAuth implementation (bypassing fhirclient)
"""
import streamlit as st
from typing import Optional, Dict
import urllib3
from ..config import smart_config
from .manual_oauth import (
    start_oauth_flow,
    handle_oauth_callback,
    make_fhir_request,
    init_oauth_session
)

# Disable SSL warnings for sandbox/test servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_smart_client():
    """
    Initialize OAuth session and handle EHR Launch parameters

    Returns tuple: (fhir_base_url, launch_token) or (None, None)
    """
    init_oauth_session()

    # Check for OAuth callback with code
    query_params = st.query_params

    # Check for EHR Launch parameters
    iss = query_params.get('iss')
    launch = query_params.get('launch')

    # Save FHIR base URL and launch token
    if iss:
        st.session_state.fhir_base_url = iss
        st.info(f"🚀 EHR Launch detected: {iss}")
    elif not st.session_state.fhir_base_url:
        st.session_state.fhir_base_url = smart_config.fhir_base_url

    if launch:
        st.session_state.launch_token = launch

    # Handle OAuth callback
    if 'code' in query_params and 'state' in query_params:
        code = query_params.get('code')
        state = query_params.get('state')

        if handle_oauth_callback(
            code,
            state,
            smart_config.client_id or 'demo_client',
            smart_config.redirect_uri
        ):
            st.session_state.authenticated = True
            st.success("✅ OAuth authentication successful!")
            # Clear query params
            st.query_params.clear()
            st.rerun()
        else:
            st.error("❌ OAuth authentication failed")
            return None, None

    fhir_base_url = st.session_state.fhir_base_url
    launch_token = st.session_state.get('launch_token')

    return fhir_base_url, launch_token


def start_smart_auth():
    """
    Start SMART on FHIR OAuth flow using manual OAuth implementation

    Taiwan MOHW uses Provider Standalone Launch (NOT EHR Launch)
    This means NO launch parameter, NO launch scope

    Redirects user to authorization URL
    """
    fhir_base_url, launch_token = get_smart_client()

    if not fhir_base_url:
        st.error("FHIR base URL not available")
        return

    # Configure scope (matching JavaScript client exactly)
    # Provider Standalone Launch - NO "launch" scope
    scope = "openid fhirUser patient/Patient.read patient/Observation.read patient/Observation.write patient/Condition.read patient/MedicationRequest.read patient/MedicationAdministration.read"

    # IMPORTANT: Taiwan MOHW uses Provider Standalone Launch
    # DO NOT pass launch token - ignore it even if present
    st.info("📋 Using Provider Standalone Launch (Taiwan MOHW pattern)")

    # Start OAuth flow WITHOUT launch token
    auth_url = start_oauth_flow(
        fhir_base_url,
        smart_config.client_id or 'demo_client',
        smart_config.redirect_uri,
        scope,
        None  # Force NO launch token for Provider Standalone Launch
    )

    if auth_url:
        # Show authorization info
        st.success("✅ Authorization URL generated successfully!")

        # Debug information
        with st.expander("🔍 Debug: OAuth Configuration", expanded=True):
            st.code(f"""Launch Type: Provider Standalone Launch
FHIR Base URL: {fhir_base_url}
Client ID: {smart_config.client_id or 'demo_client'}
Redirect URI: {smart_config.redirect_uri}
Launch Token in URL: {bool(launch_token)} (IGNORED for standalone launch)
Scope: {scope}

Note: Taiwan MOHW uses Provider Standalone Launch.
This means NO launch parameter is sent, matching the JavaScript client.""")

        with st.expander("🔍 Debug: Authorization URL", expanded=True):
            st.code(auth_url)
            st.write("URL Length:", len(auth_url))

            # Parse and show each parameter
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(auth_url)
            st.write("**Parameters:**")
            for key, value in parse_qs(parsed.query).items():
                st.code(f"{key} = {repr(value[0])}")
                if key == "launch":
                    st.write(f"Launch bytes: {value[0].encode('utf-8')}")

        with st.expander("🔍 Compare with JavaScript"):
            st.info("JavaScript client (Provider Standalone Launch) sends:")
            st.code(f"""response_type=code
client_id={smart_config.client_id or 'demo_client'}
scope={scope}
redirect_uri={smart_config.redirect_uri}
aud={fhir_base_url}
state=[random]

NO launch parameter (Provider Standalone Launch)
NO 'launch' in scope (Provider Standalone Launch)""")

        # DON'T auto-redirect - let user review first
        st.warning("⚠️ Review the debug information above before clicking the link below")
        st.markdown(f"[Click here to authorize]({auth_url})")
    else:
        st.error("❌ Failed to generate authorization URL")
        st.info(f"Attempted FHIR server: {fhir_base_url}")


def get_patient_data():
    """
    Get current patient data from SMART context

    Returns patient resource or None
    """
    access_token = st.session_state.get('access_token')
    patient_id = st.session_state.get('patient_id')
    fhir_base_url = st.session_state.get('fhir_base_url')

    if not all([access_token, patient_id, fhir_base_url]):
        return None

    try:
        # Read patient resource
        patient_url = f"{fhir_base_url}/Patient/{patient_id}"
        patient = make_fhir_request(patient_url, access_token)
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
    access_token = st.session_state.get('access_token')
    fhir_base_url = st.session_state.get('fhir_base_url')

    if not all([access_token, fhir_base_url]):
        return []

    try:
        # Build search URL
        search_url = f"{fhir_base_url}/Observation?patient={patient_id}&code={code}&_sort=-date&_count={count}"
        result = make_fhir_request(search_url, access_token)

        if result and "entry" in result:
            return [entry["resource"] for entry in result["entry"]]

        return []

    except Exception as e:
        st.error(f"Error searching observations: {e}")
        return []


def is_authenticated() -> bool:
    """Check if user is authenticated with SMART server"""
    return st.session_state.get('access_token') is not None


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
