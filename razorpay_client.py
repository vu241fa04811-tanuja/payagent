import time
import uuid
import logging
import requests
from typing import Dict, Any, Optional
from backend.config import settings
from backend.models import RazorpayOrder, RazorpayPaymentLink

logger = logging.getLogger(__name__)

class RazorpayTestClient:
    def __init__(self, key_id: str = None, key_secret: str = None):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.base_url = "https://api.razorpay.com/v1"
        self.auth = (self.key_id, self.key_secret)


    def _is_real_key(self) -> bool:
        return bool(self.key_id and self.key_id.startswith("rzp_test_") and self.key_secret and len(self.key_secret) > 10 and "mock" not in self.key_id.lower())

    def create_order(self, product_id: str, amount_in_inr: float, quantity: int = 1) -> RazorpayOrder:
        amount_in_paise = int(amount_in_inr * 100 * quantity)
        receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"

        if self._is_real_key():
            try:
                response = requests.post(
                    f"{self.base_url}/orders",
                    auth=self.auth,
                    json={
                        "amount": amount_in_paise,
                        "currency": "INR",
                        "receipt": receipt_id,
                        "notes": {
                            "product_id": product_id,
                            "created_by": "PayAgent_AI_Buyer"
                        }
                    },
                    timeout=10
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return RazorpayOrder(
                        id=data["id"],
                        entity="order",
                        amount=data["amount"],
                        currency=data["currency"],
                        receipt=data["receipt"],
                        status=data["status"],
                        product_id=product_id,
                        created_at=data["created_at"]
                    )
                else:
                    logger.warning(f"Razorpay API call failed with status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Razorpay API: {e}")

        # Fallback Test Mode Order Generator (Simulated Razorpay Test Order)
        order_id = f"order_test_{uuid.uuid4().hex[:12]}"
        return RazorpayOrder(
            id=order_id,
            entity="order",
            amount=amount_in_paise,
            currency="INR",
            receipt=receipt_id,
            status="created",
            product_id=product_id,
            created_at=int(time.time())
        )

    def create_payment_link(self, order_id: str, amount_in_paise: int, product_name: str) -> RazorpayPaymentLink:
        if self._is_real_key():
            try:
                response = requests.post(
                    f"{self.base_url}/payment_links",
                    auth=self.auth,
                    json={
                        "amount": amount_in_paise,
                        "currency": "INR",
                        "accept_partial": False,
                        "description": f"Autonomous AI Purchase: {product_name}",
                        "customer": {
                            "name": "PayAgent AI Buyer",
                            "email": "ai.agent@payagent.internal",
                            "contact": "+919999999999"
                        },
                        "notify": {"sms": False, "email": False},
                        "reminder_enable": False,
                        "notes": {
                            "order_id": order_id
                        }
                    },
                    timeout=10
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return RazorpayPaymentLink(
                        id=data["id"],
                        short_url=data["short_url"],
                        order_id=order_id,
                        amount=data["amount"],
                        currency=data["currency"],
                        status=data["status"],
                        created_at=data["created_at"]
                    )
                else:
                    logger.warning(f"Razorpay Payment Link API failed {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Razorpay Payment Link API: {e}")

        # Fallback Test Mode Payment Link Generator
        plink_id = f"plink_test_{uuid.uuid4().hex[:12]}"
        return RazorpayPaymentLink(
            id=plink_id,
            short_url=f"https://rzp.io/i/test_{uuid.uuid4().hex[:8]}",
            order_id=order_id,
            amount=amount_in_paise,
            currency="INR",
            status="created",
            created_at=int(time.time())
        )

    def simulate_confirm_payment(self, payment_link_id: str, order_id: str) -> Dict[str, Any]:
        """
        Simulates autonomous payment authorization & capture via Razorpay Test Credentials.
        Returns payment status and payment transaction details.
        """
        payment_id = f"pay_test_{uuid.uuid4().hex[:12]}"
        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "payment_link_id": payment_link_id,
            "status": "captured",
            "method": "upi",
            "upi": {
                "vpa": "payagent@razorpay"
            },
            "fee": 0,
            "tax": 0,
            "error_code": None,
            "error_description": None,
            "captured_at": int(time.time())
        }

razorpay_client = RazorpayTestClient()
