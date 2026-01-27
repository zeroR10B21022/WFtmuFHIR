"""
Test script to verify SMART on FHIR sandbox connection
Run this before launching the full Streamlit app
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ich_bp_agent.auth.smart_client import SMARTClient
from ich_bp_agent.config import smart_config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_sandbox_connection():
    """Test connection to SMART sandbox"""

    print("=" * 60)
    print("SMART on FHIR Sandbox Connection Test")
    print("=" * 60)
    print()

    # Display current configuration
    print("Configuration:")
    print(f"  FHIR Base URL: {smart_config.fhir_base_url}")
    print(f"  Client ID: {smart_config.client_id}")
    print(f"  Redirect URI: {smart_config.redirect_uri}")
    print(f"  Scopes: {', '.join(smart_config.scopes)}")
    print()

    # Validate configuration
    if not smart_config.client_id:
        print("❌ ERROR: SMART_CLIENT_ID not set in .env file")
        return False

    if not smart_config.fhir_base_url:
        print("❌ ERROR: SMART_FHIR_BASE_URL not set in .env file")
        return False

    # Initialize client
    print("Initializing SMART client...")
    client = SMARTClient()

    try:
        # Test 1: Discover endpoints
        print("\n[Test 1] Discovering SMART endpoints...")
        endpoints = await client.discover_endpoints()

        if endpoints.authorization_endpoint:
            print(f"  ✅ Authorization endpoint: {endpoints.authorization_endpoint}")
        else:
            print(f"  ❌ Authorization endpoint not found")
            return False

        if endpoints.token_endpoint:
            print(f"  ✅ Token endpoint: {endpoints.token_endpoint}")
        else:
            print(f"  ❌ Token endpoint not found")
            return False

        # Test 2: Generate authorization URL
        print("\n[Test 2] Generating authorization URL...")
        auth_url = client.get_authorization_url()
        print(f"  ✅ Authorization URL generated:")
        print(f"     {auth_url[:80]}...")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Your app is configured to use the public sandbox")
        print("2. Run the Streamlit app:")
        print("   streamlit run ich_bp_agent/ui/app.py")
        print()
        print("3. When you're ready for Taiwan MOHW sandbox:")
        print("   - Update .env with your registered client_id")
        print("   - Change SMART_FHIR_BASE_URL to Taiwan's sandbox")
        print()

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check your .env file exists and has correct values")
        print("2. Verify internet connection")
        print("3. Check if the FHIR server URL is accessible")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sandbox_connection())
    sys.exit(0 if success else 1)
