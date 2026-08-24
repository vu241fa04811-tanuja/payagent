from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float  # Price in INR
    stock: int
    description: str
    rating: float = 4.5
    image_url: Optional[str] = None

class CreateOrderRequest(BaseModel):
    product_id: str
    quantity: int = 1

class RazorpayOrder(BaseModel):
    id: str
    entity: str = "order"
    amount: int  # in paise (1 INR = 100 paise)
    currency: str = "INR"
    receipt: str
    status: str
    product_id: str
    created_at: int

class PaymentLinkRequest(BaseModel):
    order_id: str
    description: Optional[str] = None

class RazorpayPaymentLink(BaseModel):
    id: str
    short_url: str
    order_id: str
    amount: int  # in paise
    currency: str = "INR"
    status: str
    created_at: int

class PaymentConfirmationRequest(BaseModel):
    payment_id: str
    order_id: str

class DecisionLogEntry(BaseModel):
    timestamp: str
    step: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    reasoning: str
    status: str  # SUCCESS, FAILED, RECOVERING, REASONING
    output: Optional[Any] = None

class AgentRunRequest(BaseModel):
    prompt: str

class AgentRunResponse(BaseModel):
    session_id: str
    prompt: str
    final_status: str  # COMPLETED, FAILED
    total_amount_spent: float
    purchased_item: Optional[Dict[str, Any]] = None
    order_id: Optional[str] = None
    payment_link: Optional[str] = None
    payment_id: Optional[str] = None
    decision_trail: List[DecisionLogEntry]
