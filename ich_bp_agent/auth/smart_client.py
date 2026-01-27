"""
SMART on FHIR OAuth 2.0 Client
For Taiwan MOHW SMART Sandbox integration
"""
import httpx
import secrets
import hashlib
import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urlencode, urlparse, parse_qs
import json

from ..config import smart_config


@dataclass
class TokenResponse:
    """OAuth 2.0 Token Response"""
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    refresh_token: Optional[str] = None
    patient: Optional[str] = None  # Patient ID from SMART launch
    id_token: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.now)

    @property
    def expires_at(self) -> datetime:
        return self.issued_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        # Consider expired if within refresh margin
        margin = timedelta(seconds=smart_config.token_refresh_margin_seconds)
        return datetime.now() >= (self.expires_at - margin)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "scope": self.scope,
            "refresh_token": self.refresh_token,
            "patient": self.patient,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
        }


@dataclass
class SMARTEndpoints:
    """SMART on FHIR server endpoints"""
    authorization_endpoint: str
    token_endpoint: str
    introspection_endpoint: Optional[str] = None
    revocation_endpoint: Optional[str] = None
    registration_endpoint: Optional[str] = None
    management_endpoint: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)


class SMARTClient:
    """
    SMART on FHIR OAuth 2.0 Client

    Implements:
    - SMART App Launch Framework
    - OAuth 2.0 Authorization Code Flow with PKCE
    - Token refresh

    Usage:
        client = SMARTClient()
        await client.discover_endpoints()
        auth_url = client.get_authorization_url()
        # ... user authorizes ...
        tokens = await client.exchange_code(code)
    """

    def __init__(
        self,
        fhir_base_url: str = None,
        client_id: str = None,
        redirect_uri: str = None,
        scopes: List[str] = None,
    ):
        self.fhir_base_url = fhir_base_url or smart_config.fhir_base_url
        self.client_id = client_id or smart_config.client_id
        self.redirect_uri = redirect_uri or smart_config.redirect_uri
        self.scopes = scopes or smart_config.scopes

        self.endpoints: Optional[SMARTEndpoints] = None
        self._code_verifier: Optional[str] = None
        self._state: Optional[str] = None

    async def discover_endpoints(self) -> SMARTEndpoints:
        """
        Discover SMART on FHIR endpoints from server

        Fetches /.well-known/smart-configuration or /metadata
        """
        async with httpx.AsyncClient() as client:
            # Try .well-known/smart-configuration first
            smart_config_url = f"{self.fhir_base_url}/.well-known/smart-configuration"
            try:
                response = await client.get(smart_config_url)
                if response.status_code == 200:
                    data = response.json()
                    self.endpoints = SMARTEndpoints(
                        authorization_endpoint=data.get("authorization_endpoint", ""),
                        token_endpoint=data.get("token_endpoint", ""),
                        introspection_endpoint=data.get("introspection_endpoint"),
                        revocation_endpoint=data.get("revocation_endpoint"),
                        registration_endpoint=data.get("registration_endpoint"),
                        capabilities=data.get("capabilities", []),
                    )
                    return self.endpoints
            except Exception:
                pass

            # Fallback to CapabilityStatement/metadata
            metadata_url = f"{self.fhir_base_url}/metadata"
            response = await client.get(
                metadata_url,
                headers={"Accept": "application/fhir+json"}
            )
            if response.status_code == 200:
                data = response.json()
                # Extract OAuth URIs from security extension
                rest = data.get("rest", [{}])[0]
                security = rest.get("security", {})
                extensions = security.get("extension", [])

                auth_endpoint = ""
                token_endpoint = ""

                for ext in extensions:
                    if "oauth-uris" in ext.get("url", ""):
                        for inner_ext in ext.get("extension", []):
                            if inner_ext.get("url") == "authorize":
                                auth_endpoint = inner_ext.get("valueUri", "")
                            elif inner_ext.get("url") == "token":
                                token_endpoint = inner_ext.get("valueUri", "")

                self.endpoints = SMARTEndpoints(
                    authorization_endpoint=auth_endpoint,
                    token_endpoint=token_endpoint,
                )
                return self.endpoints

            raise Exception("Failed to discover SMART endpoints")

    def _generate_pkce_pair(self) -> tuple:
        """Generate PKCE code_verifier and code_challenge"""
        # Generate code_verifier (43-128 characters)
        code_verifier = secrets.token_urlsafe(64)[:128]
        self._code_verifier = code_verifier

        # Generate code_challenge (SHA256 hash, base64url encoded)
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        return code_verifier, code_challenge

    def get_authorization_url(
        self,
        state: str = None,
        launch: str = None,
        aud: str = None,
    ) -> str:
        """
        Generate authorization URL for user login

        Args:
            state: State parameter for CSRF protection
            launch: Launch context (for EHR launch)
            aud: Audience (FHIR server URL)

        Returns:
            Authorization URL to redirect user to
        """
        if not self.endpoints:
            raise ValueError("Endpoints not discovered. Call discover_endpoints() first.")

        # Generate PKCE pair
        _, code_challenge = self._generate_pkce_pair()

        # Generate state if not provided
        self._state = state or secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": self._state,
            "aud": aud or self.fhir_base_url,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        if launch:
            params["launch"] = launch

        auth_url = f"{self.endpoints.authorization_endpoint}?{urlencode(params)}"
        return auth_url

    async def exchange_code(
        self,
        code: str,
        state: str = None,
    ) -> TokenResponse:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from callback
            state: State parameter to verify

        Returns:
            TokenResponse with access token and refresh token
        """
        if not self.endpoints:
            raise ValueError("Endpoints not discovered")

        if state and self._state and state != self._state:
            raise ValueError("State mismatch - possible CSRF attack")

        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "code_verifier": self._code_verifier,
            }

            response = await client.post(
                self.endpoints.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise Exception(f"Token exchange failed: {error_data}")

            token_data = response.json()

            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                scope=token_data.get("scope", ""),
                refresh_token=token_data.get("refresh_token"),
                patient=token_data.get("patient"),
                id_token=token_data.get("id_token"),
            )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an expired access token

        Args:
            refresh_token: Refresh token from previous token response

        Returns:
            New TokenResponse with fresh access token
        """
        if not self.endpoints:
            raise ValueError("Endpoints not discovered")

        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
            }

            response = await client.post(
                self.endpoints.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise Exception(f"Token refresh failed: {error_data}")

            token_data = response.json()

            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                scope=token_data.get("scope", ""),
                refresh_token=token_data.get("refresh_token", refresh_token),
                patient=token_data.get("patient"),
            )

    def parse_callback_url(self, callback_url: str) -> Dict[str, str]:
        """
        Parse the callback URL to extract code and state

        Args:
            callback_url: Full callback URL with query parameters

        Returns:
            Dict with 'code' and 'state' parameters
        """
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)

        result = {}
        if "code" in params:
            result["code"] = params["code"][0]
        if "state" in params:
            result["state"] = params["state"][0]
        if "error" in params:
            result["error"] = params["error"][0]
            result["error_description"] = params.get("error_description", [""])[0]

        return result


class MockSMARTClient(SMARTClient):
    """
    Mock SMART client for local development/testing

    Simulates SMART authentication without real OAuth
    """

    def __init__(self, patient_id: str = "patient-ich-001"):
        super().__init__()
        self.mock_patient_id = patient_id

    async def discover_endpoints(self) -> SMARTEndpoints:
        """Return mock endpoints"""
        self.endpoints = SMARTEndpoints(
            authorization_endpoint="http://localhost:8501/mock-auth",
            token_endpoint="http://localhost:8501/mock-token",
        )
        return self.endpoints

    def get_authorization_url(self, **kwargs) -> str:
        """Return mock auth URL"""
        return "http://localhost:8501/mock-auth?mock=true"

    async def exchange_code(self, code: str, state: str = None) -> TokenResponse:
        """Return mock token response"""
        return TokenResponse(
            access_token="mock-access-token-" + secrets.token_hex(16),
            token_type="Bearer",
            expires_in=3600,
            scope=" ".join(self.scopes),
            patient=self.mock_patient_id,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Return mock refreshed token"""
        return await self.exchange_code("mock-code")
