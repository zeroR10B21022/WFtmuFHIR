# Taiwan MOHW FHIR Client Registration Guide

## Current Issue

The Taiwan MOHW SMART Sandbox requires a registered client ID, but there is **no public self-service registration portal**. The `demo_client` ID used in the code is **not registered** with Taiwan MOHW, which is why OAuth fails with:

```
error: "invalid_request"
error_description: "Invalid launch options: SyntaxError: Unexpected token � in JSON at position 3"
```

This error is misleading - it's actually a **client_id not recognized** error.

## Taiwan MOHW FHIR Infrastructure

Taiwan's Ministry of Health and Welfare (衛生福利部) has established the following FHIR infrastructure:

### Official Resources
- **Taiwan Medical Information Standards Platform**: https://medstandard.mohw.gov.tw/
- **FHIR Updates**: https://emr.mohw.gov.tw/myemr/Html/FHIR
- **Taiwan Core IG**: https://twcore.mohw.gov.tw/
- **HAPI FHIR Test Server**: https://twcore.hapi.fhir.tw/

### What's Missing
- **No public client registration portal**
- **No self-service developer signup**
- **No documented API for client registration**

## How to Get Client ID Access

### Method 1: Institutional Contact (Recommended)

Contact Taiwan MOHW directly through official channels:

1. **Visit the Medical Information Standards Platform**
   - URL: https://medstandard.mohw.gov.tw/
   - Look for "聯絡我們" (Contact Us) or developer documentation

2. **Contact via FHIR Updates Page**
   - URL: https://emr.mohw.gov.tw/myemr/Html/FHIR
   - Check for announcements about sandbox access

3. **Information to Provide**:
   ```
   Application Name: 血壓紅黃綠燈 (Blood Pressure Traffic Light System)
   Institution: [Your institution/organization]
   Purpose: ICH post-stroke blood pressure monitoring
   Application Type: Public (SMART on FHIR web application)
   Redirect URIs:
   - http://localhost:8501/callback (development)
   - https://wftmufhir.streamlit.app/callback (production)
   Scopes Required:
   - openid
   - fhirUser
   - patient/Patient.read
   - patient/Observation.read
   - patient/Observation.write
   - patient/MedicationRequest.read
   - patient/MedicationAdministration.read
   - patient/Condition.read
   ```

### Method 2: Academic/Research Collaboration

If you're affiliated with an academic institution:

1. Check if your institution has existing Taiwan MOHW FHIR access
2. Request access through your institution's IT or research department
3. Join Taiwan's medical informatics conferences/workshops:
   - Taiwan Association for Medical Informatics (TAMI)
   - Medical Informatics Taiwan conferences

### Method 3: Use Alternative FHIR Server (Temporary)

While waiting for Taiwan MOHW access, test with public FHIR servers:

**Option A: HAPI FHIR Public Test Server**
```
FHIR Base URL: https://hapi.fhir.org/baseR4
No OAuth required - direct API access
```

**Option B: SMART Health IT Sandbox**
```
FHIR Base URL: https://launch.smarthealthit.org/v/r4/fhir
Registration: https://launch.smarthealthit.org/
Public test clients available
```

**Option C: Taiwan HAPI Test Server (If no OAuth required)**
```
FHIR Base URL: https://twcore.hapi.fhir.tw/fhir
May allow direct access without OAuth
```

## Once You Have Client ID

When you receive a client ID from Taiwan MOHW:

### Update Local Configuration

Edit `.env` file:
```bash
SMART_FHIR_BASE_URL=https://thas.mohw.gov.tw/v/r4/sim/[your-token]/fhir
SMART_CLIENT_ID=[your-client-id-from-mohw]
SMART_REDIRECT_URI=http://localhost:8501/callback
```

### Update Streamlit Cloud Secrets

Go to https://share.streamlit.io → Your App → Settings → Secrets:
```toml
[smart]
SMART_FHIR_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/[your-token]/fhir"
SMART_CLIENT_ID = "[your-client-id-from-mohw]"
SMART_REDIRECT_URI = "https://wftmufhir.streamlit.app/callback"
```

### Test OAuth Flow

1. Run local app: `streamlit run streamlit_app.py`
2. Select "SMART on FHIR Login"
3. Click "Start Authentication"
4. Should redirect to Taiwan MOHW authorization page
5. Select patient
6. Should redirect back with valid token

## Why This Is Difficult

Healthcare FHIR servers typically require:
1. **Institutional authorization** for HIPAA/GDPR compliance
2. **Business Associate Agreements** (BAAs)
3. **Security review** of applications
4. **Restricted access** to prevent unauthorized health data access

This is **by design** - healthcare data requires strict access control.

## Alternative: Demo Mode

The app includes a **Demo Mode** that works without any FHIR server:
- Uses sample patient data
- Demonstrates all features
- No OAuth or client registration required
- Available now on: https://wftmufhir.streamlit.app/

## Next Steps

1. **Short-term**: Use Demo Mode to showcase functionality
2. **Medium-term**: Contact Taiwan MOHW for client registration
3. **Long-term**: Once registered, update configuration and test OAuth flow

## Questions?

If you have contacts at Taiwan MOHW or have already registered:
- Check your email for client credentials
- Look for developer documentation they may have sent
- Contact their technical support team

---

**Last Updated**: 2026-01-28
**Status**: Waiting for Taiwan MOHW client registration access
