# ICH Blood Pressure Management Web App

This is the web-based version of the ICH BP Management app using static HTML/JavaScript.

## GitHub Pages URL

Once deployed, your app will be available at:
**https://zeroR10B21022.github.io/WFtmuFHIR/**

## Usage

### For Taiwan MOHW Sandbox Registration:

**Launch URL (register this with sandbox):**
```
https://zeroR10B21022.github.io/WFtmuFHIR/launch.html
```

**Redirect URI:**
```
https://zeroR10B21022.github.io/WFtmuFHIR/index.html
```

### Direct Access (Provider Standalone Launch):

If the sandbox doesn't require registration, you can access directly:
```
https://zeroR10B21022.github.io/WFtmuFHIR/launch.html?iss=YOUR_FHIR_SERVER_URL
```

## Files

- `launch.html` - OAuth2 authorization entry point
- `index.html` - Main application page (after authorization)
- `app.js` - Application logic

## Technology

- SMART on FHIR JavaScript client
- Pure HTML/CSS/JavaScript (no build required)
- Works with any FHIR R4 server supporting SMART authorization
