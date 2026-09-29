from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserEvent:
    user_id: int
    event: str
    category: str
    event_time: datetime
