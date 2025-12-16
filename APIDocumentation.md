# API Documentation - Kodi Ticket System

## Overview

This API allows Kodi to communicate with the ticket management system, primarily to register when a user logs in with a PIN.

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### 1. Register Login (Mark Ticket as Used)

Registers that a user has logged in with a specific PIN. This marks the ticket as inactive (changes from green to red).

**Endpoint:** `POST /api/login`

**Request Body:**
```json
{
  "lock_code": "1234"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Login registered successfully",
  "profile": "Kids",
  "length": 60,
  "used_at": "2024-12-16 14:30:45"
}
```

**Error Responses:**

- **400 Bad Request** - Missing lock_code
```json
{
  "error": "lock_code is required"
}
```

- **404 Not Found** - Invalid or already used ticket
```json
{
  "error": "Invalid or inactive ticket"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"lock_code": "1234"}'
```

**Example Python:**
```python
import requests

response = requests.post(
    'http://localhost:5000/api/login',
    json={'lock_code': '1234'}
)

if response.status_code == 200:
    data = response.json()
    print(f"Profile: {data['profile']}")
    print(f"Length: {data['length']} minutes")
else:
    print(f"Error: {response.json()['error']}")
```

---

### 2. Get Ticket Information

Retrieves information about a specific ticket by its lock code.

**Endpoint:** `GET /api/ticket/<lock_code>`

**URL Parameters:**
- `lock_code` - The 4-digit PIN code

**Success Response (200 OK):**
```json
{
  "id": 1,
  "profile_id": 1,
  "profile_name": "Kids",
  "lock_code": "1234",
  "length": 60,
  "is_active": true,
  "used_at": null,
  "created_at": "2024-12-16 14:00:00"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Ticket not found"
}
```

**Example cURL:**
```bash
curl http://localhost:5000/api/ticket/1234
```

**Example Python:**
```python
import requests

response = requests.get('http://localhost:5000/api/ticket/1234')

if response.status_code == 200:
    ticket = response.json()
    print(f"Profile: {ticket['profile_name']}")
    print(f"Active: {ticket['is_active']}")
    print(f"Length: {ticket['length']} minutes")
```

---

## Workflow

### Typical Usage Flow:

1. **Admin creates a ticket** via web interface
   - Profile is selected
   - Length (in minutes) is specified
   - System auto-generates 4-digit PIN
   - Script is executed: `execute-on-kodi_set-passwd-per-profile.sh profile:PIN`
   - Ticket is created in "active" state (green in UI)

2. **Kodi displays the PIN** to the user

3. **User enters PIN on Kodi** to log in

4. **Kodi calls the login API** when authentication succeeds:
   ```bash
   POST /api/login
   {
     "lock_code": "1234"
   }
   ```

5. **System marks ticket as used**
   - `is_active` becomes `false`
   - `used_at` is set to current timestamp
   - Ticket turns red in the web UI

6. **Kodi can optionally check ticket info** before login:
   ```bash
   GET /api/ticket/1234
   ```

---

## Integration Examples

### Kodi Python Addon Example

```python
import requests
import xbmc

def register_login(pin_code):
    """Register that user has logged in with this PIN"""
    url = "http://your-flask-server:5000/api/login"
    
    try:
        response = requests.post(
            url,
            json={"lock_code": pin_code},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            xbmc.log(f"Login registered for profile: {data['profile']}", xbmc.LOGINFO)
            xbmc.log(f"Session length: {data['length']} minutes", xbmc.LOGINFO)
            return True
        else:
            xbmc.log(f"Login registration failed: {response.json()}", xbmc.LOGERROR)
            return False
            
    except Exception as e:
        xbmc.log(f"Error registering login: {str(e)}", xbmc.LOGERROR)
        return False

def check_ticket_valid(pin_code):
    """Check if a PIN is valid and active"""
    url = f"http://your-flask-server:5000/api/ticket/{pin_code}"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            ticket = response.json()
            return ticket['is_active']
        else:
            return False
            
    except Exception as e:
        xbmc.log(f"Error checking ticket: {str(e)}", xbmc.LOGERROR)
        return False
```

### Shell Script Example

```bash
#!/bin/bash
# register_kodi_login.sh

PIN=$1
SERVER="http://localhost:5000"

# Register the login
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"lock_code\": \"$PIN\"}" \
  "$SERVER/api/login")

# Check if successful
if echo "$response" | grep -q '"success": true'; then
    echo "Login registered successfully"
    exit 0
else
    echo "Login registration failed: $response"
    exit 1
fi
```

---

## Error Handling

All API endpoints return JSON responses with appropriate HTTP status codes:

- **200 OK** - Request successful
- **400 Bad Request** - Invalid request data
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

Always check the HTTP status code and handle errors appropriately in your Kodi integration.

---

## Security Considerations

1. **Network Security**: Ensure the Flask server is only accessible from trusted networks
2. **HTTPS**: Use HTTPS in production to encrypt API calls
3. **Rate Limiting**: Consider implementing rate limiting to prevent abuse
4. **PIN Uniqueness**: The system ensures all PINs are unique
5. **One-time Use**: Each ticket can only be used once (marked inactive after login)

---

## Testing with curl

```bash
# Test login registration
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"lock_code": "1234"}'

# Test get ticket info
curl http://localhost:5000/api/ticket/1234

# Test with invalid PIN
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"lock_code": "9999"}'

# Test missing lock_code
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{}'
```