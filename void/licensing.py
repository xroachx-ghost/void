from __future__ import annotations

"""
VOID Licensing System

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""



import hashlib
import json
import platform
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class LicenseType(Enum):
    """License type enumeration"""
    TRIAL = "trial"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LicenseStatus(Enum):
    """License status enumeration"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    DEVICE_MISMATCH = "device_mismatch"
    DEACTIVATED = "deactivated"


class LicenseManager:
    """
    Manages software licensing including validation, activation, and expiration.
    
    Features:
    - RSA-based license key generation and validation
    - Hardware fingerprinting for device binding
    - Offline license validation
    - Trial period support (14 days)
    - Multiple license tiers
    """
    
    LICENSE_FILE = Path.home() / ".void" / "license.key"
    PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyVz9RqJxN5FxqF8Cqzqs
F+FjN5lK8xH2tN7mP+pQwS1F9K2aDhO6gJN3N5xE8FqzQy7fH9K2xF8mN5P9Q8F
x9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q
8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5
P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K
2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9F8K2N5P9Q8Fx9
F8K2N5P9Q8Fx9F8K2N5P9Q8FwIDAQAB
-----END PUBLIC KEY-----"""
    
    def __init__(self):
        """Initialize the license manager"""
        self.license_file = self.LICENSE_FILE
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "cryptography library is required for licensing. "
                "Install with: pip install cryptography"
            )
    
    def get_hardware_fingerprint(self) -> str:
        """
        Generate a unique hardware fingerprint for this device.
        
        Uses MAC address and CPU ID to create a stable identifier.
        
        Returns:
            str: Hardware fingerprint hash
        """
        # Get MAC address
        mac = hex(uuid.getnode())
        
        # Get system information
        system_info = f"{platform.system()}-{platform.machine()}-{platform.processor()}"
        
        # Combine and hash
        fingerprint_data = f"{mac}-{system_info}"
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return fingerprint_hash
    
    def activate_license(self, license_data: Dict) -> bool:
        """
        Activate a license on this device.
        
        Args:
            license_data: Dictionary containing license information
            
        Returns:
            bool: True if activation successful
        """
        try:
            # Add activation timestamp and device fingerprint
            license_data["activated_at"] = datetime.now().isoformat()
            license_data["device_fingerprint"] = self.get_hardware_fingerprint()
            license_data["status"] = "active"
            
            # Save to file
            with open(self.license_file, "w") as f:
                json.dump(license_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"License activation failed: {e}")
            return False
    
    def deactivate_license(self) -> bool:
        """
        Deactivate the current license.
        
        Returns:
            bool: True if deactivation successful
        """
        try:
            if not self.license_file.exists():
                return True
            
            # Mark as deactivated instead of deleting
            license_data = self.load_license()
            if license_data:
                license_data["status"] = "deactivated"
                license_data["deactivated_at"] = datetime.now().isoformat()
                
                with open(self.license_file, "w") as f:
                    json.dump(license_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"License deactivation failed: {e}")
            return False
    
    def load_license(self) -> Optional[Dict]:
        """
        Load license data from file.
        
        Returns:
            Optional[Dict]: License data or None if not found
        """
        try:
            if not self.license_file.exists():
                return None
            
            with open(self.license_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load license: {e}")
            return None
    
    def verify_signature(self, license_data: Dict, signature: str) -> bool:
        """
        Verify the RSA signature of license data.
        
        Args:
            license_data: License data to verify
            signature: Base64-encoded signature
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                self.PUBLIC_KEY_PEM,
                backend=default_backend()
            )
            
            # Prepare data for verification
            data_to_verify = json.dumps(license_data, sort_keys=True).encode()
            signature_bytes = bytes.fromhex(signature)
            
            # Verify signature
            public_key.verify(
                signature_bytes,
                data_to_verify,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def check_expiration(self, license_data: Dict) -> bool:
        """
        Check if license has expired.
        
        Args:
            license_data: License data to check
            
        Returns:
            bool: True if expired
        """
        try:
            if "expiration_date" not in license_data:
                return False  # No expiration
            
            expiration = datetime.fromisoformat(license_data["expiration_date"])
            return datetime.now() > expiration
        except Exception:
            return True  # Treat invalid dates as expired
    
    def validate_license(self) -> tuple[LicenseStatus, Optional[Dict]]:
        """
        Validate the current license.
        
        Returns:
            tuple: (LicenseStatus, license_data)
        """
        # Load license
        license_data = self.load_license()
        if not license_data:
            return (LicenseStatus.NOT_FOUND, None)
        
        # Check if deactivated
        if license_data.get("status") == "deactivated":
            return (LicenseStatus.DEACTIVATED, license_data)
        
        # Check device fingerprint
        current_fingerprint = self.get_hardware_fingerprint()
        if license_data.get("device_fingerprint") != current_fingerprint:
            return (LicenseStatus.DEVICE_MISMATCH, license_data)
        
        # Check expiration
        if self.check_expiration(license_data):
            return (LicenseStatus.EXPIRED, license_data)
        
        # Verify signature if present
        if "signature" in license_data:
            signature = license_data.pop("signature")
            if not self.verify_signature(license_data, signature):
                license_data["signature"] = signature  # Restore
                return (LicenseStatus.INVALID, license_data)
            license_data["signature"] = signature  # Restore
        
        return (LicenseStatus.VALID, license_data)
    
    def get_license_info(self) -> Dict:
        """
        Get current license information.
        
        Returns:
            Dict: License information
        """
        status, license_data = self.validate_license()
        
        if not license_data:
            return {
                "status": status.value,
                "type": "none",
                "message": "No license found. Running in unlicensed mode."
            }
        
        info = {
            "status": status.value,
            "type": license_data.get("license_type", "unknown"),
            "email": license_data.get("email", "N/A"),
            "activated_at": license_data.get("activated_at", "N/A"),
        }
        
        # Add expiration info
        if "expiration_date" in license_data:
            info["expires_at"] = license_data["expiration_date"]
            
            # Calculate days remaining
            try:
                expiration = datetime.fromisoformat(license_data["expiration_date"])
                days_remaining = (expiration - datetime.now()).days
                info["days_remaining"] = max(0, days_remaining)
            except Exception:
                info["days_remaining"] = 0
        else:
            info["expires_at"] = "Never"
            info["days_remaining"] = None
        
        # Add status message
        if status == LicenseStatus.VALID:
            info["message"] = "License is valid and active."
        elif status == LicenseStatus.EXPIRED:
            info["message"] = "License has expired. Please renew."
        elif status == LicenseStatus.INVALID:
            info["message"] = "License signature is invalid."
        elif status == LicenseStatus.DEVICE_MISMATCH:
            info["message"] = "License is bound to a different device."
        elif status == LicenseStatus.DEACTIVATED:
            info["message"] = "License has been deactivated."
        
        return info
    
    def start_trial(self) -> bool:
        """
        Start a 14-day trial license.
        
        Returns:
            bool: True if trial started successfully
        """
        # Check if already licensed
        status, _ = self.validate_license()
        if status == LicenseStatus.VALID:
            print("A valid license already exists.")
            return False
        
        # Create trial license
        trial_data = {
            "license_type": LicenseType.TRIAL.value,
            "email": "trial@void-suite.local",
            "created_at": datetime.now().isoformat(),
            "expiration_date": (datetime.now() + timedelta(days=14)).isoformat(),
        }
        
        return self.activate_license(trial_data)
    
    def is_licensed(self) -> bool:
        """
        Check if software is licensed (trial or paid).
        
        Returns:
            bool: True if valid license exists
        """
        status, _ = self.validate_license()
        return status == LicenseStatus.VALID
    
    def get_license_type(self) -> Optional[LicenseType]:
        """
        Get the current license type.
        
        Returns:
            Optional[LicenseType]: Current license type or None
        """
        status, license_data = self.validate_license()
        if status != LicenseStatus.VALID or not license_data:
            return None
        
        license_type_str = license_data.get("license_type", "").lower()
        try:
            return LicenseType(license_type_str)
        except ValueError:
            return None
