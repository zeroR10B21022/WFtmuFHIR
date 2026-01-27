"""
Compare URL encoding between Python quote() and JavaScript encodeURIComponent()

This script helps identify if there are any encoding differences that could
cause the null byte error with Taiwan MOHW.
"""
from urllib.parse import quote, urlencode
import json


def show_encoding_comparison(text, description):
    """Show how Python encodes a string"""
    print(f"\n{'='*80}")
    print(f"Encoding: {description}")
    print(f"{'='*80}")
    print(f"Original: {repr(text)}")
    print(f"Bytes:    {text.encode('utf-8')}")
    print(f"quote():  {quote(text, safe='')}")
    print(f"Hex:      {quote(text, safe='').encode('utf-8').hex()}")


def main():
    print("URL ENCODING COMPARISON")
    print("=" * 80)
    print("\nPython quote() should match JavaScript encodeURIComponent()")
    print("If there are differences, they could cause the null byte error.\n")

    # Test cases
    test_cases = [
        ("demo_client", "Client ID"),
        ("openid fhirUser patient/Patient.read", "Scope with spaces and slashes"),
        ("https://wftmufhir.streamlit.app/", "Redirect URI"),
        ("https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir", "FHIR Base URL"),
        ("test_state_abc123", "State parameter"),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "Sample JWT launch token"),
    ]

    for text, description in test_cases:
        show_encoding_comparison(text, description)

    # Special test: what if launch token has null bytes?
    print(f"\n{'='*80}")
    print("TESTING FOR NULL BYTES")
    print(f"{'='*80}")

    test_with_null = "test\x00token"
    print(f"\nString with null byte: {repr(test_with_null)}")
    print(f"Bytes: {test_with_null.encode('utf-8')}")
    print(f"quote(): {quote(test_with_null, safe='')}")
    print(f"Hex: {quote(test_with_null, safe='').encode('utf-8').hex()}")
    print("\nNote: Null byte is encoded as %00 by quote()")

    # Show JavaScript equivalent
    print(f"\n{'='*80}")
    print("JAVASCRIPT EQUIVALENT")
    print(f"{'='*80}")
    print("""
In JavaScript, you would check with:

    const text = "test string";
    const encoded = encodeURIComponent(text);
    console.log(encoded);

encodeURIComponent() encodes:
- Spaces as %20
- Slashes (/) as %2F
- Colons (:) as %3A
- Special chars, but NOT: A-Z a-z 0-9 - _ . ! ~ * ' ( )

Python's quote(safe='') should match this exactly.
""")

    # Test: compare parameter building
    print(f"\n{'='*80}")
    print("COMPLETE AUTHORIZATION URL EXAMPLE")
    print(f"{'='*80}")

    params = {
        "response_type": "code",
        "client_id": "demo_client",
        "scope": "openid fhirUser patient/Patient.read patient/Observation.read launch",
        "redirect_uri": "https://wftmufhir.streamlit.app/",
        "aud": "https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir",
        "state": "test_state_123",
        "launch": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    }

    # Build URL our way
    redirect_params = []
    for key, value in params.items():
        encoded = quote(value, safe='')
        redirect_params.append(f"{key}={encoded}")
        print(f"\n{key}:")
        print(f"  Original: {value}")
        print(f"  Encoded:  {encoded}")

    authorize_url = "https://thas.mohw.gov.tw/v/r4/sim/.../oauth/authorize"
    full_url = f"{authorize_url}?{'&'.join(redirect_params)}"

    print(f"\n{'='*80}")
    print(f"Full URL length: {len(full_url)} characters")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
