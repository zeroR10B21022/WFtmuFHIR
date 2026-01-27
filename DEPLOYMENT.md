# Deploying to Streamlit Cloud

This guide explains how to deploy the ICH Blood Pressure Management app to Streamlit Cloud to work with Taiwan MOHW SMART Sandbox.

## Prerequisites

- GitHub account with the WFtmuFHIR repository
- Taiwan MOHW Sandbox account

## Step 1: Create Streamlit Cloud Account

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click "Sign up" and authenticate with your GitHub account (zeroR10B21022)
3. Authorize Streamlit to access your GitHub repositories

## Step 2: Deploy the App

1. Click "New app" in Streamlit Cloud
2. Select your repository: `zeroR10B21022/WFtmuFHIR`
3. Set the branch: `main`
4. Set the main file path: `streamlit_app.py`
5. Click "Deploy"

The app will be deployed to: `https://[your-app-name].streamlit.app`

## Step 3: Configure Secrets

1. In Streamlit Cloud, go to your app settings
2. Click "Secrets" in the left sidebar
3. Add the following secrets (TOML format):

```toml
[smart]
SMART_FHIR_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir"
SMART_CLIENT_ID = "demo_client"
SMART_REDIRECT_URI = "https://[your-app-name].streamlit.app/"
```

Replace `[your-app-name]` with your actual Streamlit Cloud app URL.

4. Click "Save"

## Step 4: Update Config to Use Streamlit Secrets

The app needs to read from Streamlit secrets instead of .env file in production.

Modify `ich_bp_agent/config.py` to check for Streamlit secrets first:

```python
import streamlit as st

# Check if running on Streamlit Cloud
if hasattr(st, 'secrets') and 'smart' in st.secrets:
    SMART_FHIR_BASE_URL = st.secrets.smart.SMART_FHIR_BASE_URL
    SMART_CLIENT_ID = st.secrets.smart.SMART_CLIENT_ID
    SMART_REDIRECT_URI = st.secrets.smart.SMART_REDIRECT_URI
else:
    # Fall back to .env for local development
    # existing code...
```

## Step 5: Test with Taiwan MOHW Sandbox

1. Get your Streamlit Cloud URL: `https://[your-app-name].streamlit.app`
2. Update SMART_REDIRECT_URI in Streamlit secrets
3. In Taiwan MOHW Sandbox, register your app with:
   - **Launch URL**: Your Streamlit Cloud URL
   - **Redirect URI**: Same Streamlit Cloud URL
4. Launch from the sandbox

## Troubleshooting

### App won't start
- Check logs in Streamlit Cloud dashboard
- Verify requirements.txt has all dependencies
- Make sure secrets are properly configured

### OAuth redirect fails
- Verify SMART_REDIRECT_URI matches exactly your Streamlit Cloud URL
- Check that Taiwan MOHW has the correct redirect URI registered

### Module import errors
- Ensure streamlit_app.py correctly imports from ich_bp_agent
- Check that all Python paths are correct

## Next Steps

Once deployed and working:
1. Test the OAuth flow with Taiwan MOHW sandbox
2. Test patient data loading
3. Test blood pressure recording functionality
4. Share your Streamlit Cloud URL with others for testing

## URLs

- **Streamlit Cloud Dashboard**: https://share.streamlit.io/
- **Your GitHub Repo**: https://github.com/zeroR10B21022/WFtmuFHIR
- **Your Deployed App**: `https://[your-app-name].streamlit.app` (after deployment)
