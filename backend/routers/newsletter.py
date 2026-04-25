from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import re

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])

class NewsletterSubscription(BaseModel):
    email: EmailStr
    firstName: str = None
    tags: list = None

class NewsletterResponse(BaseModel):
    success: bool
    message: str

# Mock Mailchimp storage (in-memory for staging)
subscriptions = {}

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@router.post("/subscribe", response_model=NewsletterResponse)
async def subscribe(subscription: NewsletterSubscription):
    """Subscribe email to newsletter (mock Mailchimp integration)"""

    # Validate email format
    if not validate_email(subscription.email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )

    # Check for duplicates
    if subscription.email in subscriptions:
        raise HTTPException(
            status_code=400,
            detail="Email already subscribed"
        )

    # Mock Mailchimp: Store subscription
    subscriptions[subscription.email] = {
        "email": subscription.email,
        "firstName": subscription.firstName,
        "tags": subscription.tags or [],
        "status": "subscribed"
    }

    return {
        "success": True,
        "message": f"Successfully subscribed {subscription.email}. Check your email for welcome message!"
    }

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "subscribers": len(subscriptions)}
