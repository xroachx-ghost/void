# Authentication & Authorization System - User Guide

## Overview

The Void Suite authentication and authorization system provides:
- **Authentication**: Who you are (login, sessions, passwords)
- **Authorization**: What you can do (roles, permissions, access control)

---

## How It Works

### Architecture

```
User Login → Authentication → Session Token → Authorization Check → Action
     ↓                                              ↓
  Password Hash                              Permission Check
  + Salt                                     based on Role
```

### Components

1. **AuthenticationManager** - Handles login, sessions, users
2. **AuthorizationManager** - Handles roles, permissions, access control
3. **Database** - SQLite database stores users, sessions, audit logs

---

## Quick Start

### 1. Basic Login (CLI/Script)

```python
from void.core.auth.authentication import get_auth_manager

# Get the authentication manager
auth = get_auth_manager()

# Login with default admin account
success, token = auth.authenticate('admin', 'admin')

if success:
    print(f"Login successful! Token: {token}")
else:
    print("Login failed!")
```

### 2. Create a New User

```python
from void.core.auth.authentication import get_auth_manager

auth = get_auth_manager()

# Create user with role
# Roles: 'viewer', 'operator', 'advanced', 'admin'
success = auth.create_user(
    username='john',
    password='SecurePassword123!',
    role='operator'
)

if success:
    print("User created!")
else:
    print("Username already exists!")
```

### 3. Check Permissions

```python
from void.core.auth.authorization import AuthorizationManager, Permission

# Check if user can perform action
role = 'operator'

# Check specific permission
can_backup = AuthorizationManager.has_permission(role, Permission.BACKUP_CREATE)
print(f"Can create backup: {can_backup}")  # True for operator

# Check by action name
can_frp = AuthorizationManager.can_perform_action(role, 'frp_bypass')
print(f"Can bypass FRP: {can_frp}")  # False for operator (needs 'advanced' role)
```

---

## Detailed Usage

### Authentication Manager

#### Create Users

```python
from void.core.auth.authentication import get_auth_manager

auth = get_auth_manager()

# Create different role users
auth.create_user('viewer_user', 'password123', 'viewer')     # Read-only
auth.create_user('operator_user', 'password123', 'operator') # Standard ops
auth.create_user('advanced_user', 'password123', 'advanced') # Advanced ops
auth.create_user('admin_user', 'password123', 'admin')       # Full access
```

#### Login / Authenticate

```python
# Login returns (success: bool, token: str)
success, token = auth.authenticate('operator_user', 'password123')

if success:
    # Token is a secure random string (32 bytes URL-safe base64)
    # Example: "xK9d3Lm2Pq8Rz1Vb4Nc7Jh6Fg5Yw0Xe3Ta8Uh2Sg1Df"
    print(f"Logged in! Token: {token}")
    
    # Token expires after 8 hours of inactivity
```

#### Validate Session

```python
# Check if token is still valid
valid, user_info = auth.validate_session(token)

if valid:
    print(f"User: {user_info['username']}")
    print(f"Role: {user_info['role']}")
    print(f"User ID: {user_info['user_id']}")
else:
    print("Session expired or invalid!")
```

#### Logout

```python
# Invalidate session token
auth.logout(token)
print("Logged out successfully!")
```

---

## Authorization Manager

### Roles Explained

| Role | Description | Use Case |
|------|-------------|----------|
| **Viewer** | Read-only access | View devices, apps (no modifications) |
| **Operator** | Standard operations | Backups, app install/uninstall, USB debug |
| **Advanced** | Advanced operations | EDL, FRP bypass, recovery mode, root ops |
| **Admin** | Full access | Everything + user management, config |

### Permissions List

