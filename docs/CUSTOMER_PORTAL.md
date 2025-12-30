# Customer Portal Implementation Guide

**Building a License Management Portal for Void Suite**

**Copyright (c) 2024 Roach Labs. All rights reserved.**

---

## Overview

This guide provides specifications for implementing a customer self-service portal for Void Suite license management. The portal allows customers to:

- Purchase and manage licenses
- Activate/deactivate devices
- Download license keys
- View usage statistics
- Access support resources
- Manage billing and subscriptions

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Payment Integration](#payment-integration)
5. [Frontend Components](#frontend-components)
6. [Security Considerations](#security-considerations)
7. [Example Implementation](#example-implementation)

---

## Architecture Overview

### Technology Stack (Recommended)

**Backend:**
- **Framework**: FastAPI (Python) or Express (Node.js)
- **Database**: PostgreSQL or MySQL
- **Cache**: Redis (optional, for sessions)
- **Queue**: Celery/RQ for async tasks (email, notifications)

**Frontend:**
- **Framework**: React, Vue, or Next.js
- **UI Library**: Tailwind CSS, Material-UI, or Chakra UI
- **State Management**: Redux or Zustand

**Infrastructure:**
- **Hosting**: AWS, Google Cloud, or Azure
- **CDN**: CloudFlare or AWS CloudFront
- **Email**: SendGrid or AWS SES
- **Payments**: Stripe or PayPal

### System Components

```
┌─────────────────┐
│   Web Frontend  │
│   (React/Vue)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│   API Server    │◄────►│   Database   │
│   (FastAPI)     │      │ (PostgreSQL) │
└────────┬────────┘      └──────────────┘
         │
         ├────► ┌──────────────┐
         │      │    Stripe    │
         │      │   (Payment)  │
         │      └──────────────┘
         │
         ├────► ┌──────────────┐
         │      │   SendGrid   │
         │      │    (Email)   │
         │      └──────────────┘
         │
         └────► ┌──────────────┐
                │  S3/Storage  │
                │  (Downloads) │
                └──────────────┘
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    country VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
```

### Licenses Table

```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    license_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    license_type VARCHAR(50) NOT NULL, -- trial, personal, professional, enterprise
    status VARCHAR(50) DEFAULT 'active', -- active, suspended, expired, cancelled
    
    -- Limits
    device_limit INTEGER DEFAULT 1,
    devices_activated INTEGER DEFAULT 0,
    
    -- Dates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    expires_at TIMESTAMP,
    renewed_at TIMESTAMP,
    
    -- Payment
    order_id VARCHAR(255),
    payment_processor VARCHAR(50), -- stripe, paypal, manual
    payment_id VARCHAR(255),
    
    -- Additional data
    metadata JSONB,
    
    CONSTRAINT valid_device_count CHECK (devices_activated <= device_limit)
);

CREATE INDEX idx_licenses_user ON licenses(user_id);
CREATE INDEX idx_licenses_key ON licenses(license_key);
CREATE INDEX idx_licenses_status ON licenses(status);
```

### Device Activations Table

```sql
CREATE TABLE device_activations (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255) NOT NULL,
    device_name VARCHAR(255),
    
    -- System info
    os_type VARCHAR(50),
    os_version VARCHAR(50),
    hostname VARCHAR(255),
    
    -- Activation tracking
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata JSONB,
    
    CONSTRAINT unique_active_device UNIQUE (license_id, device_fingerprint)
);

CREATE INDEX idx_activations_license ON device_activations(license_id);
CREATE INDEX idx_activations_fingerprint ON device_activations(device_fingerprint);
```

### Usage Tracking Table

```sql
CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,
    device_activation_id INTEGER REFERENCES device_activations(id),
    
    event_type VARCHAR(100) NOT NULL, -- startup, frp_bypass, edl_operation, etc.
    event_data JSONB,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Optional: telemetry data if user opted in
    telemetry_data JSONB
);

CREATE INDEX idx_usage_license ON usage_logs(license_id);
CREATE INDEX idx_usage_timestamp ON usage_logs(timestamp);
CREATE INDEX idx_usage_event_type ON usage_logs(event_type);
```

### Orders Table

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Payment
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_processor VARCHAR(50),
    payment_id VARCHAR(255),
    
    -- Product
    product_type VARCHAR(50) NOT NULL, -- personal, professional, enterprise
    license_id INTEGER REFERENCES licenses(id),
    
    -- Dates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    refunded_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_number ON orders(order_number);
```

### Support Tickets Table (Optional)

```sql
CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    license_id INTEGER REFERENCES licenses(id),
    
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, closed
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    assigned_to INTEGER, -- staff user ID
    
    metadata JSONB
);

CREATE INDEX idx_tickets_user ON support_tickets(user_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
```

---

## API Endpoints

### Authentication Endpoints

```
POST   /api/v1/auth/register          - Register new user
POST   /api/v1/auth/login             - Login user
POST   /api/v1/auth/logout            - Logout user
POST   /api/v1/auth/refresh           - Refresh access token
POST   /api/v1/auth/verify-email      - Verify email address
POST   /api/v1/auth/reset-password    - Request password reset
POST   /api/v1/auth/change-password   - Change password
```

### User Endpoints

```
GET    /api/v1/user/profile           - Get user profile
PUT    /api/v1/user/profile           - Update user profile
GET    /api/v1/user/licenses          - Get user's licenses
GET    /api/v1/user/orders            - Get user's orders
```

### License Endpoints

```
GET    /api/v1/licenses               - List user's licenses
GET    /api/v1/licenses/:id           - Get license details
POST   /api/v1/licenses/:id/activate  - Activate license on device
POST   /api/v1/licenses/:id/deactivate - Deactivate device
GET    /api/v1/licenses/:id/devices   - List activated devices
DELETE /api/v1/licenses/:id/devices/:device_id - Remove device
GET    /api/v1/licenses/:id/download  - Download license key file
GET    /api/v1/licenses/:id/usage     - Get usage statistics
```

### Purchase Endpoints

```
GET    /api/v1/products               - List available products/tiers
POST   /api/v1/checkout               - Create checkout session (Stripe)
POST   /api/v1/orders                 - Create order
GET    /api/v1/orders/:id             - Get order details
POST   /api/v1/webhooks/stripe        - Stripe webhook handler
POST   /api/v1/refunds                - Request refund
```

### Support Endpoints

```
GET    /api/v1/support/tickets        - List user's tickets
POST   /api/v1/support/tickets        - Create support ticket
GET    /api/v1/support/tickets/:id    - Get ticket details
PUT    /api/v1/support/tickets/:id    - Update ticket
POST   /api/v1/support/tickets/:id/messages - Add message to ticket
```

---

## Payment Integration

### Stripe Integration Example

**1. Create Checkout Session:**

```python
import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
stripe.api_key = "sk_test_..."

class CheckoutRequest(BaseModel):
    product_type: str  # personal, professional, enterprise
    success_url: str
    cancel_url: str

@router.post("/checkout")
async def create_checkout(request: CheckoutRequest, user_id: int):
    """Create Stripe checkout session"""
    
    # Product pricing
    prices = {
        "personal": "price_1234567890",  # Stripe Price ID
        "professional": "price_0987654321",
        "enterprise": None  # Custom pricing
    }
    
    if request.product_type not in prices:
        raise HTTPException(400, "Invalid product type")
    
    # Create checkout session
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        client_reference_id=str(user_id),
        customer_email=user.email,
        line_items=[{
            "price": prices[request.product_type],
            "quantity": 1
        }],
        metadata={
            "user_id": user_id,
            "product_type": request.product_type
        }
    )
    
    return {"session_id": session.id, "url": session.url}
```

**2. Webhook Handler:**

```python
from void.license_generator import LicenseGenerator

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    
    # Handle successful payment
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Extract metadata
        user_id = session["metadata"]["user_id"]
        product_type = session["metadata"]["product_type"]
        
        # Generate license
        generator = LicenseGenerator()
        license_data = generator.generate_license(
            email=session["customer_email"],
            license_type=product_type,
            expiration_days=None if product_type != "trial" else 14
        )
        
        # Save to database
        license = await create_license(
            user_id=user_id,
            license_data=license_data,
            order_id=session["id"],
            payment_id=session["payment_intent"]
        )
        
        # Send email with license
        await send_license_email(user_id, license)
    
    return {"status": "success"}
```

---

## Frontend Components

### React Example - License Dashboard

```jsx
// components/LicenseDashboard.jsx
import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function LicenseDashboard() {
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadLicenses();
  }, []);
  
  const loadLicenses = async () => {
    try {
      const response = await api.get('/licenses');
      setLicenses(response.data);
    } catch (error) {
      console.error('Failed to load licenses:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const downloadLicense = async (licenseId) => {
    try {
      const response = await api.get(`/licenses/${licenseId}/download`, {
        responseType: 'blob'
      });
      
      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `license_${licenseId}.key`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download license:', error);
    }
  };
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="license-dashboard">
      <h1>My Licenses</h1>
      
      {licenses.map(license => (
        <div key={license.id} className="license-card">
          <h3>{license.license_type.toUpperCase()} License</h3>
          <p>Status: {license.status}</p>
          <p>Devices: {license.devices_activated}/{license.device_limit}</p>
          <p>Created: {new Date(license.created_at).toLocaleDateString()}</p>
          {license.expires_at && (
            <p>Expires: {new Date(license.expires_at).toLocaleDateString()}</p>
          )}
          
          <button onClick={() => downloadLicense(license.id)}>
            Download License Key
          </button>
          
          <button onClick={() => navigate(`/licenses/${license.id}/devices`)}>
            Manage Devices
          </button>
        </div>
      ))}
      
      <button onClick={() => navigate('/purchase')}>
        Purchase New License
      </button>
    </div>
  );
}
```

---

## Security Considerations

### API Security

1. **Authentication**: Use JWT tokens with short expiration (15 min access, 7 day refresh)
2. **Authorization**: Verify user owns resource before allowing access
3. **Rate Limiting**: Implement rate limits (e.g., 100 requests/minute per user)
4. **Input Validation**: Validate all inputs, sanitize data
5. **HTTPS Only**: Enforce HTTPS, use HSTS header
6. **CORS**: Configure CORS properly, whitelist domains

### Data Protection

1. **Password Hashing**: Use bcrypt or Argon2 (never store plain text)
2. **Encryption**: Encrypt sensitive data at rest
3. **License Keys**: Store encrypted, decrypt only when needed
4. **PII**: Minimize PII collection, comply with GDPR/CCPA
5. **Audit Logging**: Log all sensitive operations

### Payment Security

1. **PCI Compliance**: Never store credit card data (use Stripe/PayPal)
2. **Webhook Verification**: Always verify webhook signatures
3. **Idempotency**: Implement idempotent payment processing
4. **Fraud Detection**: Monitor for suspicious patterns

---

## Example Implementation

See the complete implementation example in:
- `examples/customer-portal/` (to be created)
- FastAPI backend: `examples/customer-portal/backend/`
- React frontend: `examples/customer-portal/frontend/`

---

## Deployment Checklist

- [ ] Set up PostgreSQL database
- [ ] Configure Stripe API keys
- [ ] Set up email service (SendGrid)
- [ ] Configure environment variables
- [ ] Set up SSL certificates
- [ ] Configure CORS and security headers
- [ ] Set up monitoring and logging
- [ ] Test payment flow end-to-end
- [ ] Test license generation and delivery
- [ ] Set up backup system
- [ ] Configure rate limiting
- [ ] Test email deliverability
- [ ] Set up error tracking (Sentry)

---

## Contact

For implementation assistance or questions:

**Email**: support@roach-labs.com  
**Enterprise**: enterprise@roach-labs.com

---

**Last Updated**: December 30, 2024  
**Version**: 1.0

**Copyright (c) 2024 Roach Labs. All rights reserved.**
