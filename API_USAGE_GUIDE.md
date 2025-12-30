# API Dependencies - Complete Installation and Usage Guide

## Quick Start

### Installing API Dependencies

The API dependencies are optional and need to be installed separately:

```bash
# Install Void Suite with API support
pip install void-suite[api]

# Or if installing from source
cd void
pip install -e .[api]

# Or install all optional dependencies (GUI + API + Dev)
pip install -e .[gui,api,dev]
```

### What Gets Installed

When you install `void-suite[api]`, you get:

```
fastapi>=0.104.0           # Modern web framework
uvicorn[standard]>=0.24.0  # ASGI server with extras (websockets, etc.)
pydantic>=2.0.0            # Data validation
```

---

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# From the void directory
cd /path/to/void

# Install with API dependencies
pip install -e .[api]

# Verify installation
python -c "import fastapi; import uvicorn; print('✅ API dependencies installed!')"
```

### 2. Start the API Server

#### Method 1: Using the built-in runner

```bash
# Start API server (default: http://0.0.0.0:8000)
python -m void.api.server
```

#### Method 2: Using uvicorn directly

```bash
# Basic start
uvicorn void.api.server:create_app --reload

# With custom host and port
uvicorn void.api.server:create_app --host 0.0.0.0 --port 8080

# With auto-reload (development)
uvicorn void.api.server:create_app --reload --host 127.0.0.1 --port 8000

# Production mode (multiple workers)
uvicorn void.api.server:create_app --host 0.0.0.0 --port 8000 --workers 4
```

#### Method 3: Python script

```python
# my_api_server.py
from void.api.server import run_api_server

if __name__ == '__main__':
    run_api_server(host='0.0.0.0', port=8000)
```

```bash
python my_api_server.py
```

### 3. Access the API

Once running, the API is available at:

- **API Root**: http://localhost:8000/
- **Swagger UI (Interactive Docs)**: http://localhost:8000/api/docs
- **ReDoc (Alternative Docs)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

---

## Using the API

### 1. Login to Get Token

```bash
# Using curl
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Response:
{
  "success": true,
  "session_token": "xK9d3Lm2Pq8Rz1Vb4Nc7Jh6Fg5Yw0Xe3Ta8Uh2Sg1Df",
  "message": "Login successful"
}
```

### 2. Make Authenticated Requests

```bash
# Save token to variable
TOKEN="xK9d3Lm2Pq8Rz1Vb4Nc7Jh6Fg5Yw0Xe3Ta8Uh2Sg1Df"

# List devices
curl -X GET http://localhost:8000/devices \
  -H "Authorization: Bearer $TOKEN"

# Get device info
curl -X GET http://localhost:8000/devices/emulator-5554 \
  -H "Authorization: Bearer $TOKEN"

# Create backup
curl -X POST http://localhost:8000/devices/emulator-5554/backup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "emulator-5554", "include_apps": true, "include_data": true}'

# Enable USB debugging
curl -X POST http://localhost:8000/devices/emulator-5554/usb-debug \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "emulator-5554", "method": "standard", "force": false}'

# Reboot device
curl -X POST "http://localhost:8000/devices/emulator-5554/reboot?mode=recovery" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Python Client Example

### Basic Client

