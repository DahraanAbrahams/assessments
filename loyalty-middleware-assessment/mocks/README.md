# Mock Services

This directory contains mock implementations of the three loyalty program APIs that your middleware needs to integrate with. These services simulate real enterprise APIs with different authentication methods and business rules.

## Services Overview

### 1. CoffeeChain (Port 8001)
- **Authentication:** API Key
- **Currency:** Stars (1 star = $0.01)
- **Special Rule:** Requires approval for bookings over 50,000 stars
- **Rate Limit:** 100 requests/minute

### 2. TelcoCorp (Port 8002)
- **Authentication:** OAuth 2.0
- **Currency:** Points (100 points = $1)
- **Special Rule:** Economy class only
- **Rate Limit:** 50 requests/minute

### 3. FintechApp (Port 8003)
- **Authentication:** JWT with session validation
- **Currency:** Coins (1 coin = $1)
- **Special Rule:** 2% cashback on all bookings
- **Rate Limit:** 200 requests/minute

## Running the Services

All services are configured to run via Docker Compose and use `uv` for fast dependency management:

```bash
# Start all mock services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services (if needed)
docker-compose build --no-cache
```

## Data Reset

**Important:** All mock services reset their data to initial state every hour. This simulates a testing environment where you always have predictable test data.

## Test Credentials

### CoffeeChain
- API Key: `test_cc_api_key_12345`
- Test Members:
  - `CC1234567` - John Doe (150,000 stars)
  - `CC2222222` - Jane Smith (45,000 stars)
  - `CC3333333` - Bob Johnson (500,000 stars)
  - `CC0000000` - Test User (1,000 stars - low balance)

### TelcoCorp
- Client ID: `telcocorp_client_id`
- Client Secret: `telcocorp_client_secret`
- Test Customers:
  - `TC-ABC123` - Alice Johnson (25,000 points)
  - `TC-DEF456` - David Brown (150,000 points)
  - `TC-GHI789` - Emma Wilson (5,000 points)

### FintechApp
- Test Users:
  - `FA_12345678` - Sarah Connor (2,500 coins)
  - `FA_87654321` - Michael Chen (10,000 coins)
  - `FA_11111111` - Test User (50 coins - low balance)

## Error Simulation

All services support error simulation via the `X-Mock-Error` header:

```bash
# Simulate general error
curl -H "X-Mock-Error: true" ...

# Simulate specific errors
curl -H "X-Mock-Error: insufficient-balance" ...
curl -H "X-Mock-Error: auth-failed" ...
curl -H "X-Mock-Error: api-timeout" ...
curl -H "X-Mock-Error: approval-required" ...  # CoffeeChain only
curl -H "X-Mock-Error: invalid-member" ...     # FintechApp only
```

## Service Endpoints

### CoffeeChain
- `GET /api/v1/members/{member_id}/balance`
- `POST /api/v1/members/{member_id}/deduct`
- `POST /api/v1/members/{member_id}/refund`
- `POST /api/v1/approvals/check`
- `GET /health`

### TelcoCorp
- `POST /oauth/token`
- `GET /api/v2/customers/{customer_id}/points`
- `POST /api/v2/customers/{customer_id}/points/use`
- `GET /api/v2/customers/{customer_id}/travel/eligibility`
- `GET /health`

### FintechApp
- `POST /api/v1/sessions/validate`
- `GET /api/v1/users/{user_id}/coins`
- `POST /api/v1/users/{user_id}/coins/deduct`
- `POST /api/v1/webhooks/validate`
- `GET /health`

## Implementation Notes

1. **Don't modify these services** - They're designed to simulate real third-party APIs
2. **Use the correct base URLs** - Your middleware should use environment variables for API URLs
3. **Handle rate limits** - Each service has different rate limits that your middleware should respect
4. **Test error cases** - Use the `X-Mock-Error` header to test your error handling
5. **Remember the hourly reset** - Don't rely on data persisting beyond an hour

## Network Communication

When running via Docker Compose, services can communicate using service names:
- `http://coffeechain-api`
- `http://telcocorp-api`
- `http://fintechapp-api`

From your host machine, use:
- `http://localhost:8001`
- `http://localhost:8002`
- `http://localhost:8003`