from enum import Enum

class OrderStatus(str, Enum):
    ACTIVE = "active"
    TAKEN = "taken"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELED = "canceled"
    DISPUTE = "dispute"

class UserRole(str, Enum):
    CUSTOMER = "customer"
    EXECUTOR = "executor"
    ADMIN = "admin"

class DisputeStatus(str, Enum):
    OPENED = "opened"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

ORDER_TYPES = {
    "exam": ("📚", "ЭКЗАМЕН"),
    "coursework": ("📝", "КУРСОВАЯ"), 
    "other": ("✏️", "ДРУГОЕ ЗАДАНИЕ")
}

ORDER_STATUS_DISPLAY = {
    OrderStatus.ACTIVE: "🟢 Активен",
    OrderStatus.TAKEN: "🟣 Принят",
    OrderStatus.IN_PROGRESS: "🟠 В работе",
    OrderStatus.UNDER_REVIEW: "🔵 На проверке",
    OrderStatus.COMPLETED: "✅ Завершен",
    OrderStatus.CANCELED: "❌ Отменен",
    OrderStatus.DISPUTE: "⚖️ Спор"
}