```python
import requests

class VoidAPIClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        """Login and store token"""
        response = requests.post(
            f'{self.base_url}/auth/login',
            json={'username': username, 'password': password}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                self.token = data['session_token']
                print(f"✅ Logged in as {username}")
                return True
        
        print(f"❌ Login failed: {response.json()}")
        return False
    
    def _headers(self):
        """Get authorization headers"""
        if not self.token:
            raise ValueError("Not logged in. Call login() first.")
        return {'Authorization': f'Bearer {self.token}'}
    
    def get_devices(self):
        """Get all connected devices"""
        response = requests.get(
            f'{self.base_url}/devices',
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_device(self, device_id):
        """Get specific device info"""
        response = requests.get(
            f'{self.base_url}/devices/{device_id}',
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def create_backup(self, device_id, include_apps=True, include_data=True):
        """Create device backup"""
        response = requests.post(
            f'{self.base_url}/devices/{device_id}/backup',
            headers=self._headers(),
            json={
                'device_id': device_id,
                'include_apps': include_apps,
                'include_data': include_data
            }
        )
        response.raise_for_status()
        return response.json()
    
    def enable_usb_debugging(self, device_id, method='standard', force=False):
        """Enable USB debugging"""
        response = requests.post(
            f'{self.base_url}/devices/{device_id}/usb-debug',
            headers=self._headers(),
            json={
                'device_id': device_id,
                'method': method,
                'force': force
            }
        )
        response.raise_for_status()
        return response.json()
    
    def reboot_device(self, device_id, mode='system'):
        """Reboot device"""
        response = requests.post(
            f'{self.base_url}/devices/{device_id}/reboot',
            headers=self._headers(),
            params={'mode': mode}
        )
        response.raise_for_status()
        return response.json()
    
    def logout(self):
        """Logout"""
        response = requests.post(
            f'{self.base_url}/auth/logout',
            headers=self._headers()
        )
        self.token = None
        return response.json()


# Usage example
if __name__ == '__main__':
    # Create client
    client = VoidAPIClient('http://localhost:8000')
    
    # Login
    if not client.login('admin', 'admin'):
        exit(1)
    
    # Get devices
    devices = client.get_devices()
    print(f"\n📱 Found {len(devices)} devices:")
    for device in devices:
        print(f"  • {device['id']} - {device['manufacturer']} {device['model']}")
    
    # Get first device details
    if devices:
        device_id = devices[0]['id']
        device_info = client.get_device(device_id)
        print(f"\n📊 Device Info:")
        print(f"  ID: {device_info['id']}")
        print(f"  Model: {device_info['model']}")
        print(f"  Android: {device_info['android_version']}")
    
    # Enable USB debugging
    if devices:
        print(f"\n🔌 Enabling USB debugging...")
        result = client.enable_usb_debugging(device_id, method='standard')
        print(f"  Result: {result['message']}")
        print(f"  ADB Enabled: {result['adb_enabled']}")
    
    # Logout
    client.logout()
    print("\n✅ Logged out")
```

Save this as `void_client.py` and run:

```bash
python void_client.py
```

---

## Advanced Usage

### Using Requests Session

```python
import requests

class VoidAPISession:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username, password):
        """Login and configure session"""
        response = self.session.post(
            f'{self.base_url}/auth/login',
            json={'username': username, 'password': password}
        )
        
        if response.status_code == 200 and response.json()['success']:
            token = response.json()['session_token']
            # Set token for all future requests
            self.session.headers.update({'Authorization': f'Bearer {token}'})
            return True
        return False
    
    def get(self, endpoint):
        """GET request"""
        return self.session.get(f'{self.base_url}{endpoint}')
    
    def post(self, endpoint, json=None):
        """POST request"""
        return self.session.post(f'{self.base_url}{endpoint}', json=json)

# Usage
api = VoidAPISession()
api.login('admin', 'admin')

# Now all requests are authenticated
devices = api.get('/devices').json()
backup = api.post('/devices/emulator-5554/backup', json={'device_id': 'emulator-5554'}).json()
```

### Async Client (using httpx)

```python
import httpx
import asyncio

class AsyncVoidClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.token = None
    
    async def login(self, username, password):
        """Async login"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/auth/login',
                json={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.token = data['session_token']
                    return True
        return False
    
    async def get_devices(self):
        """Async get devices"""
        headers = {'Authorization': f'Bearer {self.token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self.base_url}/devices',
                headers=headers
            )
            return response.json()
    
    async def create_backup(self, device_id):
        """Async create backup"""
        headers = {'Authorization': f'Bearer {self.token}'}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/devices/{device_id}/backup',
                headers=headers,
                json={'device_id': device_id}
            )
            return response.json()

# Usage
async def main():
    client = AsyncVoidClient()
    await client.login('admin', 'admin')
    
    devices = await client.get_devices()
    print(f"Found {len(devices)} devices")
    
    if devices:
        result = await client.create_backup(devices[0]['id'])
        print(f"Backup: {result['message']}")

asyncio.run(main())
```

