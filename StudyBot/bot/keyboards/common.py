from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Оставить заказ", callback_data="create_order")
    builder.button(text="📋 Мои заказы", callback_data="my_orders")
    builder.button(text="ℹ️ Правила", callback_data="show_rules")
    builder.button(text="💬 Чат с поддержкой", url="https://t.me/StudyTipsSupport")
    builder.adjust(1)
    return builder.as_markup()

def get_back_kb(back_to: str = "back_to_start"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=back_to)
    return builder.as_markup()