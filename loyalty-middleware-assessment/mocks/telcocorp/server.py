from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TelcoCorp API Mock", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# OAuth credentials
CLIENT_ID = "telcocorp_client_id"
CLIENT_SECRET = "telcocorp_client_secret"

# In-memory storage for tokens and customers
tokens = {}
customers_data = {
    "TC-ABC123": {
        "name": "Alice Johnson",
        "email": "alice.j@email.com",
        "points": 25000,  # 25,000 points = $250
        "status": "active",
        "tier": "gold",
        "travel_eligible": True
    },
    "TC-DEF456": {
        "name": "David Brown",
        "email": "david.b@email.com",
        "points": 150000,  # 150,000 points = $1,500
        "status": "active",
        "tier": "platinum",
        "travel_eligible": True
    },
    "TC-GHI789": {
        "name": "Emma Wilson",
        "email": "emma.w@email.com",
        "points": 5000,  # 5,000 points = $50
        "status": "active",
        "tier": "silver",
        "travel_eligible": True
    }
}

# Track point usage for refunds
usage_log = {}

# Track last reset time
last_reset = datetime.utcnow()

def reset_data_if_needed():
    """Reset data every hour"""
    global last_reset, customers_data, usage_log, tokens
    if datetime.utcnow() - last_reset > timedelta(hours=1):
        customers_data = {
            "TC-ABC123": {"name": "Alice Johnson", "email": "alice.j@email.com", "points": 25000, "status": "active", "tier": "gold", "travel_eligible": True},
            "TC-DEF456": {"name": "David Brown", "email": "david.b@email.com", "points": 150000, "status": "active", "tier": "platinum", "travel_eligible": True},
            "TC-GHI789": {"name": "Emma Wilson", "email": "emma.w@email.com", "points": 5000, "status": "active", "tier": "silver", "travel_eligible": True}
        }
        usage_log = {}
        tokens = {}
        last_reset = datetime.utcnow()
        logger.info("Data reset completed")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and add rate limit headers"""
    reset_data_if_needed()
    
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "50"
    response.headers["X-RateLimit-Remaining"] = "45"
    response.headers["X-RateLimit-Reset"] = str(int((datetime.utcnow() + timedelta(minutes=1)).timestamp()))
    
    return response

def check_mock_error(x_mock_error: Optional[str] = Header(None)):
    """Simulate errors for testing"""
    if x_mock_error == "true":
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Simulated error for testing"
            }
        )
    elif x_mock_error == "auth-failed":
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Authentication failed"
            }
        )
    elif x_mock_error == "api-timeout":
        import time
        time.sleep(35)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify OAuth token"""
    token = credentials.credentials
    
    if token not in tokens:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_token",
                "message": "Invalid or expired token"
            }
        )
    
    token_data = tokens[token]
    
    # Check if token is expired
    if datetime.utcnow() > token_data["expires_at"]:
        del tokens[token]
        raise HTTPException(
            status_code=401,
            detail={
                "error": "token_expired",
                "message": "Token has expired"
            }
        )
    
    return token_data

class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    scope: Optional[str] = "points:read points:use"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str

@app.post("/oauth/token")
async def get_oauth_token(
    request: TokenRequest,
    x_mock_error: Optional[str] = Header(None)
):
    """OAuth 2.0 token endpoint"""
    check_mock_error(x_mock_error)
    
    if request.grant_type != "client_credentials":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_grant_type",
                "message": "Only client_credentials grant type is supported"
            }
        )
    
    if request.client_id != CLIENT_ID or request.client_secret != CLIENT_SECRET:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_client",
                "message": "Invalid client credentials"
            }
        )
    
    # Generate token
    token = f"tc_token_{secrets.token_urlsafe(32)}"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    tokens[token] = {
        "expires_at": expires_at,
        "scope": request.scope or "points:read points:use",
        "client_id": request.client_id
    }
    
    return TokenResponse(
        access_token=token,
        expires_in=3600,
        scope=request.scope or "points:read points:use"
    )

class PointsBalance(BaseModel):
    customer_id: str
    points: int
    tier: str
    status: str

@app.get("/api/v2/customers/{customer_id}/points")
async def get_customer_points(
    customer_id: str,
    token_data: dict = Depends(verify_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Get customer's points balance"""
    check_mock_error(x_mock_error)
    
    if customer_id not in customers_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "customer_not_found",
                "message": f"Customer {customer_id} not found"
            }
        )
    
    customer = customers_data[customer_id]
    return PointsBalance(
        customer_id=customer_id,
        points=customer["points"],
        tier=customer["tier"],
        status=customer["status"]
    )

class UsePointsRequest(BaseModel):
    points: int
    reference_id: str
    description: str
    travel_class: str = "economy"

class UsePointsResponse(BaseModel):
    transaction_id: str
    customer_id: str
    points_used: int
    remaining_points: int
    timestamp: str

@app.post("/api/v2/customers/{customer_id}/points/use")
async def use_customer_points(
    customer_id: str,
    request: UsePointsRequest,
    token_data: dict = Depends(verify_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Use customer points for booking"""
    check_mock_error(x_mock_error)
    
    if x_mock_error == "insufficient-balance":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_points",
                "message": "Customer has insufficient points",
                "current_points": 1000,
                "requested_points": request.points
            }
        )
    
    # TelcoCorp only allows economy class
    if request.travel_class != "economy":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_travel_class",
                "message": "TelcoCorp members can only book economy class",
                "allowed_classes": ["economy"]
            }
        )
    
    if customer_id not in customers_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "customer_not_found",
                "message": f"Customer {customer_id} not found"
            }
        )
    
    customer = customers_data[customer_id]
    
    if customer["points"] < request.points:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_points",
                "message": "Customer has insufficient points",
                "current_points": customer["points"],
                "requested_points": request.points
            }
        )
    
    # Use points
    customer["points"] -= request.points
    transaction_id = f"tctxn_{uuid.uuid4().hex[:12]}"
    
    # Log usage for potential refund
    usage_log[transaction_id] = {
        "customer_id": customer_id,
        "points": request.points,
        "reference_id": request.reference_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return UsePointsResponse(
        transaction_id=transaction_id,
        customer_id=customer_id,
        points_used=request.points,
        remaining_points=customer["points"],
        timestamp=datetime.utcnow().isoformat()
    )

class TravelEligibility(BaseModel):
    customer_id: str
    eligible: bool
    allowed_classes: list[str]
    restrictions: Optional[list[str]]

@app.get("/api/v2/customers/{customer_id}/travel/eligibility")
async def check_travel_eligibility(
    customer_id: str,
    token_data: dict = Depends(verify_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Check customer's travel eligibility and restrictions"""
    check_mock_error(x_mock_error)
    
    if customer_id not in customers_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "customer_not_found",
                "message": f"Customer {customer_id} not found"
            }
        )
    
    customer = customers_data[customer_id]
    
    return TravelEligibility(
        customer_id=customer_id,
        eligible=customer["travel_eligible"],
        allowed_classes=["economy"],  # TelcoCorp only allows economy
        restrictions=["Economy class only", "No upgrades available"]
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "telcocorp-mock",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)