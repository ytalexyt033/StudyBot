from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Dispute:
    dispute_id: str
    order_id: str
    opened_by: int
    admin_id: Optional[int] = None
    reason: Optional[str] = None
    status: str = "opened"
    resolution: Optional[str] = None
    created_at: datetime = None
    resolved_at: Optional[datetime] = None