```python
from void.core.auth.authorization import Permission

# Device permissions
Permission.DEVICE_VIEW       # View device list and info
Permission.DEVICE_CONNECT    # Connect to devices
Permission.DEVICE_REBOOT     # Reboot devices

# Backup permissions
Permission.BACKUP_CREATE     # Create backups
Permission.BACKUP_RESTORE    # Restore backups
Permission.BACKUP_DELETE     # Delete backups

# App permissions
Permission.APP_LIST          # List apps
Permission.APP_INSTALL       # Install apps
Permission.APP_UNINSTALL     # Uninstall apps

# System permissions
Permission.SYSTEM_TWEAK      # System tweaks (DPI, animations)
Permission.SYSTEM_ROOT       # Root operations
Permission.USB_DEBUG         # USB debugging

# Advanced permissions
Permission.EDL_ACCESS        # EDL mode operations
Permission.FRP_BYPASS        # FRP bypass
Permission.RECOVERY_MODE     # Recovery mode

# Admin permissions
Permission.USER_MANAGE       # User management
Permission.AUDIT_VIEW        # View audit logs
Permission.CONFIG_MANAGE     # Manage configuration
```

### Check Permissions

```python
from void.core.auth.authorization import AuthorizationManager, Permission

role = 'operator'

# Method 1: Check specific permission
can_backup = AuthorizationManager.has_permission(role, Permission.BACKUP_CREATE)
# Returns: True (operators can create backups)

can_edl = AuthorizationManager.has_permission(role, Permission.EDL_ACCESS)
# Returns: False (operators cannot use EDL)

# Method 2: Check by action name
can_install_app = AuthorizationManager.can_perform_action(role, 'install_app')
# Returns: True

# Method 3: Get all permissions for role
permissions = AuthorizationManager.get_role_permissions(role)
print(f"Operator has {len(permissions)} permissions")
```

---

## Security Features

### Password Security

```python
# Passwords are NEVER stored in plain text!
# Uses PBKDF2-SHA256 with random salt

# When you create a user:
auth.create_user('john', 'password123', 'operator')

# What happens internally:
# 1. Generate random salt (16 bytes)
# 2. Hash password with salt (100,000 iterations)
# 3. Store: username, password_hash, salt
# 4. Original password is NEVER stored
```

### Account Lockout

```python
# After 5 failed login attempts, account locks for 15 minutes

# Try 5 failed logins
for i in range(5):
    auth.authenticate('john', 'wrong_password')

# 6th attempt will fail even with correct password
success, token = auth.authenticate('john', 'correct_password')
# Returns: (False, None) - Account locked

# Wait 15 minutes or admin must unlock
```

### Session Expiry

```python
# Sessions expire after 8 hours of inactivity

success, token = auth.authenticate('john', 'password123')
# Token valid for 8 hours

# Each time you validate_session(), the expiry extends
valid, user_info = auth.validate_session(token)
# Expiry now reset to 8 hours from now

# After 8 hours of no activity, token expires
```

### Audit Logging

```python
# All authentication events are logged

# Logged events:
# - user_created
# - login_success
# - login_failed
# - session_expired
# - logout

# Logs include:
# - Username
# - Action
# - Success/failure
# - IP address (if provided)
# - Timestamp
# - Details (failure reason)
```

---

## Integration Examples

### Example 1: Protecting a Function

```python
from void.core.auth.authorization import require_permission, Permission

@require_permission(Permission.BACKUP_CREATE)
def create_backup(device_id, user_role='viewer'):
    """Create backup - requires BACKUP_CREATE permission"""
    # This function will only execute if user has permission
    print(f"Creating backup for {device_id}")
    return {'success': True}

# Usage
try:
    create_backup('emulator-5554', user_role='operator')  # Works!
    create_backup('emulator-5554', user_role='viewer')    # Raises PermissionError!
except PermissionError as e:
    print(f"Access denied: {e}")
```

### Example 2: CLI Authentication

```python
from void.core.auth.authentication import get_auth_manager
from void.core.auth.authorization import AuthorizationManager, Permission

def cli_login():
    """CLI login prompt"""
    auth = get_auth_manager()
    
    username = input("Username: ")
    password = input("Password: ")
    
    success, token = auth.authenticate(username, password)
    
    if not success:
        print("❌ Login failed!")
        return None
    
    # Validate and get user info
    valid, user_info = auth.validate_session(token)
    
    print(f"✅ Welcome {user_info['username']}!")
    print(f"   Role: {user_info['role']}")
    
    return token, user_info

def cli_backup(token, device_id):
    """CLI backup command with auth check"""
    auth = get_auth_manager()
    
    # Validate session
    valid, user_info = auth.validate_session(token)
    if not valid:
        print("❌ Session expired. Please login again.")
        return
    
    # Check permission
    if not AuthorizationManager.has_permission(user_info['role'], Permission.BACKUP_CREATE):
        print(f"❌ Permission denied. Role '{user_info['role']}' cannot create backups.")
        return
    
    # Proceed with backup
    print(f"✅ Creating backup for {device_id}...")
    # ... backup logic ...

# Usage
token, user_info = cli_login()
if token:
    cli_backup(token, 'emulator-5554')
```

