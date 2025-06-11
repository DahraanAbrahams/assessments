# API Documentation

## Base URL and Versioning

```
Base URL: http://localhost:8000/api/v1
Version: 1.0.0
```

## Authentication

Authentication is handled per tenant using the `X-Tenant-ID` header combined with tenant-specific auth:

### CoffeeChain
```
X-Tenant-ID: coffeechain
X-CC-API-Key: {member_api_key}
X-CC-Member-ID: {member_id}
```

### TelcoCorp
```
X-Tenant-ID: telcocorp
Authorization: Bearer {oauth_token}
X-TC-Customer-ID: {customer_id}
```

### FintechApp
```
X-Tenant-ID: fintechapp
Authorization: Bearer {jwt_token}
X-FA-User-ID: {user_id}
```

## Rate Limiting

Rate limits are applied per tenant:
- CoffeeChain: 100 requests/minute
- TelcoCorp: 50 requests/minute
- FintechApp: 200 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699564800
```

## Endpoints

### 1. Search Flights

Search for available flights between origins and destinations.

**Endpoint:** `POST /api/v1/flights/search`

**Request Body:**
```json
{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2024-03-15",
    "return_date": "2024-03-22",
    "passengers": {
        "adults": 1,
        "children": 0,
        "infants": 0
    },
    "cabin_class": "economy",
    "currency": "USD"
}
```

**Response:**
```json
{
    "data": {
        "search_id": "src_1234567890",
        "flights": [
            {
                "id": "flt_abc123",
                "airline": "United Airlines",
                "flight_number": "UA123",
                "departure": {
                    "airport": "JFK",
                    "time": "2024-03-15T08:00:00Z",
                    "terminal": "4"
                },
                "arrival": {
                    "airport": "LAX",
                    "time": "2024-03-15T11:30:00Z",
                    "terminal": "7"
                },
                "duration": "PT5H30M",
                "price": {
                    "amount": 35000,
                    "currency": "USD",
                    "loyalty_amount": 3500000,
                    "loyalty_currency": "stars"
                },
                "available_seats": 45,
                "cabin_class": "economy"
            }
        ],
        "metadata": {
            "total_results": 15,
            "search_time_ms": 1250
        }
    }
}
```

**Error Response (TelcoCorp - Economy Only):**
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/invalid-cabin-class",
        "title": "Invalid Cabin Class",
        "status": 400,
        "detail": "This tenant does not support the requested cabin class",
        "instance": "/api/v1/flights/search"
    }
}
```

### 2. Create Booking

Create a new flight booking using loyalty currency.

**Endpoint:** `POST /api/v1/bookings`

**Request Body:**
```json
{
    "flight_id": "flt_abc123",
    "passengers": [
        {
            "type": "adult",
            "title": "Mr",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1985-03-15",
            "email": "john.doe@email.com",
            "phone": "+1-555-123-4567"
        }
    ],
    "payment": {
        "method": "loyalty_points",
        "amount": 3500000,
        "currency": "stars"
    },
    "contact": {
        "email": "john.doe@email.com",
        "phone": "+1-555-123-4567"
    }
}
```

**Response (Success):**
```json
{
    "data": {
        "booking_id": "bkg_xyz789",
        "status": "confirmed",
        "tenant_id": "coffeechain",
        "member_id": "CC1234567",
        "flight": {
            "id": "flt_abc123",
            "flight_number": "UA123",
            "departure": "2024-03-15T08:00:00Z",
            "arrival": "2024-03-15T11:30:00Z"
        },
        "passengers": [
            {
                "name": "John Doe",
                "ticket_number": "0162345678901"
            }
        ],
        "payment": {
            "loyalty_amount": 3500000,
            "loyalty_currency": "stars",
            "usd_equivalent": 35000
        },
        "created_at": "2024-02-01T10:30:00Z",
        "expires_at": "2024-02-01T11:00:00Z"
    }
}
```

**Response (Pending Approval - CoffeeChain >50k stars):**
```json
{
    "data": {
        "booking_id": "bkg_pending123",
        "status": "pending_approval",
        "tenant_id": "coffeechain",
        "approval_required": true,
        "approval_reason": "Booking exceeds 50,000 stars limit",
        "estimated_approval_time": "PT24H"
    }
}
```

### 3. Get Booking

Retrieve details of a specific booking.

**Endpoint:** `GET /api/v1/bookings/{booking_id}`

**Response:**
```json
{
    "data": {
        "booking_id": "bkg_xyz789",
        "status": "confirmed",
        "tenant_id": "coffeechain",
        "member_id": "CC1234567",
        "flight": {
            "id": "flt_abc123",
            "airline": "United Airlines",
            "flight_number": "UA123",
            "departure": {
                "airport": "JFK",
                "time": "2024-03-15T08:00:00Z",
                "terminal": "4"
            },
            "arrival": {
                "airport": "LAX",
                "time": "2024-03-15T11:30:00Z",
                "terminal": "7"
            }
        },
        "passengers": [
            {
                "name": "John Doe",
                "ticket_number": "0162345678901",
                "seat": "23A"
            }
        ],
        "payment": {
            "loyalty_amount": 3500000,
            "loyalty_currency": "stars",
            "usd_equivalent": 35000,
            "cashback": null
        },
        "created_at": "2024-02-01T10:30:00Z",
        "updated_at": "2024-02-01T10:35:00Z"
    }
}
```

