#!/usr/bin/env python3
"""
VOID License Generator

Administrative tool for generating customer license keys.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.

SECURITY WARNING: Keep the private key secure and never commit it to version control.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class LicenseGenerator:
    """
    Generate and sign license keys for Void Suite.

    This tool should only be used by authorized administrators.
    The private key must be kept secure.
    """

    # Path to private key (should be stored securely, not in repo)
    PRIVATE_KEY_PATH = Path.home() / ".void" / "private_key.pem"

    def __init__(self):
        """Initialize the license generator"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "cryptography library is required. " "Install with: pip install cryptography"
            )

        self.private_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing private key or generate new key pair"""
        if self.PRIVATE_KEY_PATH.exists():
            # Load existing private key
            with open(self.PRIVATE_KEY_PATH, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            print(f"Loaded existing private key from {self.PRIVATE_KEY_PATH}")
        else:
            # Generate new key pair
            print("Generating new RSA key pair...")
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )

            # Save private key
            self.PRIVATE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            with open(self.PRIVATE_KEY_PATH, "wb") as f:
                f.write(pem)
            self.PRIVATE_KEY_PATH.chmod(0o600)  # Restrict permissions

            # Save public key for reference
            public_key = self.private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            public_key_path = self.PRIVATE_KEY_PATH.parent / "public_key.pem"
            with open(public_key_path, "wb") as f:
                f.write(public_pem)

            print("Generated new keys:")
            print(f"  Private key: {self.PRIVATE_KEY_PATH}")
            print(f"  Public key: {public_key_path}")
            print("\nWARNING: Keep the private key secure!")
            print("Add the public key to void/licensing.py PUBLIC_KEY_PEM constant.")

    def sign_license(self, license_data: dict) -> str:
        """
        Sign license data with private key.

        Args:
            license_data: License data to sign

        Returns:
            str: Hex-encoded signature
        """
        # Serialize license data
        data_to_sign = json.dumps(license_data, sort_keys=True).encode()

        # Sign with private key
        signature = self.private_key.sign(
            data_to_sign,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )

        return signature.hex()

    def generate_license(
        self,
        email: str,
        license_type: str,
        expiration_days: int = None,
        device_limit: int = 1,
        customer_name: str = None,
    ) -> dict:
        """
        Generate a new license.

        Args:
            email: Customer email address
            license_type: Type of license (trial, personal, professional, enterprise)
            expiration_days: Number of days until expiration (None for perpetual)
            device_limit: Maximum number of devices
            customer_name: Optional customer name

        Returns:
            dict: License data with signature
        """
        # Create license data
        license_data = {
            "email": email,
            "license_type": license_type.lower(),
            "created_at": datetime.now().isoformat(),
            "device_limit": device_limit,
        }

        if customer_name:
            license_data["customer_name"] = customer_name

        if expiration_days:
            expiration_date = datetime.now() + timedelta(days=expiration_days)
            license_data["expiration_date"] = expiration_date.isoformat()

        # Sign the license
        signature = self.sign_license(license_data)
        license_data["signature"] = signature

        return license_data

    def save_license(self, license_data: dict, output_file: Path):
        """
        Save license to file.

        Args:
            license_data: License data to save
            output_file: Output file path
        """
        with open(output_file, "w") as f:
            json.dump(license_data, f, indent=2)
        print(f"\nLicense saved to: {output_file}")

    def print_license(self, license_data: dict):
        """Print license information"""
        print("\n" + "=" * 60)
        print("VOID SUITE LICENSE")
        print("=" * 60)
        print(f"Email: {license_data.get('email')}")
        print(f"Type: {license_data.get('license_type').upper()}")
        print(f"Created: {license_data.get('created_at')}")

        if "customer_name" in license_data:
            print(f"Customer: {license_data.get('customer_name')}")

        if "expiration_date" in license_data:
            print(f"Expires: {license_data.get('expiration_date')}")
        else:
            print("Expires: Never (Perpetual)")

        print(f"Device Limit: {license_data.get('device_limit')}")
        print(f"Signature: {license_data.get('signature')[:32]}...")
        print("=" * 60)


def main():
    """Main entry point for license generator"""
    parser = argparse.ArgumentParser(
        description="Generate Void Suite license keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a 14-day trial license
  python -m void.license_generator --email user@example.com --type trial --days 14

  # Generate a perpetual personal license
  python -m void.license_generator --email user@example.com --type personal

  # Generate a professional license with 1-year expiration
  python -m void.license_generator --email user@example.com --type professional --days 365

  # Generate an enterprise license with custom name
  python -m void.license_generator --email admin@company.com --type enterprise \\
      --name "Acme Corporation" --devices 100
        """,
    )

    parser.add_argument("--email", required=True, help="Customer email address")

    parser.add_argument(
        "--type",
        required=True,
        choices=["trial", "personal", "professional", "enterprise"],
        help="License type",
    )

    parser.add_argument(
        "--days", type=int, default=None, help="Days until expiration (omit for perpetual license)"
    )

    parser.add_argument(
        "--devices", type=int, default=1, help="Maximum number of devices (default: 1)"
    )

    parser.add_argument("--name", help="Customer name or organization")

    parser.add_argument(
        "--output", type=Path, help="Output file path (default: license_<email>.key)"
    )

    args = parser.parse_args()

    try:
        # Create generator
        generator = LicenseGenerator()

        # Generate license
        license_data = generator.generate_license(
            email=args.email,
            license_type=args.type,
            expiration_days=args.days,
            device_limit=args.devices,
            customer_name=args.name,
        )

        # Print license info
        generator.print_license(license_data)

        # Save to file
        if args.output:
            output_file = args.output
        else:
            # Default output filename
            safe_email = args.email.replace("@", "_").replace(".", "_")
            output_file = Path(f"license_{safe_email}.key")

        generator.save_license(license_data, output_file)

        print("\nLicense generated successfully!")
        print(f"Send this file to the customer: {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
