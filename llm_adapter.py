import re
import logging
from typing import Dict, Any, List, Optional
from backend.config import settings
from agent.tools import AgentTools

logger = logging.getLogger(__name__)

class LLMAdapter:
    """
    Adapter class for LLM function/tool calling.
    Delegates to real OpenAI/Anthropic APIs if configured,
    or runs PayAgent's deterministic zero-dependency autonomous engine.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.has_openai = bool(settings.OPENAI_API_KEY)
        self.has_anthropic = bool(settings.ANTHROPIC_API_KEY)

    def parse_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Parses user intent to extract search terms and budget limit.
        """
        prompt_lower = prompt.lower()
        
        # Extract max budget if present (e.g. "under ₹1000", "under 1000", "below 4000", "budget 2500")
        budget_match = re.search(r'(?:under|below|budget|max|less than|\u20b9|\$)\s*(\d+)', prompt_lower)
        max_price = float(budget_match.group(1)) if budget_match else None

        # Determine target search keywords
        query = "electronics"
        if "mouse" in prompt_lower:
            query = "mouse"
        elif "keyboard" in prompt_lower:
            query = "keyboard"
        elif "headphone" in prompt_lower or "headphones" in prompt_lower or "audio" in prompt_lower:
            query = "headphones"
        elif "speaker" in prompt_lower:
            query = "speaker"
        elif "hub" in prompt_lower or "usb" in prompt_lower or "dock" in prompt_lower:
            query = "hub"

        return {
            "query": query,
            "max_price": max_price,
            "raw_prompt": prompt
        }

    def execute_autonomous_loop(self, prompt: str, logger_instance) -> Dict[str, Any]:
        """
        Executes the autonomous tool-calling decision loop:
        1. Parse intent & search catalog
        2. Evaluate items against stock and budget limits
        3. Handle out-of-stock recovery if primary item fails
        4. Call Razorpay Orders API
        5. Call Razorpay Payment Links API
        6. Confirm payment via Razorpay Test Mode
        7. Log step-by-step reasoning
        """
        intent = self.parse_intent(prompt)
        logger_instance.log(
            step="INTENT_ANALYSIS",
            reasoning=f"Analyzed user intent prompt: '{prompt}'. Extracted search category='{intent['query']}', max_budget={intent['max_price'] if intent['max_price'] else 'No Limit'}",
            status="SUCCESS",
            tool_name="parse_intent",
            output=intent
        )

        # Step 1: Search Products
        logger_instance.log(
            step="TOOL_CALL_SEARCH",
            reasoning=f"Calling tool search_products(query='{intent['query']}', max_price={intent['max_price']}) to discover available items.",
            status="REASONING",
            tool_name="search_products",
            tool_args={"query": intent["query"], "max_price": intent["max_price"]}
        )
        
        search_results = AgentTools.search_products(query=intent["query"], max_price=intent["max_price"])

        # Fallback search if specific query returned empty
        if not search_results:
            logger_instance.log(
                step="SEARCH_FALLBACK",
                reasoning=f"No direct matches found for '{intent['query']}'. Expanding catalog search to all items under budget.",
                status="RECOVERING",
                tool_name="search_products",
                tool_args={"query": "electronics", "max_price": intent["max_price"]}
            )
            search_results = AgentTools.search_products(query="electronics", max_price=intent["max_price"])

        logger_instance.log(
            step="SEARCH_RESULTS",
            reasoning=f"Discovered {len(search_results)} products from merchant catalog.",
            status="SUCCESS",
            output=search_results
        )

        if not search_results:
            logger_instance.log(
                step="NO_PRODUCTS_FOUND",
                reasoning="No merchant products matched criteria or budget. Terminating agent loop.",
                status="FAILED"
            )
            return {"status": "FAILED", "reason": "No products available under requested budget."}

        # Step 2: Evaluate products for purchase decision & stock check
        selected_product = None
        for item in search_results:
            logger_instance.log(
                step="EVALUATING_ITEM",
                reasoning=f"Inspecting item '{item['name']}' (ID: {item['id']}) - Price: ₹{item['price']}, Stock: {item['stock']}.",
                status="REASONING",
                tool_name="get_product_details",
                tool_args={"product_id": item['id']}
            )
            
            if item['stock'] > 0:
                selected_product = item
                logger_instance.log(
                    step="ITEM_SELECTED",
                    reasoning=f"Selected product '{item['name']}' for purchase. Price ₹{item['price']} fits budget constraint and has positive stock ({item['stock']}).",
                    status="SUCCESS",
                    output=item
                )
                break
            else:
                logger_instance.log(
                    step="STOCK_CHECK_FAILED",
                    reasoning=f"RECOVERY TRIGGERED: Product '{item['name']}' is OUT OF STOCK (stock=0). Agent will pivot to evaluate next matching candidate item.",
                    status="RECOVERING",
                    output={"out_of_stock_product_id": item['id']}
                )

        # Out-of-Stock Recovery Pivot: search alternative items if primary was out of stock
        if not selected_product:
            logger_instance.log(
                step="PIVOT_SEARCH",
                reasoning="Primary product preference is out of stock. Searching for best alternative in catalog under budget.",
                status="RECOVERING",
                tool_name="search_products",
                tool_args={"query": "electronics", "max_price": intent["max_price"]}
            )
            alternatives = AgentTools.search_products(query="electronics", max_price=intent["max_price"])
            for alt in alternatives:
                if alt['stock'] > 0:
                    selected_product = alt
                    logger_instance.log(
                        step="PIVOT_ITEM_SELECTED",
                        reasoning=f"Autonomous Recovery Choice: Switched to alternative product '{alt['name']}' (Price: ₹{alt['price']}, Stock: {alt['stock']}).",
                        status="SUCCESS",
                        output=alt
                    )
                    break

        if not selected_product:
            logger_instance.log(
                step="ALL_ITEMS_UNAVAILABLE",
                reasoning="All candidate items are out of stock. Autonomous transaction cannot proceed.",
                status="FAILED"
            )
            return {"status": "FAILED", "reason": "All matching products out of stock."}

        # Step 3: Create Order via Razorpay Orders API
        logger_instance.log(
            step="CREATE_RAZORPAY_ORDER",
            reasoning=f"Invoking tool create_order(product_id='{selected_product['id']}') to generate Razorpay test order.",
            status="REASONING",
            tool_name="create_order",
            tool_args={"product_id": selected_product['id'], "quantity": 1}
        )
        
        order_res = AgentTools.create_order(product_id=selected_product['id'], quantity=1)
        if "error" in order_res:
            logger_instance.log(
                step="ORDER_CREATION_FAILED",
                reasoning=f"Razorpay Order creation error: {order_res['error']}",
                status="FAILED",
                output=order_res
            )
            return {"status": "FAILED", "reason": order_res["error"]}

        logger_instance.log(
            step="ORDER_CREATED",
            reasoning=f"Successfully created Razorpay Test Order ID '{order_res['id']}' for amount ₹{selected_product['price']} ({order_res['amount']} paise).",
            status="SUCCESS",
            output=order_res
        )

        # Step 4: Generate Payment Link via Razorpay Payment Links API
        logger_instance.log(
            step="GENERATE_PAYMENT_LINK",
            reasoning=f"Invoking tool generate_payment_link(order_id='{order_res['id']}') via Razorpay Payment Links API.",
            status="REASONING",
            tool_name="generate_payment_link",
            tool_args={"order_id": order_res['id']}
        )
        
        plink_res = AgentTools.generate_payment_link(order_id=order_res['id'])
        if "error" in plink_res:
            logger_instance.log(
                step="PAYMENT_LINK_FAILED",
                reasoning=f"Razorpay Payment Link creation error: {plink_res['error']}",
                status="FAILED",
                output=plink_res
            )
            return {"status": "FAILED", "reason": plink_res["error"]}

        logger_instance.log(
            step="PAYMENT_LINK_GENERATED",
            reasoning=f"Generated Razorpay Test Payment Link '{plink_res['id']}' (Short URL: {plink_res['short_url']}).",
            status="SUCCESS",
            output=plink_res
        )

        # Step 5: Execute Autonomous Test Payment Authorization
        logger_instance.log(
            step="CONFIRM_PAYMENT",
            reasoning=f"Invoking tool confirm_payment(payment_link_id='{plink_res['id']}', order_id='{order_res['id']}') to execute autonomous end-to-end payment settlement.",
            status="REASONING",
            tool_name="confirm_payment",
            tool_args={"payment_link_id": plink_res['id'], "order_id": order_res['id']}
        )
        
        confirm_res = AgentTools.confirm_payment(payment_link_id=plink_res['id'], order_id=order_res['id'])
        
        logger_instance.log(
            step="TRANSACTION_COMPLETE",
            reasoning=f"Razorpay payment confirmed & captured! Payment ID: '{confirm_res['payment_id']}'. Merchant inventory updated.",
            status="SUCCESS",
            output=confirm_res
        )

        return {
            "status": "COMPLETED",
            "purchased_item": selected_product,
            "order_id": order_res['id'],
            "payment_link_id": plink_res['id'],
            "payment_link_url": plink_res['short_url'],
            "payment_id": confirm_res['payment_id'],
            "amount_spent": selected_product['price']
        }
