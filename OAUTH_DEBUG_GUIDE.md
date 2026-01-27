# OAuth Debugging Guide

## What Changed

I've updated the Python OAuth implementation to **exactly match** the JavaScript fhirclient.js behavior:

### Key Fixes

1. **'aud' parameter**: Now uses FHIR base URL directly (not derived from authorize_url)
2. **'launch' scope**: Automatically adds " launch" to scope when launch token exists (not "launch/patient")
3. **URL encoding**: Uses `quote(safe='')` to match JavaScript's `encodeURIComponent()`
4. **Parameter validation**: Strips whitespace and validates launch token before use

### What to Check

When you test the app, **EXPAND THE DEBUG SECTIONS** and look for:

#### 1. Launch Token Information
```
Launch Token Value: '<the actual token>'
Launch Token Type: str
Launch Token Length: <number>
```

**Check for:**
- Is the launch token valid? Or is it None/"None"/empty string?
- Does it contain any unusual characters or null bytes?
- Does the length seem reasonable?

#### 2. Authorization URL Parameters

The debug output shows each parameter separately. Compare with what JavaScript would send:

**Expected for EHR Launch:**
```
response_type = code
client_id = demo_client
scope = openid fhirUser patient/Patient.read ... launch
redirect_uri = https://wftmufhir.streamlit.app/
aud = <FHIR base URL>
state = <random string>
launch = <the launch token>
```

**Check for:**
- Is "launch" in the scope? (it should be if you have a launch token)
- Is the launch parameter present and properly encoded?
- Does the aud match the FHIR base URL exactly?

#### 3. Launch Bytes

If there's a launch parameter, you'll see:
```
Launch bytes: b'...'
```

**Check for:**
- Any `\x00` (null bytes) in the output
- Any unexpected characters or encoding issues

## Common Issues

### Issue 1: No Launch Token in EHR Launch
If you're using EHR Launch but the debug shows no launch token, the `?launch=...` parameter might not be in the URL when you first visit the app.

### Issue 2: Launch Token is "None" String
If `Launch Token Value: 'None'` appears, something is passing the string "None" instead of an actual token or None.

### Issue 3: Launch Parameter Has Null Bytes
If the Taiwan MOHW error mentions "position 53" and you see `\x00` in the launch bytes, the token itself is corrupted.

## Testing Steps

### Test 1: Standalone Launch (No Launch Token)
1. Visit: `https://wftmufhir.streamlit.app/`
2. Should NOT have launch parameter
3. Should NOT have "launch" in scope

### Test 2: EHR Launch (With Launch Token)
1. Start from Taiwan MOHW sandbox EHR launch
2. URL should have `?iss=...&launch=...`
3. Debug should show launch token value
4. Authorization URL should include `launch=<encoded token>`
5. Scope should include "launch"

## Manual Testing with test_oauth_url.py

Run the test script locally to see what URLs the Python code generates:

```bash
python test_oauth_url.py
```

This will show:
- URL for standalone launch
- URL for EHR launch with sample token
- Expected JavaScript behavior

Compare the Python output with what the JavaScript `launch.html` would generate.

## Next Steps

Based on the debug output, we can identify:
1. **If launch token is the problem**: Check how Taiwan MOHW passes it
2. **If encoding is the problem**: Try different encoding methods
3. **If URL structure is wrong**: Adjust parameter order or format

**Please test and share the debug output from the expanded sections!**
