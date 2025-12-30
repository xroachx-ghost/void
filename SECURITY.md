# Security Policy

**Copyright (c) 2024 Roach Labs. All rights reserved.**

## 🔒 Reporting Security Vulnerabilities

The security of Void Suite is taken seriously. If you discover a security vulnerability, please follow responsible disclosure practices.

### Do NOT

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed
- Exploit the vulnerability beyond what is necessary to demonstrate it

### Do

- Report vulnerabilities privately and promptly
- Provide sufficient detail to reproduce and understand the issue
- Allow reasonable time for the issue to be resolved before disclosure

## 📧 How to Report

Send security vulnerability reports to the maintainers via:

1. **GitHub Private Vulnerability Reporting** (preferred)
   - Go to the [Security tab](https://github.com/xroachx-ghost/void/security)
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Direct Contact**
   - If private reporting is unavailable, contact the repository owner directly

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested fixes (optional)
- Your contact information for follow-up

## 🛡️ Security Considerations

### Intended Use

Void Suite is designed for **authorized device maintenance and recovery** only. Users must:

- Have explicit permission to access any connected device
- Comply with all applicable laws and regulations
- Use the tool only on devices they own or are authorized to service

### Sensitive Operations

The following features involve sensitive operations and include safety measures:

| Feature | Risk Level | Safeguards |
|---------|------------|------------|
| EDL Flash | High | Confirmation prompts, audit logging |
| Partition Dump | High | Confirmation prompts, audit logging |
| FRP Operations | Medium | Authorization checks, logging |
| System Tweaks | Medium | Reversibility notes, confirmations |
| Data Recovery | Low-Medium | Permission checks |

### Data Handling

- Void Suite creates local logs, backups, and reports
- Sensitive data remains on the local system
- Users are responsible for securing exported data
- The Gemini AI agent may send queries to external services

## 🔄 Supported Versions

| Version | Supported |
|---------|-----------|
| 6.0.x   | ✅ Yes    |
| < 6.0   | ❌ No     |

Only the latest major version receives security updates.

## 🙏 Acknowledgments

We appreciate security researchers who help keep Void Suite and its users safe. Responsible disclosures will be acknowledged (with permission) in release notes.

---

*Thank you for helping keep Void Suite secure.*