# Licensing Guide

**Void Suite Licensing System**

**Copyright (c) 2024 Roach Labs. All rights reserved.**

---

## Table of Contents

1. [Overview](#overview)
2. [How Licensing Works](#how-licensing-works)
3. [License Types](#license-types)
4. [Activation](#activation)
5. [Deactivation](#deactivation)
6. [License Management](#license-management)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Overview

Void Suite uses a flexible licensing system that supports multiple tiers to meet different user needs. The licensing system is designed to:

- Work offline after initial activation
- Bind licenses to specific hardware
- Support trial periods for evaluation
- Enable easy transfers between devices
- Provide clear license status information

---

## How Licensing Works

### Architecture

The Void Suite licensing system consists of:

1. **License Key**: A digitally signed JSON file containing your license information
2. **Hardware Fingerprint**: A unique identifier generated from your device's hardware
3. **Local Validation**: License verification happens locally, no server required
4. **RSA Signing**: Cryptographic signatures prevent tampering

### Security Features

- **Hardware Binding**: License tied to your device's MAC address and CPU ID
- **RSA-2048 Encryption**: Industry-standard cryptographic signing
- **Offline Operation**: No "phone home" or internet requirements after activation
- **Tamper Protection**: Any modification to license file invalidates it

---

## License Types

### Trial License

**Purpose**: Evaluate Void Suite before purchasing

- **Duration**: 14 days from activation
- **Features**: Full access to all features
- **Devices**: 1 device
- **Support**: Community support
- **Commercial Use**: ❌ Not permitted
- **Price**: FREE

**How to Start Trial:**
```bash
void license trial
```

Or during first run, the software will offer to start a trial.

### Personal License

**Purpose**: Individual users for personal projects

- **Duration**: Perpetual (lifetime)
- **Features**: Full access
- **Devices**: 1 device per license
- **Support**: Email support (48-hour response)
- **Commercial Use**: ❌ Personal projects only
- **Updates**: Free minor updates, paid major upgrades
- **Price**: Contact sales

**Best for:**
- Hobbyists and enthusiasts
- Personal device management
- Learning and experimentation

### Professional License

**Purpose**: Individual professionals and small businesses

- **Duration**: Perpetual with 1-year update period
- **Features**: Full access + priority updates
- **Devices**: Up to 3 devices per license
- **Support**: Priority email support (24-hour response)
- **Commercial Use**: ✅ Permitted
- **Updates**: Free updates for 1 year
- **Renewal**: Optional (30-40% of original price)
- **Price**: Contact sales

**Best for:**
- Repair technicians
- Independent consultants
- Small repair shops
- Freelancers

### Enterprise License

**Purpose**: Organizations and large-scale deployments

- **Duration**: Annual subscription or perpetual
- **Features**: Full access + custom integrations
- **Devices**: Unlimited within organization
- **Support**: Dedicated support with SLA (4-hour response)
- **Commercial Use**: ✅ Unlimited
- **Updates**: Free updates during subscription
- **Custom Terms**: Available
- **Price**: Custom pricing

**Best for:**
- Large repair operations
- Corporate IT departments
- Refurbishment companies
- Device resellers

---

## Activation

### Prerequisites

- Valid license key file (`.key` file from your purchase)
- Internet connection (for initial activation only)
- Device to bind license to

### Activation Methods

#### Method 1: GUI Activation

1. Launch Void Suite GUI
2. Click **Help** → **License Manager**
3. Click **Activate License**
4. Browse to your `.key` file or paste license content
5. Click **Activate**
6. Restart application

#### Method 2: CLI Activation

```bash
# Activate from file
void license activate --file /path/to/license.key

# Activate from clipboard
void license activate --clipboard

# Check status
void license status
```

#### Method 3: Manual Activation

1. Copy license key file to `~/.void/license.key`
2. Restart Void Suite
3. License auto-detected and activated

### What Happens During Activation

1. **Validation**: License signature verified using public key
2. **Fingerprinting**: Device hardware fingerprint generated
3. **Binding**: License bound to this specific device
4. **Storage**: License saved to `~/.void/license.key`
5. **Confirmation**: Success message displayed

### Activation Limits

- **Personal**: 1 device at a time (can transfer)
- **Professional**: Up to 3 devices simultaneously
- **Enterprise**: Unlimited devices in organization

---

## Deactivation

### When to Deactivate

Deactivate before:
- Transferring license to new device
- Selling or disposing of device
- Reinstalling operating system
- Major hardware upgrades

### Deactivation Methods

#### GUI Deactivation

1. Open **Help** → **License Manager**
2. Click **Deactivate License**
3. Confirm deactivation
4. License slot freed for reactivation

#### CLI Deactivation

```bash
void license deactivate
```

### Transfer to New Device

1. **Deactivate** on old device
2. Copy license key file to new device
3. **Activate** on new device
4. Done!

**Personal/Professional**: Can transfer once every 12 months (free)  
**Enterprise**: Contact support for transfers

---

## License Management

### Checking License Status

#### GUI Method

1. Open **Help** → **About**
2. View license information panel
3. See type, expiration, devices remaining

#### CLI Method

```bash
# Full license information
void license status

# Quick check
void license info
```

**Sample Output:**
```
License Status: VALID
License Type: Professional
Email: user@example.com
Activated: 2024-01-15
Expires: 2025-01-15 (150 days remaining)
Devices: 2/3 used
```

### Renewing License

#### Professional License Renewal

Professional licenses include 1 year of updates. After that:

1. **Continue Using**: You can keep using your current version forever
2. **Renew for Updates**: Pay renewal fee (~30-40% of original) for another year of updates

**To Renew:**
- Email: sales@roach-labs.com
- Provide: Current license key or order number
- Receive: Extended license key

#### Enterprise License Renewal

Enterprise subscriptions must be renewed to continue use:

- Reminder sent 60 days before expiration
- Auto-renewal available
- Contact account manager or sales

### Upgrading License Tier

#### From Trial to Paid

1. Purchase Personal or Professional license
2. Deactivate trial
3. Activate new license

#### From Personal to Professional

1. Contact sales: sales@roach-labs.com
2. Pay upgrade fee (prorated)
3. Receive upgraded license
4. Activate (replaces old license)

#### From Any to Enterprise

1. Contact sales for custom quote
2. Receive enterprise license
3. Activate on unlimited devices

---

## Troubleshooting

### License Not Found

**Symptom**: "No license found" error

**Solutions:**
1. Check if `~/.void/license.key` exists
2. Verify file permissions (should be readable)
3. Try activating again
4. Check if file is valid JSON

### License Invalid

**Symptom**: "License signature invalid" error

**Causes:**
- File was modified or corrupted
- Wrong license file
- Damaged download

**Solutions:**
1. Re-download license from email
2. Verify file integrity
3. Contact support if issue persists

### License Expired

**Symptom**: "License has expired" error

**For Trial:**
- 14 days have passed
- Purchase a paid license to continue

**For Professional:**
- Update period ended
- Renew to get updates
- Current version still works

**For Enterprise:**
- Subscription lapsed
- Must renew to continue use

### Device Mismatch

**Symptom**: "License bound to different device" error

**Causes:**
- Used license from another device
- Major hardware change
- MAC address changed

**Solutions:**
1. Deactivate on original device first
2. If original device unavailable, contact support
3. One transfer allowed per year (free)

### Too Many Devices

**Symptom**: "Device limit exceeded" error

**Solution:**
1. Deactivate on devices you're not using
2. Purchase additional licenses
3. Upgrade to higher tier (Professional or Enterprise)

### Hardware Change Issues

If you upgraded RAM, HDD, or GPU:
- License should still work (uses MAC + CPU ID)

If you replaced motherboard or CPU:
- Counts as new device
- Deactivate before hardware change
- Reactivate after

If impossible to deactivate first:
- Contact support: support@roach-labs.com
- Provide proof of ownership
- One-time transfer allowed

---

## FAQ

### General Questions

**Q: Do I need internet connection to use Void Suite?**

A: Internet required only for initial license activation. After activation, everything works offline.

**Q: Can I use one license on multiple devices?**

A: Depends on tier:
- Personal: 1 device (can transfer)
- Professional: 3 devices simultaneously
- Enterprise: Unlimited

**Q: What happens if my license expires?**

A:
- Trial: Limited functionality, prompt to purchase
- Professional: Current version keeps working, no updates
- Enterprise: Software stops working, must renew

**Q: Can I use Void Suite without a license?**

A: Yes, but with limited functionality. Most advanced features require a license.

### Purchase Questions

**Q: How do I purchase a license?**

A: Contact sales@roach-labs.com with your requirements. We'll provide pricing and purchase link.

**Q: What payment methods are accepted?**

A: Credit card, PayPal, bank transfer (Enterprise), purchase orders (Enterprise with credit approval).

**Q: Do you offer refunds?**

A: Yes, 14-day money-back guarantee for Personal and Professional licenses. See TERMS_OF_SALE.md.

**Q: Are there educational discounts?**

A: Yes, contact sales with proof of student/educator status for discounts.

### Technical Questions

**Q: Where is the license file stored?**

A: `~/.void/license.key` (Linux/Mac) or `C:\Users\<username>\.void\license.key` (Windows)

**Q: Can I backup my license file?**

A: Yes! Keep a backup in secure location. Also available in customer portal.

**Q: How is hardware fingerprint generated?**

A: SHA-256 hash of MAC address + CPU ID + system info. Stable across OS reinstalls.

**Q: Can I share my license with colleagues?**

A: No, licenses are personal/organizational. Sharing violates terms and may result in deactivation.

**Q: What if I lose my license file?**

A: Re-download from purchase confirmation email or customer portal.

### Support Questions

**Q: How do I get support?**

A: Depends on license tier:
- Trial: GitHub issues
- Personal: support@roach-labs.com (48-hour response)
- Professional: support@roach-labs.com (24-hour response)
- Enterprise: Dedicated support portal

**Q: What if I have a license issue?**

A: Email licensing@roach-labs.com with:
- License key or order number
- Description of issue
- Screenshots if applicable

---

## Contact Information

**Sales & Licensing:**
Email: sales@roach-labs.com

**Technical Support:**
Email: support@roach-labs.com

**License Issues:**
Email: licensing@roach-labs.com

**Website:**
https://github.com/xroachx-ghost/void

---

**Last Updated**: December 30, 2024  
**Version**: 1.0

**Copyright (c) 2024 Roach Labs. All rights reserved.**
