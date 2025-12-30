"""
REST API Server for Void Suite

Provides programmatic access to all Void Suite functionality.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Provide dummy classes for type hints
    class BaseModel:
        pass
    FastAPI = None

from ..core.device import DeviceDetector
from ..core.backup import AutoBackup
from ..core.system import SystemTweaker
from ..core.auth.authentication import get_auth_manager
from ..core.auth.authorization import AuthorizationManager, Permission


# Pydantic models
class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    session_token: Optional[str] = None
    message: str


class Device Model(BaseModel):
    """Device information"""
    id: str
    manufacturer: str
    model: str
    android_version: str
    state: str


class BackupRequest(BaseModel):
    """Backup request"""
    device_id: str
    include_apps: bool = True
    include_data: bool = True


class BackupResponse(BaseModel):
    """Backup response"""
    success: bool
    backup_path: Optional[str] = None
    message: str


class USBDebugRequest(BaseModel):
    """USB debugging request"""
    device_id: str
    method: str = 'standard'
    force: bool = False


class USBDebugResponse(BaseModel):
    """USB debugging response"""
    success: bool
    adb_enabled: bool
    steps: List[Dict[str, Any]]
    message: str


# Security
security = HTTPBearer() if FASTAPI_AVAILABLE else None


def create_app() -> FastAPI:
    """Create FastAPI application"""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is not installed. Install with: pip install 'void-suite[api]'")
    
    app = FastAPI(
        title="Void Suite API",
        description="Professional Android Device Management & Recovery Toolkit API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Authentication dependency
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify session token"""
        auth_manager = get_auth_manager()
        valid, user_info = auth_manager.validate_session(credentials.credentials)
        
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token"
            )
        
        return user_info
    
    # Routes
    @app.get("/")
    async def root():
        """API root"""
        return {
            "name": "Void Suite API",
            "version": "1.0.0",
            "status": "operational",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Authenticate user"""
        auth_manager = get_auth_manager()
        success, session_token = auth_manager.authenticate(request.username, request.password)
        
        return LoginResponse(
            success=success,
            session_token=session_token,
            message="Login successful" if success else "Invalid credentials"
        )
    
    @app.post("/auth/logout")
    async def logout(user: dict = Depends(get_current_user)):
        """Logout user"""
        # Session token is already validated
        return {"success": True, "message": "Logged out successfully"}
    
    @app.get("/devices", response_model=List[DeviceModel])
    async def list_devices(user: dict = Depends(get_current_user)):
        """List all connected devices"""
        if not AuthorizationManager.has_permission(user['role'], Permission.DEVICE_VIEW):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        devices, _ = DeviceDetector.detect_all()
        return [
            DeviceModel(
                id=d.get('id', ''),
                manufacturer=d.get('manufacturer', 'Unknown'),
                model=d.get('model', 'Unknown'),
                android_version=d.get('android_version', 'Unknown'),
                state=d.get('state', 'unknown')
            )
            for d in devices
        ]
    
    @app.get("/devices/{device_id}")
    async def get_device_info(device_id: str, user: dict = Depends(get_current_user)):
        """Get device information"""
        if not AuthorizationManager.has_permission(user['role'], Permission.DEVICE_VIEW):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        devices, _ = DeviceDetector.detect_all()
        device = next((d for d in devices if d.get('id') == device_id), None)
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return device
    
    @app.post("/devices/{device_id}/backup", response_model=BackupResponse)
    async def create_backup(device_id: str, request: BackupRequest, user: dict = Depends(get_current_user)):
        """Create device backup"""
        if not AuthorizationManager.has_permission(user['role'], Permission.BACKUP_CREATE):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = AutoBackup.create_backup(device_id)
        
        return BackupResponse(
            success=result.get('success', False),
            backup_path=result.get('backup_path'),
            message="Backup created successfully" if result.get('success') else "Backup failed"
        )
    
    @app.post("/devices/{device_id}/usb-debug", response_model=USBDebugResponse)
    async def enable_usb_debugging(device_id: str, request: USBDebugRequest, user: dict = Depends(get_current_user)):
        """Enable USB debugging"""
        if not AuthorizationManager.has_permission(user['role'], Permission.USB_DEBUG):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = SystemTweaker.force_usb_debugging(device_id, request.method)
        
        return USBDebugResponse(
            success=result.get('success', False),
            adb_enabled=result.get('adb_enabled', False),
            steps=result.get('steps', []),
            message="USB debugging enabled" if result.get('success') else "USB debugging failed"
        )
    
    @app.post("/devices/{device_id}/reboot")
    async def reboot_device(device_id: str, mode: str = "system", user: dict = Depends(get_current_user)):
        """Reboot device"""
        if not AuthorizationManager.has_permission(user['role'], Permission.DEVICE_REBOOT):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        from ..core.utils import SafeSubprocess
        
        cmd = ['adb', '-s', device_id, 'reboot']
        if mode != 'system':
            cmd.append(mode)
        
        code, stdout, stderr = SafeSubprocess.run(cmd)
        
        return {
            "success": code == 0,
            "message": f"Device rebooting to {mode}" if code == 0 else f"Reboot failed: {stderr}"
        }
    
    return app


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run API server"""
    if not FASTAPI_AVAILABLE:
        print("FastAPI is not installed. Install with: pip install 'void-suite[api]'")
        return
    
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api_server()
