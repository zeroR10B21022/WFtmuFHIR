# FIXED: Launch Parameter Issue

## The Problem

We were getting this error from Taiwan MOHW:
```
{"error":"invalid_request","error_description":"Invalid launch options: SyntaxError: Unexpected token \u0000 in JSON at position 53"}
```

## Root Cause Identified

After analyzing the Python Flask FHIR client and comparing it to the working JavaScript implementation, I discovered:

**Taiwan MOHW uses Provider Standalone Launch, NOT EHR Launch!**

Looking at [docs/launch.html:56](docs/launch.html#L56), the comment says:
```javascript
// 請求的權限範圍 (Provider Standalone Launch)
// Translation: "Requested permission scope (Provider Standalone Launch)"
```

The JavaScript `FHIR.oauth2.authorize()` call does **NOT** include:
- A `launch` parameter
- "launch" in the scope

## The Two SMART Launch Patterns

### EHR Launch (What We Were Trying To Do)
- Used when app is launched from within an EHR system
- Receives `iss` (FHIR server URL) and `launch` (context token) in URL
- Must include `launch` parameter in OAuth request
- Must include "launch" or "launch/patient" in scope
- Example: `?iss=https://...&launch=eyJhbG...`

### Provider Standalone Launch (What Taiwan MOHW Uses)
- Used when app is launched directly (not from EHR)
- Receives `iss` (FHIR server URL) in URL, or uses hardcoded value
- **NO** `launch` parameter in OAuth request
- **NO** "launch" in scope
- User selects patient during OAuth flow

## What We Changed

### Before (Wrong - EHR Launch)
```python
# Trying to use launch parameter from URL
auth_url = start_oauth_flow(
    fhir_base_url,
    client_id,
    redirect_uri,
    scope + " launch",  # Added "launch" to scope
    launch_token  # Passed launch token
)
```

Authorization URL included:
```
...&scope=...+launch&launch=xyz&...
```

### After (Correct - Provider Standalone Launch)
```python
# Ignore launch parameter, use standalone launch
auth_url = start_oauth_flow(
    fhir_base_url,
    client_id,
    redirect_uri,
    scope,  # NO "launch" in scope
    None    # NO launch parameter
)
```

Authorization URL includes:
```
...&scope=openid+fhirUser+patient/...
```
(No launch parameter at all)

## Additional Improvements

1. **Changed to `urlencode()`**: Now using Python's `urlencode()` like the official fhirclient library, instead of manually building parameter strings with `quote()`

2. **Better debugging**: Debug output now clearly shows it's using Provider Standalone Launch

3. **Validation**: Added warning if launch parameter is accidentally present

## Testing

The app should now work with Taiwan MOHW sandbox:

1. Visit the app URL directly (standalone launch)
2. Click "Start Authentication"
3. Authorization URL will NOT include launch parameter
4. Taiwan MOHW will prompt for patient selection
5. OAuth flow should complete successfully

## References

- [JavaScript launch.html](docs/launch.html) - Working implementation
- [Python Flask FHIR client demo](https://github.com/smart-on-fhir/client-py/blob/main/demos/flask/flask_app.py)
- [Python fhirclient auth.py](https://github.com/smart-on-fhir/client-py/blob/main/fhirclient/auth.py)
- [SMART App Launch Framework](http://www.hl7.org/fhir/smart-app-launch/)

## Files Modified

- [ich_bp_agent/auth/manual_oauth.py](ich_bp_agent/auth/manual_oauth.py) - Changed URL building to use urlencode(), removed launch scope addition
- [ich_bp_agent/auth/streamlit_smart.py](ich_bp_agent/auth/streamlit_smart.py) - Force launch token to None, updated debug output

## Next Steps

Test the app with Taiwan MOHW sandbox. It should now:
- ✅ Generate authorization URL without launch parameter
- ✅ Complete OAuth flow successfully
- ✅ Receive access token and patient context
- ✅ Allow reading/writing FHIR resources