### Example 3: API Authentication

```python
# Already implemented in void/api/server.py!

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    """Verify session token from API request"""
    auth = get_auth_manager()
    valid, user_info = auth.validate_session(credentials.credentials)
    
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_info

# Use in endpoint
@app.get("/devices")
async def list_devices(user: dict = Depends(get_current_user)):
    """List devices - requires authentication"""
    # user contains: {'user_id': 1, 'username': 'john', 'role': 'operator'}
    
    # Check permission
    if not AuthorizationManager.has_permission(user['role'], Permission.DEVICE_VIEW):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Return devices
    return get_devices()
```

---

## GUI Integration (Planned)

### Login Dialog

```python
import tkinter as tk
from void.core.auth.authentication import get_auth_manager

class LoginDialog:
    def __init__(self, parent):
        self.parent = parent
        self.token = None
        self.user_info = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Void Suite - Login")
        
        # Username
        tk.Label(self.dialog, text="Username:").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.dialog)
        self.username_entry.grid(row=0, column=1)
        
        # Password
        tk.Label(self.dialog, text="Password:").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.dialog, show="*")
        self.password_entry.grid(row=1, column=1)
        
        # Login button
        tk.Button(self.dialog, text="Login", command=self.login).grid(row=2, columnspan=2)
    
    def login(self):
        auth = get_auth_manager()
        
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        success, token = auth.authenticate(username, password)
        
        if success:
            self.token = token
            valid, self.user_info = auth.validate_session(token)
            self.dialog.destroy()
        else:
            tk.messagebox.showerror("Login Failed", "Invalid credentials")

# Usage
login = LoginDialog(root)
root.wait_window(login.dialog)

if login.token:
    print(f"Logged in as {login.user_info['username']}")
    # Continue with authenticated session
```

---

## Database Schema

The authentication system uses SQLite with 3 tables:

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active INTEGER DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TEXT
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_activity TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Audit Log Table
```sql
CREATE TABLE auth_audit (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    success INTEGER NOT NULL,
    ip_address TEXT,
    timestamp TEXT NOT NULL,
    details TEXT
);
```

**Location:** `~/.void/auth.db`

---

## Common Use Cases

### Use Case 1: Multi-User Environment

```python
from void.core.auth.authentication import get_auth_manager

auth = get_auth_manager()

# Create users for team
auth.create_user('alice', 'alice_pass', 'admin')      # Team lead
auth.create_user('bob', 'bob_pass', 'operator')       # Standard tech
auth.create_user('charlie', 'charlie_pass', 'viewer') # Manager (read-only)

# Each user logs in with their credentials
success, alice_token = auth.authenticate('alice', 'alice_pass')
success, bob_token = auth.authenticate('bob', 'bob_pass')

# Alice can do admin tasks
valid, alice_info = auth.validate_session(alice_token)
if AuthorizationManager.has_permission(alice_info['role'], Permission.USER_MANAGE):
    print("Alice can manage users")

# Bob cannot
valid, bob_info = auth.validate_session(bob_token)
if not AuthorizationManager.has_permission(bob_info['role'], Permission.USER_MANAGE):
    print("Bob cannot manage users")
```

### Use Case 2: Automated Scripts

```python
#!/usr/bin/env python3
"""Automated backup script with authentication"""

from void.core.auth.authentication import get_auth_manager
from void.core.auth.authorization import AuthorizationManager, Permission
from void.core.backup import AutoBackup
import sys

def authenticated_backup(username, password, device_id):
    """Run backup with authentication"""
    auth = get_auth_manager()
    
    # Authenticate
    success, token = auth.authenticate(username, password)
    if not success:
        print("❌ Authentication failed")
        return False
    
    # Check permission
    valid, user_info = auth.validate_session(token)
    if not AuthorizationManager.has_permission(user_info['role'], Permission.BACKUP_CREATE):
        print(f"❌ User '{username}' does not have backup permission")
        auth.logout(token)
        return False
    
    # Create backup
    print(f"✅ Creating backup as {username}...")
    result = AutoBackup.create_backup(device_id)
    
    # Logout
    auth.logout(token)
    
    return result['success']

if __name__ == '__main__':
    # Usage: python backup_script.py operator_user password123 emulator-5554
    if len(sys.argv) != 4:
        print("Usage: backup_script.py <username> <password> <device_id>")
        sys.exit(1)
    
    success = authenticated_backup(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if success else 1)
```

