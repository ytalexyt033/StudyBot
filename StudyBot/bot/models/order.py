from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class Order:
    order_id: str
    type: str
    subject: str
    description: str
    deadline: str
    budget: int
    client_id: int
    executor_id: Optional[int] = None
    status: str = "active"
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    message_id: Optional[int] = None

    @property
    def type_display(self) -> tuple:
        from config.constants import ORDER_TYPES
        return ORDER_TYPES.get(self.type, ("✏️", "ДРУГОЕ ЗАДАНИЕ"))

    @property
    def status_display(self) -> str:
        from config.constants import ORDER_STATUS_DISPLAY
        return ORDER_STATUS_DISPLAY.get(self.status, "❓ Неизвестен")