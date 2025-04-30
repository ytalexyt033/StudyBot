from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from models.user import User
from services.database import Database
from keyboards.common import get_main_menu_kb
from keyboards.common import get_back_kb
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup   

router = Router()

@router.message(Command("start"))
async def start(message: Message, db: Database):
    user = message.from_user
    db_user = User(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add_user(db_user)
    
    await message.answer(
        "🔹 *STUDY TIPS*\n_Решаем, пишем, спасаем — пока ты отдыхаешь!_\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🔹 *STUDY TIPS*\n_Решаем, пишем, спасаем — пока ты отдыхаешь!_\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "show_rules")
async def show_rules(callback: CallbackQuery):
    await callback.answer()
    
    rules_text = (
        "📜 *Правила сервиса STUDY TIPS*\n\n"
        "1. Запрещено размещать заказы, нарушающие законодательство\n"
        "2. Исполнитель обязан выполнить работу в срок\n"
        "3. Заказчик обязан оплатить работу после проверки\n"
        "4. Все споры решаются с участием администрации\n"
        "5. Максимальное количество активных заказов - 3\n\n"
        "⚠️ Нарушение правил может привести к блокировке!"
    )
    
    from keyboards.common import get_back_kb
    await callback.message.edit_text(
        rules_text,
        reply_markup=get_back_kb(),
        parse_mode="Markdown"
    )