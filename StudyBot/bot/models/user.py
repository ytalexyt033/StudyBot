from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    role: str = "customer"
    rating: float = 0.0
    completed_orders: int = 0
    created_at: datetime = None

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f"{self.first_name or ''} {self.last_name or ''}".strip()