---

## Interactive Testing with Swagger UI

### Access Swagger UI

1. Start the API server
2. Open browser: http://localhost:8000/api/docs
3. You'll see an interactive API documentation

### How to Use Swagger UI

1. **Click "Authorize" button** (top right)
2. **Login first** using the `/auth/login` endpoint:
   - Click on `POST /auth/login`
   - Click "Try it out"
   - Enter credentials:
     ```json
     {
       "username": "admin",
       "password": "admin"
     }
     ```
   - Click "Execute"
   - Copy the `session_token` from the response

3. **Set Authorization**:
   - Click "Authorize" button again
   - Paste token in "Value" field (format: `Bearer your_token_here`)
   - Click "Authorize"
   - Click "Close"

4. **Test Other Endpoints**:
   - Now you can test any endpoint
   - Click on endpoint → "Try it out" → Fill parameters → "Execute"

---

## Troubleshooting

### Error: "FastAPI is not installed"

```bash
# Solution: Install API dependencies
pip install fastapi uvicorn pydantic

# Or use the bundle
pip install void-suite[api]
```

### Error: "ModuleNotFoundError: No module named 'fastapi'"

```bash
# Check if installed
pip list | grep fastapi

# If not found, install
pip install -e .[api]
```

### Error: "Port 8000 already in use"

```bash
# Use different port
uvicorn void.api.server:create_app --port 8080

# Or find and kill process using port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: "401 Unauthorized"

```bash
# Your token expired or is invalid
# Solution: Login again to get new token

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### Error: "403 Forbidden"

```bash
# Your user role doesn't have permission
# Solution: Login with user that has required permission

# Example: operator can backup, but viewer cannot
# Create operator user or login as admin
```

---

## Production Deployment

### Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn void.api.server:create_app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .[api]

# Copy code
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "void.api.server:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t void-api .
docker run -p 8000:8000 void-api
```

### Behind Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/void-api
server {
    listen 80;
    server_name api.void.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With SSL/TLS

```bash
# Use certbot for Let's Encrypt
sudo certbot --nginx -d api.void.example.com

# Or use uvicorn with SSL
uvicorn void.api.server:create_app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

---

## Configuration

### Environment Variables

```bash
# Set API configuration via environment
export VOID_API_HOST=0.0.0.0
export VOID_API_PORT=8000
export VOID_API_WORKERS=4
export VOID_AUTH_DB=/path/to/auth.db
```

### Custom Configuration

```python
# config.py
import os

API_HOST = os.getenv('VOID_API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('VOID_API_PORT', 8000))
API_WORKERS = int(os.getenv('VOID_API_WORKERS', 4))

# Use in server
from void.api.server import create_app
import uvicorn

app = create_app()
uvicorn.run(app, host=API_HOST, port=API_PORT, workers=API_WORKERS)
```

---

## Testing the API

### Using pytest

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from void.api.server import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_login(client):
    response = client.post('/auth/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert 'session_token' in response.json()

def test_get_devices_requires_auth(client):
    response = client.get('/devices')
    assert response.status_code == 403  # No auth header
```

```bash
# Run API tests
pytest tests/test_api.py -v
```

---

## Summary

✅ **Install**: `pip install void-suite[api]`  
✅ **Start Server**: `python -m void.api.server`  
✅ **Access Docs**: http://localhost:8000/api/docs  
✅ **Login**: POST to `/auth/login` to get token  
✅ **Use Token**: Add `Authorization: Bearer <token>` header  
✅ **Test**: Use Swagger UI or Python client  

**You're ready to use the Void Suite API!** 🚀

---

## Quick Reference

```bash
# Install
pip install void-suite[api]

# Start
python -m void.api.server

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use API
curl -X GET http://localhost:8000/devices \
  -H "Authorization: Bearer YOUR_TOKEN"

# Docs
http://localhost:8000/api/docs
```

---

**Copyright © 2024 Roach Labs. All rights reserved.**  
**Made by James Michael Roach Jr.**
