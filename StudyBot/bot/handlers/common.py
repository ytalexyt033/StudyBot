from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from models.enums import UserRole
from config import SELECTING_ACTION

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    buttons = [
        [InlineKeyboardButton("📝 Оставить заказ", callback_data="create_order")],
        [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ Правила", callback_data="show_rules")],
        [InlineKeyboardButton("💬 Чат с поддержкой", url="https://t.me/StudyTipsSupport")]
    ]
    
    user_data = db.get_user(user.id)
    if user_data and user_data['role'] == UserRole.ADMIN.value:
        buttons.append([InlineKeyboardButton("👑 Меню администратора", callback_data="admin_menu")])
    
    if user_data and user_data['role'] == UserRole.EXECUTOR.value:
        buttons.append([InlineKeyboardButton("👨‍💻 Меню исполнителя", callback_data="executor_menu")])
    
    if update.message:
        await update.message.reply_text(
            "🔹 *STUDY TIPS*\n_Решаем, пишем, спасаем — пока ты отдыхаешь!_\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "🔹 *STUDY TIPS*\n_Решаем, пишем, спасаем — пока ты отдыхаешь!_\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    
    return SELECTING_ACTION

def register_common_handlers(application):
    application.add_handler(CommandHandler("start", start))