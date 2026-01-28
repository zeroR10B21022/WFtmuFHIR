"""
Manual SMART on FHIR OAuth2 Implementation
Bypasses fhirclient library to match JavaScript client behavior
"""
import streamlit as st
import httpx
import secrets
from urllib.parse import urlencode, parse_qs, urlparse, quote
from typing import Optional, Dict, Any
import json


def get_oauth_endpoints(fhir_base_url: str) -> Dict[str, str]:
    """
    Fetch OAuth endpoints from FHIR server's capability statement

    Args:
        fhir_base_url: Base URL of FHIR server

    Returns:
        Dictionary with authorize_url and token_url
    """
    try:
        # Fetch capability statement
        response = httpx.get(
            f"{fhir_base_url}/metadata",
            verify=False,  # Disable SSL verification for sandbox
            timeout=10.0
        )
        response.raise_for_status()
        capability = response.json()

        # Find OAuth URIs in capability statement
        if "rest" in capability and len(capability["rest"]) > 0:
            rest = capability["rest"][0]
            if "security" in rest and "extension" in rest["security"]:
                for ext in rest["security"]["extension"]:
                    if ext.get("url") == "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris":
                        oauth_uris = ext.get("extension", [])

                        result = {}
                        for uri in oauth_uris:
                            if uri.get("url") == "authorize":
                                result["authorize_url"] = uri.get("valueUri")
                            elif uri.get("url") == "token":
                                result["token_url"] = uri.get("valueUri")

                        return result

        raise ValueError("No OAuth endpoints found in capability statement")

    except Exception as e:
        st.error(f"Failed to get OAuth endpoints: {e}")
        return {}


def build_authorization_url(
    authorize_url: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    fhir_base_url: str,
    launch: Optional[str] = None
) -> str:
    """
    Build OAuth2 authorization URL (matching fhirclient.js behavior)

    Args:
        authorize_url: Authorization endpoint URL
        client_id: Client ID
        redirect_uri: Redirect URI after authorization
        scope: OAuth scopes
        state: Random state for CSRF protection
        fhir_base_url: FHIR server base URL (used for 'aud' parameter)
        launch: Optional launch token for EHR launch

    Returns:
        Complete authorization URL
    """
    # Validate and clean launch parameter (must be non-empty string)
    # For Taiwan MOHW: Provider Standalone Launch does NOT use launch parameter
    if launch:
        launch = str(launch).strip()
        if not launch or launch == "None":
            launch = None

    # Validate redirect_uri format
    from urllib.parse import urlparse
    parsed = urlparse(redirect_uri)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid redirect_uri format: {redirect_uri}")

    # Log which redirect URI is being used (for debugging)
    try:
        import streamlit as st
        st.info(f"📍 Using redirect URI: {redirect_uri}")
    except:
        pass

    # Build parameters dictionary (like Python fhirclient)
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,  # Scope is passed as-is, no "launch" added
        'redirect_uri': redirect_uri,
        'aud': fhir_base_url,
        'state': state
    }

    # Add launch parameter ONLY if it's a valid non-empty string
    # NOTE: For Provider Standalone Launch, launch should be None
    if launch:
        # Log for debugging
        try:
            import streamlit as st
            st.write(f"DEBUG: Adding launch parameter: {repr(launch)}, bytes: {launch.encode('utf-8')}")
            st.warning("⚠️ Launch parameter present! Taiwan MOHW uses Provider Standalone Launch (no launch param)")
        except:
            pass
        params['launch'] = launch

    # Use urlencode like Python fhirclient does
    # This matches the Python FHIR client behavior more closely
    from urllib.parse import urlencode as url_encode
    encoded_params = url_encode(params, doseq=True)

    return f"{authorize_url}?{encoded_params}"


def exchange_code_for_token(
    token_url: str,
    code: str,
    client_id: str,
    redirect_uri: str
) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access token

    Args:
        token_url: Token endpoint URL
        code: Authorization code from callback
        client_id: Client ID
        redirect_uri: Redirect URI (must match authorization request)

    Returns:
        Token response with access_token, patient, etc.
    """
    try:
        response = httpx.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=False,  # Disable SSL verification for sandbox
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        st.error(f"Token exchange failed: {e}")
        return None


def make_fhir_request(
    url: str,
    access_token: str,
    method: str = "GET",
    json_data: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Make authenticated FHIR API request

    Args:
        url: FHIR resource URL
        access_token: OAuth access token
        method: HTTP method (GET, POST, etc.)
        json_data: Optional JSON data for POST/PUT

    Returns:
        FHIR resource response
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json"
        }

        if method == "GET":
            response = httpx.get(url, headers=headers, verify=False, timeout=10.0)
        elif method == "POST":
            headers["Content-Type"] = "application/fhir+json"
            response = httpx.post(url, headers=headers, json=json_data, verify=False, timeout=10.0)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    except Exception as e:
        st.error(f"FHIR request failed: {e}")
        return None


def init_oauth_session():
    """Initialize OAuth session state variables"""
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'patient_id' not in st.session_state:
        st.session_state.patient_id = None
    if 'fhir_base_url' not in st.session_state:
        st.session_state.fhir_base_url = None


def start_oauth_flow(
    fhir_base_url: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    launch: Optional[str] = None
):
    """
    Start OAuth2 authorization flow

    Args:
        fhir_base_url: Base URL of FHIR server
        client_id: Client ID
        redirect_uri: Redirect URI
        scope: OAuth scopes
        launch: Optional launch token for EHR launch
    """
    init_oauth_session()

    # Get OAuth endpoints
    endpoints = get_oauth_endpoints(fhir_base_url)
    if not endpoints:
        st.error("Failed to retrieve OAuth endpoints")
        return None

    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    st.session_state.oauth_state = state
    st.session_state.fhir_base_url = fhir_base_url

    # Build authorization URL (matching fhirclient.js behavior)
    auth_url = build_authorization_url(
        endpoints["authorize_url"],
        client_id,
        redirect_uri,
        scope,
        state,
        fhir_base_url,  # Pass FHIR base URL for 'aud' parameter
        launch
    )

    return auth_url


def handle_oauth_callback(
    code: str,
    state: str,
    client_id: str,
    redirect_uri: str
) -> bool:
    """
    Handle OAuth callback with authorization code

    Args:
        code: Authorization code
        state: State parameter (for CSRF protection)
        client_id: Client ID
        redirect_uri: Redirect URI

    Returns:
        True if successful, False otherwise
    """
    init_oauth_session()

    # Verify state
    if state != st.session_state.oauth_state:
        st.error("Invalid state parameter - possible CSRF attack")
        return False

    # Get token endpoint
    fhir_base_url = st.session_state.fhir_base_url
    if not fhir_base_url:
        st.error("FHIR base URL not found in session")
        return False

    endpoints = get_oauth_endpoints(fhir_base_url)
    if not endpoints:
        return False

    # Exchange code for token
    token_response = exchange_code_for_token(
        endpoints["token_url"],
        code,
        client_id,
        redirect_uri
    )

    if not token_response:
        return False

    # Save token and patient ID
    st.session_state.access_token = token_response.get("access_token")
    st.session_state.patient_id = token_response.get("patient")

    return True
