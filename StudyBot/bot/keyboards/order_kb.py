from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config.constants import ORDER_TYPES, OrderStatus
from models.order import Order

def get_order_type_kb():
    builder = InlineKeyboardBuilder()
    for typ, (emoji, name) in ORDER_TYPES.items():
        builder.button(text=f"{emoji} {name}", callback_data=f"type_{typ}")
    builder.button(text="🔙 Назад", callback_data="back_to_start")
    builder.adjust(1)
    return builder.as_markup()

def get_order_confirmation_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, создать", callback_data="final_confirm")
    builder.button(text="✏️ Редактировать", callback_data="edit_order")
    builder.button(text="🔙 Назад", callback_data="back_to_budget")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_order_accept_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Взять заказ", callback_data=f"accept_{order_id}")
    return builder.as_markup()

def get_order_actions_kb(order: Order):
    builder = InlineKeyboardBuilder()
    
    if order.status == OrderStatus.ACTIVE.value:
        builder.button(text="✅ Взять заказ", callback_data=f"accept_{order.order_id}")
        builder.button(text="❌ Отменить", callback_data=f"cancel_{order.order_id}")
    elif order.status == OrderStatus.TAKEN.value:
        builder.button(text="🔄 В работу", callback_data=f"progress_{order.order_id}")
        builder.button(text="❌ Отменить", callback_data=f"cancel_{order.order_id}")
    elif order.status == OrderStatus.IN_PROGRESS.value:
        builder.button(text="🔍 На проверку", callback_data=f"review_{order.order_id}")
        builder.button(text="⚖️ Спор", callback_data=f"dispute_{order.order_id}")
    elif order.status == OrderStatus.UNDER_REVIEW.value:
        builder.button(text="✅ Завершить", callback_data=f"complete_{order.order_id}")
        builder.button(text="⚖️ Спор", callback_data=f"dispute_{order.order_id}")
    elif order.status == OrderStatus.DISPUTE.value:
        builder.button(text="⚖️ Принять спор", callback_data=f"take_dispute_{order.order_id}")
    
    builder.adjust(2)
    return builder.as_markup()

def get_order_created_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Повысить бюджет", callback_data=f"increase_{order_id}")
    builder.button(text="📋 Мои заказы", callback_data="my_orders")
    builder.button(text="🔙 В главное меню", callback_data="back_to_start")
    builder.adjust(1)
    return builder.as_markup()

def get_rating_kb(order_id: str):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"{i}⭐", callback_data=f"rate_{order_id}_{i}")
    builder.adjust(5)
    return builder.as_markup()