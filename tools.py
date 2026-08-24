import logging
from typing import Dict, Any, List, Optional
from backend.db import db
from backend.razorpay_client import razorpay_client

logger = logging.getLogger(__name__)

# Tool Schemas for OpenAI / Anthropic Tool Calling format
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Searches the merchant catalog for products matching a query or category, with optional budget filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or category (e.g. 'mouse', 'audio', 'keyboard')"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum budget/price limit in INR"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Fetches complete product information including price, description, rating, and stock level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The unique product ID (e.g. 'prod_mouse_01')"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Calls Razorpay Test Mode Orders API to create an order for a given product and quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID to purchase"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to order (default 1)",
                        "default": 1
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_payment_link",
            "description": "Calls Razorpay Test Mode Payment Links API to generate a checkout payment link for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The Razorpay order ID returned by create_order"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_payment",
            "description": "Simulates / verifies payment authorization on Razorpay test mode and completes the transaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_link_id": {
                        "type": "string",
                        "description": "The payment link ID"
                    },
                    "order_id": {
                        "type": "string",
                        "description": "The Razorpay order ID"
                    }
                },
                "required": ["payment_link_id", "order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_decision",
            "description": "Logs agent reasoning, status updates, or error recovery rationale for audit trail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Explanations of why the decision was taken"
                    },
                    "status": {
                        "type": "string",
                        "description": "Current status (SUCCESS, FAILED, RECOVERING, REASONING)"
                    }
                },
                "required": ["reasoning", "status"]
            }
        }
    }
]

class AgentTools:
    @staticmethod
    def search_products(query: str, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        products = db.search_products(query=query, max_price=max_price)
        return [p.dict() for p in products]

    @staticmethod
    def get_product_details(product_id: str) -> Dict[str, Any]:
        product = db.get_product_by_id(product_id)
        if not product:
            return {"error": f"Product '{product_id}' not found in catalog."}
        return product.dict()

    @staticmethod
    def create_order(product_id: str, quantity: int = 1) -> Dict[str, Any]:
        product = db.get_product_by_id(product_id)
        if not product:
            return {"error": f"Cannot create order: Product '{product_id}' not found."}
        
        if product.stock < quantity:
            return {
                "error": f"OUT_OF_STOCK: Requested product '{product.name}' has stock={product.stock}, but {quantity} requested.",
                "product_id": product_id,
                "available_stock": product.stock
            }
        
        # Call Razorpay client
        order = razorpay_client.create_order(product_id=product_id, amount_in_inr=product.price, quantity=quantity)
        db.save_order(order)
        return order.dict()

    @staticmethod
    def generate_payment_link(order_id: str) -> Dict[str, Any]:
        order = db.get_order(order_id)
        if not order:
            return {"error": f"Cannot generate payment link: Order '{order_id}' not found."}
        
        product = db.get_product_by_id(order.product_id)
        prod_name = product.name if product else "Merchant Item"
        
        payment_link = razorpay_client.create_payment_link(
            order_id=order_id,
            amount_in_paise=order.amount,
            product_name=prod_name
        )
        db.save_payment_link(payment_link)
        return payment_link.dict()

    @staticmethod
    def confirm_payment(payment_link_id: str, order_id: str) -> Dict[str, Any]:
        order = db.get_order(order_id)
        if not order:
            return {"error": f"Cannot confirm payment: Order '{order_id}' not found."}
        
        payment_res = razorpay_client.simulate_confirm_payment(payment_link_id=payment_link_id, order_id=order_id)
        
        # Decrement stock in merchant DB
        stock_updated = db.decrement_stock(order.product_id, quantity=1)
        payment_res["stock_decremented"] = stock_updated
        
        return payment_res

    @staticmethod
    def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
        tool_map = {
            "search_products": AgentTools.search_products,
            "get_product_details": AgentTools.get_product_details,
            "create_order": AgentTools.create_order,
            "generate_payment_link": AgentTools.generate_payment_link,
            "confirm_payment": AgentTools.confirm_payment,
            "log_decision": lambda reasoning, status="REASONING": {"logged": True, "reasoning": reasoning, "status": status}
        }
        if tool_name not in tool_map:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        
        return tool_map[tool_name](**tool_args)
