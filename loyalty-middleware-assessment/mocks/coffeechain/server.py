from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CoffeeChain API Mock", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test API key
TEST_API_KEY = "test_cc_api_key_12345"

# In-memory storage for members (resets hourly in production)
members_data = {
    "CC1234567": {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "balance": 150000,  # 150,000 stars = $1,500
        "status": "active",
        "tier": "gold"
    },
    "CC2222222": {
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "balance": 45000,  # 45,000 stars = $450
        "status": "active",
        "tier": "silver"
    },
    "CC3333333": {
        "name": "Bob Johnson",
        "email": "bob.johnson@email.com",
        "balance": 500000,  # 500,000 stars = $5,000
        "status": "active",
        "tier": "platinum"
    },
    "CC0000000": {
        "name": "Test User",
        "email": "test@email.com",
        "balance": 1000,  # 1,000 stars = $10 (low balance for testing)
        "status": "active",
        "tier": "bronze"
    }
}

# Track deductions for refunds
deductions_log = {}

# Track last reset time
last_reset = datetime.utcnow()

def reset_data_if_needed():
    """Reset data every hour"""
    global last_reset, members_data, deductions_log
    if datetime.utcnow() - last_reset > timedelta(hours=1):
        # Reset to initial state
        members_data = {
            "CC1234567": {"name": "John Doe", "email": "john.doe@email.com", "balance": 150000, "status": "active", "tier": "gold"},
            "CC2222222": {"name": "Jane Smith", "email": "jane.smith@email.com", "balance": 45000, "status": "active", "tier": "silver"},
            "CC3333333": {"name": "Bob Johnson", "email": "bob.johnson@email.com", "balance": 500000, "status": "active", "tier": "platinum"},
            "CC0000000": {"name": "Test User", "email": "test@email.com", "balance": 1000, "status": "active", "tier": "bronze"}
        }
        deductions_log = {}
        last_reset = datetime.utcnow()
        logger.info("Data reset completed")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    reset_data_if_needed()
    
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "95"
    response.headers["X-RateLimit-Reset"] = str(int((datetime.utcnow() + timedelta(minutes=1)).timestamp()))
    
    return response

def verify_api_key(x_cc_api_key: Optional[str] = Header(None)):
    """Verify API key"""
    if x_cc_api_key != TEST_API_KEY:
        logger.warning(f"Invalid API key: {x_cc_api_key}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Invalid API key"
            }
        )
    return x_cc_api_key

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
        time.sleep(35)  # Simulate timeout

class BalanceResponse(BaseModel):
    member_id: str
    balance: int
    currency: str = "stars"
    tier: str
    status: str

@app.get("/api/v1/members/{member_id}/balance")
async def get_member_balance(
    member_id: str,
    x_cc_api_key: str = Header(None),
    x_mock_error: Optional[str] = Header(None)
):
    """Get member's star balance"""
    verify_api_key(x_cc_api_key)
    check_mock_error(x_mock_error)
    
    if member_id not in members_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "member_not_found",
                "message": f"Member {member_id} not found"
            }
        )
    
    member = members_data[member_id]
    return BalanceResponse(
        member_id=member_id,
        balance=member["balance"],
        tier=member["tier"],
        status=member["status"]
    )

class DeductRequest(BaseModel):
    amount: int
    reference_id: str
    description: str

class DeductResponse(BaseModel):
    transaction_id: str
    member_id: str
    amount_deducted: int
    remaining_balance: int
    timestamp: str

@app.post("/api/v1/members/{member_id}/deduct")
async def deduct_stars(
    member_id: str,
    request: DeductRequest,
    x_cc_api_key: str = Header(None),
    x_mock_error: Optional[str] = Header(None)
):
    """Deduct stars from member balance"""
    verify_api_key(x_cc_api_key)
    check_mock_error(x_mock_error)
    
    if x_mock_error == "insufficient-balance":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_balance",
                "message": "Member has insufficient stars",
                "current_balance": 1000,
                "requested_amount": request.amount
            }
        )
    
    if member_id not in members_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "member_not_found",
                "message": f"Member {member_id} not found"
            }
        )
    
    member = members_data[member_id]
    
    if member["balance"] < request.amount:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_balance",
                "message": "Member has insufficient stars",
                "current_balance": member["balance"],
                "requested_amount": request.amount
            }
        )
    
    # Deduct stars
    member["balance"] -= request.amount
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    
    # Log deduction for potential refund
    deductions_log[transaction_id] = {
        "member_id": member_id,
        "amount": request.amount,
        "reference_id": request.reference_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return DeductResponse(
        transaction_id=transaction_id,
        member_id=member_id,
        amount_deducted=request.amount,
        remaining_balance=member["balance"],
        timestamp=datetime.utcnow().isoformat()
    )

class RefundRequest(BaseModel):
    transaction_id: str
    reason: str

class RefundResponse(BaseModel):
    refund_id: str
    transaction_id: str
    member_id: str
    amount_refunded: int
    new_balance: int
    timestamp: str

@app.post("/api/v1/members/{member_id}/refund")
async def refund_stars(
    member_id: str,
    request: RefundRequest,
    x_cc_api_key: str = Header(None),
    x_mock_error: Optional[str] = Header(None)
):
    """Refund stars to member"""
    verify_api_key(x_cc_api_key)
    check_mock_error(x_mock_error)
    
    if request.transaction_id not in deductions_log:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "transaction_not_found",
                "message": f"Transaction {request.transaction_id} not found"
            }
        )
    
    transaction = deductions_log[request.transaction_id]
    
    if transaction["member_id"] != member_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "unauthorized",
                "message": "Transaction does not belong to this member"
            }
        )
    
    if member_id not in members_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "member_not_found",
                "message": f"Member {member_id} not found"
            }
        )
    
    # Refund stars
    member = members_data[member_id]
    member["balance"] += transaction["amount"]
    
    refund_id = f"ref_{uuid.uuid4().hex[:12]}"
    
    return RefundResponse(
        refund_id=refund_id,
        transaction_id=request.transaction_id,
        member_id=member_id,
        amount_refunded=transaction["amount"],
        new_balance=member["balance"],
        timestamp=datetime.utcnow().isoformat()
    )

class ApprovalCheckRequest(BaseModel):
    member_id: str
    amount: int
    booking_reference: str

class ApprovalCheckResponse(BaseModel):
    approval_required: bool
    approval_id: Optional[str]
    reason: Optional[str]
    estimated_time: Optional[str]

@app.post("/api/v1/approvals/check")
async def check_approval_requirement(
    request: ApprovalCheckRequest,
    x_cc_api_key: str = Header(None),
    x_mock_error: Optional[str] = Header(None)
):
    """Check if booking requires approval (>50k stars)"""
    verify_api_key(x_cc_api_key)
    check_mock_error(x_mock_error)
    
    if x_mock_error == "approval-required":
        return ApprovalCheckResponse(
            approval_required=True,
            approval_id=f"appr_{uuid.uuid4().hex[:12]}",
            reason="Forced approval for testing",
            estimated_time="PT24H"
        )
    
    # Check if amount exceeds 50,000 stars
    if request.amount > 50000:
        return ApprovalCheckResponse(
            approval_required=True,
            approval_id=f"appr_{uuid.uuid4().hex[:12]}",
            reason=f"Booking exceeds 50,000 stars limit ({request.amount} stars)",
            estimated_time="PT24H"  # 24 hours in ISO 8601 duration
        )
    
    return ApprovalCheckResponse(
        approval_required=False,
        approval_id=None,
        reason=None,
        estimated_time=None
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "coffeechain-mock",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)