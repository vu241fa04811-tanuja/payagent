import uuid
import logging
from typing import Dict, Any
from backend.models import AgentRunResponse
from backend.db import db
from agent.logger import AgentLogger
from agent.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)

class PayAgentRunner:
    def __init__(self):
        self.llm_adapter = LLMAdapter()

    def run_agent(self, prompt: str) -> AgentRunResponse:
        session_id = f"sess_{uuid.uuid4().hex[:10]}"
        agent_logger = AgentLogger()

        agent_logger.log(
            step="AGENT_INITIALIZATION",
            reasoning=f"Initialized PayAgent session '{session_id}' for prompt: '{prompt}'",
            status="SUCCESS"
        )

        try:
            result = self.llm_adapter.execute_autonomous_loop(prompt=prompt, logger_instance=agent_logger)
            
            final_status = result.get("status", "COMPLETED")
            amount_spent = result.get("amount_spent", 0.0)
            purchased_item = result.get("purchased_item")
            order_id = result.get("order_id")
            payment_link = result.get("payment_link_url")
            payment_id = result.get("payment_id")
            item_id = purchased_item.get("id") if purchased_item else None

            # Persist run to SQLite database
            db.save_agent_run(
                session_id=session_id,
                prompt=prompt,
                final_status=final_status,
                purchased_item_id=item_id,
                order_id=order_id,
                payment_id=payment_id,
                amount_spent=amount_spent,
                decision_trail=agent_logger.get_logs()
            )

            return AgentRunResponse(
                session_id=session_id,
                prompt=prompt,
                final_status=final_status,
                total_amount_spent=amount_spent,
                purchased_item=purchased_item,
                order_id=order_id,
                payment_link=payment_link,
                payment_id=payment_id,
                decision_trail=agent_logger.get_logs()
            )

        except Exception as e:
            logger.error(f"Fatal error in agent execution loop: {e}", exc_info=True)
            agent_logger.log(
                step="FATAL_ERROR",
                reasoning=f"Unhandled exception in agent loop: {str(e)}",
                status="FAILED"
            )
            return AgentRunResponse(
                session_id=session_id,
                prompt=prompt,
                final_status="FAILED",
                total_amount_spent=0.0,
                purchased_item=None,
                order_id=None,
                payment_link=None,
                payment_id=None,
                decision_trail=agent_logger.get_logs()
            )

pay_agent_runner = PayAgentRunner()