### 4. List Bookings

List all bookings for the authenticated member/user.

**Endpoint:** `GET /api/v1/bookings`

**Query Parameters:**
- `status` (optional): Filter by status (confirmed, pending, cancelled)
- `from_date` (optional): Filter bookings created after this date
- `to_date` (optional): Filter bookings created before this date
- `limit` (optional): Number of results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
    "data": {
        "bookings": [
            {
                "booking_id": "bkg_xyz789",
                "status": "confirmed",
                "flight_number": "UA123",
                "departure_date": "2024-03-15",
                "route": "JFK → LAX",
                "loyalty_amount": 3500000,
                "created_at": "2024-02-01T10:30:00Z"
            },
            {
                "booking_id": "bkg_abc456",
                "status": "cancelled",
                "flight_number": "DL456",
                "departure_date": "2024-02-20",
                "route": "LAX → JFK",
                "loyalty_amount": 4200000,
                "created_at": "2024-01-15T14:20:00Z"
            }
        ],
        "pagination": {
            "total": 25,
            "limit": 20,
            "offset": 0,
            "has_more": true
        }
    }
}
```

### 5. Cancel Booking

Cancel an existing booking and refund loyalty points.

**Endpoint:** `POST /api/v1/bookings/{booking_id}/cancel`

**Request Body:**
```json
{
    "reason": "Change of plans",
    "refund_requested": true
}
```

**Response:**
```json
{
    "data": {
        "booking_id": "bkg_xyz789",
        "status": "cancelled",
        "cancelled_at": "2024-02-02T09:15:00Z",
        "refund": {
            "status": "processed",
            "loyalty_amount": 3500000,
            "loyalty_currency": "stars",
            "fee": 0,
            "net_refund": 3500000,
            "processed_at": "2024-02-02T09:15:30Z"
        }
    }
}
```

### 6. Health Check

Check the health status of the API and its dependencies.

**Endpoint:** `GET /api/v1/health`

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-02-01T10:00:00Z",
    "version": "1.0.0",
    "services": {
        "database": "healthy",
        "duffel_api": "healthy",
        "coffeechain_api": "healthy",
        "telcocorp_api": "healthy",
        "fintechapp_api": "healthy"
    }
}
```

## Error Responses

All errors follow RFC 7807 (Problem Details for HTTP APIs):

### 400 Bad Request
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/validation-error",
        "title": "Validation Error",
        "status": 400,
        "detail": "departure_date must be in the future",
        "instance": "/api/v1/flights/search",
        "errors": [
            {
                "field": "departure_date",
                "message": "Must be a future date"
            }
        ]
    }
}
```

### 401 Unauthorized
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/unauthorized",
        "title": "Unauthorized",
        "status": 401,
        "detail": "Invalid or expired authentication credentials",
        "instance": "/api/v1/bookings"
    }
}
```

### 403 Forbidden
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/insufficient-balance",
        "title": "Insufficient Balance",
        "status": 403,
        "detail": "Member has an insufficient balance. Required: 3500000, Available: 2000000",
        "instance": "/api/v1/bookings",
        "balance": {
            "required": 3500000,
            "available": 2000000,
            "currency": "stars"
        }
    }
}
```

### 404 Not Found
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/not-found",
        "title": "Booking Not Found",
        "status": 404,
        "detail": "Booking with ID 'bkg_xyz789' not found",
        "instance": "/api/v1/bookings/bkg_xyz789"
    }
}
```

### 429 Too Many Requests
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/rate-limit",
        "title": "Rate Limit Exceeded",
        "status": 429,
        "detail": "Rate limit exceeded. Please try again later.",
        "instance": "/api/v1/flights/search",
        "retry_after": 45
    }
}
```

### 500 Internal Server Error
```json
{
    "error": {
        "type": "https://api.loyalty-middleware.com/errors/internal-error",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred while processing your request",
        "instance": "/api/v1/bookings",
        "trace_id": "abc-123-def-456"
    }
}
```

## Webhooks (Optional)

If implemented, your middleware should send webhooks for booking status changes:

### Booking Confirmed
```json
{
    "event": "booking.confirmed",
    "timestamp": "2024-02-01T10:35:00Z",
    "data": {
        "booking_id": "bkg_xyz789",
        "tenant_id": "coffeechain",
        "member_id": "CC1234567",
        "status": "confirmed"
    }
}
```

### Booking Cancelled
```json
{
    "event": "booking.cancelled",
    "timestamp": "2024-02-02T09:15:00Z",
    "data": {
        "booking_id": "bkg_xyz789",
        "tenant_id": "coffeechain",
        "member_id": "CC1234567",
        "status": "cancelled",
        "refund_amount": 3500000
    }
}
```

## Testing with Mock Services

Use the `X-Mock-Error` header to simulate errors:

```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "X-Tenant-ID: coffeechain" \
  -H "X-CC-API-Key: test_cc_api_key_12345" \
  -H "X-CC-Member-ID: CC1234567" \
  -H "X-Mock-Error: insufficient-balance" \
  -d '{...}'
```

Supported mock errors:
- `insufficient-balance`: Simulate insufficient loyalty points
- `auth-failed`: Simulate authentication failure
- `api-timeout`: Simulate timeout from tenant API
- `approval-required`: Force approval requirement (CoffeeChain)
- `invalid-member`: Simulate invalid member/customer/user ID