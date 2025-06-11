from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging
import uuid
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FintechApp API Mock", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# JWT configuration
SECRET_KEY = "fintechapp_secret_key_for_jwt_signing"
ALGORITHM = "HS256"

# In-memory storage for users and sessions
users_data = {
    "FA_12345678": {
        "name": "Sarah Connor",
        "email": "sarah.c@email.com",
        "coins": 2500.00,  # $2,500
        "status": "active",
        "cashback_rate": 0.02,  # 2%
        "total_cashback": 125.50
    },
    "FA_87654321": {
        "name": "Michael Chen",
        "email": "michael.c@email.com",
        "coins": 10000.00,  # $10,000
        "status": "active",
        "cashback_rate": 0.02,
        "total_cashback": 450.00
    },
    "FA_11111111": {
        "name": "Test User",
        "email": "test.user@email.com",
        "coins": 50.00,  # $50 (low balance for testing)
        "status": "active",
        "cashback_rate": 0.02,
        "total_cashback": 0.00
    }
}

# Track coin usage for refunds
deductions_log = {}

# Active sessions
active_sessions = {}

# Track last reset time
last_reset = datetime.utcnow()

def reset_data_if_needed():
    """Reset data every hour"""
    global last_reset, users_data, deductions_log, active_sessions
    if datetime.utcnow() - last_reset > timedelta(hours=1):
        users_data = {
            "FA_12345678": {"name": "Sarah Connor", "email": "sarah.c@email.com", "coins": 2500.00, "status": "active", "cashback_rate": 0.02, "total_cashback": 125.50},
            "FA_87654321": {"name": "Michael Chen", "email": "michael.c@email.com", "coins": 10000.00, "status": "active", "cashback_rate": 0.02, "total_cashback": 450.00},
            "FA_11111111": {"name": "Test User", "email": "test.user@email.com", "coins": 50.00, "status": "active", "cashback_rate": 0.02, "total_cashback": 0.00}
        }
        deductions_log = {}
        active_sessions = {}
        last_reset = datetime.utcnow()
        logger.info("Data reset completed")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and add rate limit headers"""
    reset_data_if_needed()
    
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "200"
    response.headers["X-RateLimit-Remaining"] = "195"
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

def create_jwt_token(user_id: str, session_id: str) -> str:
    """Create a JWT token"""
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": user_id,
        "session_id": session_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and session"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid token structure"
                }
            )
        
        # Check if session is active
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "session_expired",
                    "message": "Session has expired or is invalid"
                }
            )
        
        session = active_sessions[session_id]
        if session["user_id"] != user_id:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "session_mismatch",
                    "message": "Session does not match token"
                }
            )
        
        return {"user_id": user_id, "session_id": session_id}
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_token",
                "message": "Could not validate token"
            }
        )

class SessionValidateRequest(BaseModel):
    user_id: str
    device_id: str

class SessionValidateResponse(BaseModel):
    session_id: str
    jwt_token: str
    expires_in: int = 86400  # 24 hours
    user: dict

@app.post("/api/v1/sessions/validate")
async def validate_session(
    request: SessionValidateRequest,
    x_mock_error: Optional[str] = Header(None)
):
    """Validate user and create session with JWT"""
    check_mock_error(x_mock_error)
    
    if x_mock_error == "invalid-member":
        raise HTTPException(
            status_code=404,
            detail={
                "error": "user_not_found",
                "message": f"User {request.user_id} not found"
            }
        )
    
    if request.user_id not in users_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "user_not_found",
                "message": f"User {request.user_id} not found"
            }
        )
    
    user = users_data[request.user_id]
    
    # Create session
    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    active_sessions[session_id] = {
        "user_id": request.user_id,
        "device_id": request.device_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    
    # Create JWT
    jwt_token = create_jwt_token(request.user_id, session_id)
    
    return SessionValidateResponse(
        session_id=session_id,
        jwt_token=jwt_token,
        user={
            "user_id": request.user_id,
            "name": user["name"],
            "email": user["email"],
            "status": user["status"]
        }
    )

class CoinsBalance(BaseModel):
    user_id: str
    coins: float
    cashback_rate: float
    total_cashback: float
    currency: str = "USD"

@app.get("/api/v1/users/{user_id}/coins")
async def get_user_coins(
    user_id: str,
    token_data: dict = Depends(verify_jwt_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Get user's coin balance"""
    check_mock_error(x_mock_error)
    
    # Verify user matches token
    if token_data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Cannot access other user's data"
            }
        )
    
    if user_id not in users_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "user_not_found",
                "message": f"User {user_id} not found"
            }
        )
    
    user = users_data[user_id]
    return CoinsBalance(
        user_id=user_id,
        coins=user["coins"],
        cashback_rate=user["cashback_rate"],
        total_cashback=user["total_cashback"]
    )

class DeductCoinsRequest(BaseModel):
    amount: float
    reference_id: str
    description: str

class DeductCoinsResponse(BaseModel):
    transaction_id: str
    user_id: str
    amount_deducted: float
    cashback_earned: float
    remaining_coins: float
    timestamp: str

@app.post("/api/v1/users/{user_id}/coins/deduct")
async def deduct_coins(
    user_id: str,
    request: DeductCoinsRequest,
    token_data: dict = Depends(verify_jwt_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Deduct coins and calculate cashback"""
    check_mock_error(x_mock_error)
    
    if x_mock_error == "insufficient-balance":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_coins",
                "message": "User has insufficient coins",
                "current_coins": 10.00,
                "requested_amount": request.amount
            }
        )
    
    # Verify user matches token
    if token_data["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Cannot access other user's data"
            }
        )
    
    if user_id not in users_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "user_not_found",
                "message": f"User {user_id} not found"
            }
        )
    
    user = users_data[user_id]
    
    if user["coins"] < request.amount:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_coins",
                "message": "User has insufficient coins",
                "current_coins": user["coins"],
                "requested_amount": request.amount
            }
        )
    
    # Calculate cashback (2%)
    cashback = round(request.amount * user["cashback_rate"], 2)
    
    # Deduct coins
    user["coins"] -= request.amount
    user["coins"] += cashback  # Add cashback immediately
    user["total_cashback"] += cashback
    
    transaction_id = f"fatxn_{uuid.uuid4().hex[:12]}"
    
    # Log deduction for potential refund
    deductions_log[transaction_id] = {
        "user_id": user_id,
        "amount": request.amount,
        "cashback": cashback,
        "reference_id": request.reference_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return DeductCoinsResponse(
        transaction_id=transaction_id,
        user_id=user_id,
        amount_deducted=request.amount,
        cashback_earned=cashback,
        remaining_coins=user["coins"],
        timestamp=datetime.utcnow().isoformat()
    )

class WebhookValidationRequest(BaseModel):
    webhook_url: str
    secret: str

class WebhookValidationResponse(BaseModel):
    validated: bool
    webhook_id: str

@app.post("/api/v1/webhooks/validate")
async def validate_webhook(
    request: WebhookValidationRequest,
    token_data: dict = Depends(verify_jwt_token),
    x_mock_error: Optional[str] = Header(None)
):
    """Validate webhook endpoint (for testing)"""
    check_mock_error(x_mock_error)
    
    # Simple validation - in real implementation would test the webhook
    webhook_id = f"whk_{uuid.uuid4().hex[:12]}"
    
    return WebhookValidationResponse(
        validated=True,
        webhook_id=webhook_id
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fintechapp-mock",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)