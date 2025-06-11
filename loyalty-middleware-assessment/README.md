# Loyalty Middleware Assessment

## Overview

Welcome to the Python Full Stack Engineer assessment for our Travel-as-a-Service Loyalty and Rewards team. In this challenge, you'll build a multi-tenant middleware system that enables enterprises to offer flight bookings through their loyalty programs.

**Time Expectation:** 4-6 hours

## The Challenge

Your task is to build a middleware system that:
1. Integrates with multiple enterprise loyalty programs (multi-tenant architecture)
2. Allows their members to search and book flights using loyalty points/rewards
3. Handles different authentication methods and business rules per tenant
4. Provides a unified API interface while managing tenant-specific requirements
5. Includes a dashboard for monitoring bookings across all tenants

## Client Companies

You'll integrate with three mock client APIs:

### 1. CoffeeChain ☕
- **Currency:** Stars (1 star = $0.01)
- **Authentication:** API Key (header: `X-CC-API-Key`)
- **Special Rules:** Requires manual approval for bookings over 50,000 stars
- **Member ID Format:** CC1234567

### 2. TelcoCorp 📱
- **Currency:** Points (100 points = $1)
- **Authentication:** OAuth 2.0
- **Special Rules:** Members can only book economy class
- **Customer ID Format:** TC-XXXXXX

### 3. FintechApp 💳
- **Currency:** Coins (1 coin = $1)
- **Authentication:** JWT with session validation
- **Special Rules:** 2% cashback on all bookings
- **User ID Format:** FA_XXXXXXXX

## What You Need to Build

### Backend Requirements (70% - Must Have)
- **Multi-tenant API** supporting all three authentication methods
- **Flight search** integration with Duffel API (sandbox, ask your recruiter/hiring manager for credentials)
- **Booking creation** with tenant-specific currency conversion
- **Booking management** (retrieve, list, cancel)
- **Proper error handling** following RFC 7807
- **Database persistence** for bookings and tenant data
- **Configuration management** for tenant settings
- **Rate limiting** per tenant
- **Comprehensive logging**

### Frontend Requirements (20% - Should Have)
- **Admin dashboard** showing bookings across all tenants
- **Booking details** view with tenant information
- **Basic filtering** by tenant, status, date range
- **Responsive design** for desktop and tablet
- **Error state handling**

### Nice to Have (10%)
- Unit and integration tests
- API documentation (OpenAPI/Swagger)
- Webhook support for status updates
- Docker configuration for your services
- Performance optimizations
- Advanced monitoring/metrics

## Technical Specifications

### Required Technologies
- **Backend:** Python 3.11+ (FastAPI, Django, or Flask)
- **Frontend:** Next.js, React, or vanilla TypeScript
- **Database:** PostgreSQL or MySQL (via Docker)
- **External API:** Duffel API (sandbox mode)

### API Endpoints to Implement

Your middleware should expose these endpoints:

```
POST   /api/v1/flights/search
POST   /api/v1/bookings
GET    /api/v1/bookings/{booking_id}
GET    /api/v1/bookings
POST   /api/v1/bookings/{booking_id}/cancel
GET    /api/v1/health
```

See `API_DOCUMENTATION.md` for detailed specifications.

## Getting Started

1. **Fork/clone this repository** to your GitHub account
2. **Start the mock services**
   ```bash
   docker-compose up
   ```
3. **Create your backend and frontend directories**
   ```bash
   mkdir backend frontend
   ```
4. **Update docker-compose.yml** to include your services
5. **Start building**

### Mock Services Endpoints

- CoffeeChain API: http://localhost:8001 or http://coffeechain-api (if using docker-compose)
- TelcoCorp API: http://localhost:8002 or http://telcocorp-api (if using docker-compose)
- FintechApp API: http://localhost:8003 or http://fintechapp-api (if using docker-compose)

See `docs/examples/` for authentication examples for each service.

## Expected Final Structure

```
loyalty-middleware-assessment/
├── backend/
├── frontend/
├── mocks/              (provided)
├── docs/               (provided)
└── docker-compose.yml  (update with your services)
```

## Evaluation Criteria

### Code Quality (40%)
- Clean, readable, and well-organized code
- Proper error handling and validation
- Following Python/JavaScript best practices
- Appropriate design patterns

### Functionality (30%)
- All core requirements working correctly
- Proper multi-tenant isolation
- Accurate currency conversions
- Reliable booking lifecycle management

### Architecture (20%)
- Scalable multi-tenant design
- Proper separation of concerns
- Security considerations
- Database schema design

### Documentation (10%)
- Clear setup instructions
- Code comments where necessary
- Solution documentation in `SOLUTION_TEMPLATE.md`

## Important Notes

1. **Mock services reset hourly** - Test data returns to initial state
2. **Use sandbox credentials** for Duffel API (ask your recruiter/hiring manager for credentials)
3. **Error simulation** - Use `X-Mock-Error: {ERROR_CODE}` header to test error handling (see `API_DOCUMENTATION.md`)
4. **Rate limits** - Each tenant has different limits (see API docs)
5. **Currency precision** - Maintain accuracy for financial calculations

## Submission Instructions

1. Complete your implementation in your forked/cloned repository
2. Fill out `SOLUTION_TEMPLATE.md` with your approach and decisions
3. Ensure your solution runs with `docker-compose up`
4. Submit your solution to your recruiter/hiring manager
5. Include any special setup instructions in your repository's README.md

## Resources

- [Duffel API Documentation](https://duffel.com/docs)
- [API Documentation](./API_DOCUMENTATION.md)
- [Getting Started Guide](./docs/getting_started.md)

## Questions?

If you encounter any issues with the mock services or have questions about the requirements, please open an issue in the repository.

Good luck! We're excited to see your implementation. 🚀