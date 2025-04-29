from enum import Enum

class OrderStatus(Enum):
    ACTIVE = "active"
    TAKEN = "taken"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELED = "canceled"
    DISPUTE = "dispute"

class UserRole(Enum):
    CUSTOMER = "customer"
    EXECUTOR = "executor"
    ADMIN = "admin"

class DisputeStatus(Enum):
    OPENED = "opened"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

order_types = {
    "exam": ("📚", "ЭКЗАМЕН"),
    "coursework": ("📝", "КУРСОВАЯ"), 
    "other": ("✏️", "ДРУГОЕ ЗАДАНИЕ")
}