from datetime import datetime
from typing import List, Optional, Any, Dict
from backend.models import DecisionLogEntry

class AgentLogger:
    def __init__(self):
        self.logs: List[DecisionLogEntry] = []

    def log(self, step: str, reasoning: str, status: str = "REASONING", tool_name: Optional[str] = None, tool_args: Optional[Dict[str, Any]] = None, output: Optional[Any] = None):
        entry = DecisionLogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            step=step,
            tool_name=tool_name,
            tool_args=tool_args,
            reasoning=reasoning,
            status=status,
            output=output
        )
        self.logs.append(entry)
        return entry

    def get_logs(self) -> List[DecisionLogEntry]:
        return self.logs
