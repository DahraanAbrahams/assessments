# Getting Started

This guide will help you set up the development environment and start building your loyalty middleware solution.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for backend development)
- Node.js 18+ (for frontend development)
- Git
- A code editor (VS Code, PyCharm, etc.)
- Duffel API sandbox account (free at https://duffel.com)

## Initial Setup

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/loyalty-middleware-assessment.git
cd loyalty-middleware-assessment
```

### 2. Copy Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Duffel API key:
```
DUFFEL_API_KEY=your_actual_duffel_sandbox_key_here
```

### 3. Start the Mock Services

```bash
docker-compose up -d
```

This will start three mock services:
- CoffeeChain API: http://localhost:8001
- TelcoCorp API: http://localhost:8002
- FintechApp API: http://localhost:8003

Verify they're running:
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### 4. Create Your Project Structure

```bash
# Create backend directory
mkdir -p backend/app/{api,core,models,services,tenants}
mkdir -p backend/tests

# Create frontend directory
mkdir -p frontend/src/{components,pages,services,utils}
mkdir -p frontend/public
```

### 5. Set Up Your Backend

Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose httpx
```

### 6. Set Up Your Frontend

```bash
cd ../frontend
npm init -y
npm install react react-dom axios
# Or use create-react-app, Vue CLI, etc.
```

### 7. Update Docker Compose

Add your services to `docker-compose.yml`. See the commented example in the file.

## Development Workflow

### Backend Development

1. Start with the database models
2. Implement tenant configuration system
3. Create authentication middleware for each tenant
4. Build the flight search integration with Duffel
5. Implement booking endpoints
6. Add proper error handling and logging

### Frontend Development

1. Create a basic dashboard layout
2. Implement booking list view
3. Add booking details modal/page
4. Create filters for tenant, status, dates
5. Add error handling and loading states

### Testing Your Implementation

Use the provided `test_mocks.py` script to verify mock services:

```bash
python test_mocks.py
```

See `docs/examples/` for authentication examples for each tenant.

## Common Issues

### Port Already in Use

If you get port conflicts, check what's using the ports:
```bash
lsof -i :8001  # On Linux/Mac
netstat -ano | findstr :8001  # On Windows
```

### Docker Network Issues

If services can't communicate, ensure they're on the same network:
```bash
docker network ls
docker network inspect loyalty-middleware-assessment_loyalty-network
```

### Mock Service Errors

Use the `X-Mock-Error` header to test error scenarios:
```bash
curl -H "X-Mock-Error: insufficient-balance" http://localhost:8001/api/v1/members/CC1234567/balance
```

## Next Steps

1. Review the [API Documentation](../API_DOCUMENTATION.md)
2. Check authentication examples in [docs/examples/](./examples/)
3. Understand the [expected structure](./expected_structure.md)
4. Start implementing!

## Tips

- Start simple - get one tenant working first
- Use environment variables for configuration
- Log everything during development
- Test error cases early
- Keep your commits small and focused
- Document your decisions in SOLUTION_TEMPLATE.md

Good luck! 🚀