### Use Case 3: API Client

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
                return True
        return False
    
    def get_devices(self):
        """Get devices (requires authentication)"""
        if not self.token:
            raise ValueError("Not logged in")
        
        response = requests.get(
            f'{self.base_url}/devices',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if response.status_code == 401:
            raise ValueError("Session expired")
        
        return response.json()
    
    def create_backup(self, device_id):
        """Create backup (requires permissions)"""
        response = requests.post(
            f'{self.base_url}/devices/{device_id}/backup',
            headers={'Authorization': f'Bearer {self.token}'},
            json={'include_apps': True, 'include_data': True}
        )
        
        if response.status_code == 403:
            raise PermissionError("Insufficient permissions")
        
        return response.json()

# Usage
client = VoidAPIClient()
client.login('operator_user', 'password123')

devices = client.get_devices()
print(f"Found {len(devices)} devices")

result = client.create_backup(devices[0]['id'])
print(f"Backup: {result['message']}")
```

---

## FAQ

### Q: Where is the database stored?
**A:** `~/.void/auth.db` (in your home directory)

### Q: What is the default admin password?
**A:** Username: `admin`, Password: `admin`  
**⚠️ CHANGE THIS IMMEDIATELY in production!**

### Q: How do I change a password?
**A:** Currently requires direct database access. Password change API coming soon!

```python
# Workaround: Delete user and recreate
import sqlite3
from pathlib import Path

db = Path.home() / '.void' / 'auth.db'
conn = sqlite3.connect(db)
conn.execute('DELETE FROM users WHERE username = ?', ('john',))
conn.commit()

# Then create with new password
auth.create_user('john', 'new_password', 'operator')
```

### Q: Can I disable authentication?
**A:** Yes, just don't use it! The system is optional. If you don't call authentication functions, Void Suite works normally.

### Q: How do I view audit logs?
**A:** Direct database access or create admin tool:

```python
import sqlite3
from pathlib import Path

db = Path.home() / '.void' / 'auth.db'
conn = sqlite3.connect(db)
cursor = conn.execute('SELECT * FROM auth_audit ORDER BY timestamp DESC LIMIT 10')

for row in cursor:
    print(f"{row[5]} - {row[1]} - {row[2]} - {'Success' if row[3] else 'Failed'}")
```

### Q: What happens if I lose my token?
**A:** Just login again to get a new token. Old token remains valid until expiry.

### Q: Can multiple users login simultaneously?
**A:** Yes! Each user can have multiple active sessions.

### Q: Is this production-ready?
**A:** Yes for internal use. For internet-facing production, add:
- HTTPS/TLS
- Rate limiting
- 2FA/MFA
- Password complexity requirements
- Session management UI

---

## Next Steps

1. **Change default admin password:**
   ```python
   # Delete and recreate admin with strong password
   auth.create_user('admin', 'YourStrongPassword123!', 'admin')
   ```

2. **Create your users:**
   ```python
   auth.create_user('your_username', 'your_password', 'operator')
   ```

3. **Test authentication:**
   ```python
   success, token = auth.authenticate('your_username', 'your_password')
   ```

4. **Integrate into your workflow!**

---

## Summary

✅ **Authentication**: Login, sessions, password security, lockout protection  
✅ **Authorization**: 4 roles, 15+ permissions, granular access control  
✅ **Security**: PBKDF2-SHA256, sessions, audit logs, lockout  
✅ **Integration**: CLI, API, GUI ready, decorator support  

**You're ready to use enterprise-grade authentication!** 🔐

---

**Copyright © 2024 Roach Labs. All rights reserved.**  
**Made by James Michael Roach Jr.**
