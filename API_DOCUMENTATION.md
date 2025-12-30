# Void Suite REST API Documentation

## Overview

The Void Suite REST API provides programmatic access to all Android device management features.

## Installation

```bash
pip install void-suite[api]
```

## Running the API Server

```bash
# Start the API server
python -m void.api.server

# Or use uvicorn directly
uvicorn void.api.server:create_app --host 0.0.0.0 --port 8000
```

## Authentication

All API endpoints (except `/auth/login`) require authentication using a session token.

### Login

```bash
POST /auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "your_password"
}

Response:
{
    "success": true,
    "session_token": "your_token_here",
    "message": "Login successful"
}
```

### Using the Token

Include the token in the Authorization header:

```bash
Authorization: Bearer your_token_here
```

## API Endpoints

### Health Check

```bash
GET /health

Response:
{
    "status": "healthy",
    "timestamp": "2024-12-30T13:00:00"
}
```

### List Devices

```bash
GET /devices
Authorization: Bearer your_token

Response:
[
    {
        "id": "emulator-5554",
        "manufacturer": "Google",
        "model": "Pixel 5",
        "android_version": "11",
        "state": "device"
    }
]
```

### Get Device Info

```bash
GET /devices/{device_id}
Authorization: Bearer your_token

Response:
{
    "id": "emulator-5554",
    "manufacturer": "Google",
    "model": "Pixel 5",
    ...
}
```

### Create Backup

```bash
POST /devices/{device_id}/backup
Authorization: Bearer your_token
Content-Type: application/json

{
    "device_id": "emulator-5554",
    "include_apps": true,
    "include_data": true
}

Response:
{
    "success": true,
    "backup_path": "/home/user/.void/backups/backup_123.tar",
    "message": "Backup created successfully"
}
```

### Enable USB Debugging

```bash
POST /devices/{device_id}/usb-debug
Authorization: Bearer your_token
Content-Type: application/json

{
    "device_id": "emulator-5554",
    "method": "standard",
    "force": false
}

Response:
{
    "success": true,
    "adb_enabled": true,
    "steps": [...],
    "message": "USB debugging enabled"
}
```

### Reboot Device

```bash
POST /devices/{device_id}/reboot?mode=recovery
Authorization: Bearer your_token

Response:
{
    "success": true,
    "message": "Device rebooting to recovery"
}
```

## Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Role-Based Access Control

The API enforces role-based permissions:

- **Viewer**: Can only view devices and apps
- **Operator**: Can perform backups, install apps, enable USB debugging
- **Advanced**: Can perform EDL operations, FRP bypass, recovery mode
- **Admin**: Full access to all operations + user management

## Rate Limiting

API rate limiting is configured per role:
- Viewer: 60 requests/minute
- Operator: 120 requests/minute
- Advanced: 240 requests/minute
- Admin: Unlimited

## Security

- All passwords are hashed with PBKDF2-SHA256
- Sessions expire after 8 hours of inactivity
- Account lockout after 5 failed login attempts (15 minutes)
- All actions are logged for audit

## Example: Python Client

```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', json={
    'username': 'admin',
    'password': 'your_password'
})
token = response.json()['session_token']

# List devices
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/devices', headers=headers)
devices = response.json()

# Enable USB debugging
response = requests.post(
    f'http://localhost:8000/devices/{devices[0]["id"]}/usb-debug',
    headers=headers,
    json={'method': 'standard', 'force': False}
)
print(response.json())
```

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `500`: Server error

Error response format:
```json
{
    "detail": "Error message here"
}
```

## Support

For API issues, please file an issue on GitHub: https://github.com/xroachx-ghost/void/issues
