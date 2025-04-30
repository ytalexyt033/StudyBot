from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from models.order import Order
from services.order_service import OrderService
from keyboards.order_kb import (
    get_order_type_kb,
    get_order_confirmation_kb,
    get_back_kb,
    get_order_actions_kb
)
from config.constants import OrderStatus
from config.settings import MAX_ORDERS_PER_USER

router = Router()

class OrderStates(StatesGroup):
    SELECTING_ORDER_TYPE = State()
    ENTERING_SUBJECT = State()
    ENTERING_DESCRIPTION = State()
    ENTERING_DEADLINE = State()
    ENTERING_BUDGET = State()
    UPLOADING_FILE = State()
    CONFIRMING_ORDER = State()

@router.callback_query(F.data == "create_order")
async def create_order(
    callback: CallbackQuery, 
    state: FSMContext,
    order_service: OrderService,
    db: Database
):
    await callback.answer()
    user = callback.from_user
    
    active_orders = db.get_user_orders(user.id, OrderStatus.ACTIVE.value)
    if len(active_orders) >= MAX_ORDERS_PER_USER:
        from keyboards.common import get_main_menu_kb
        await callback.message.edit_text(
            f"⚠️ Вы достигли лимита активных заказов ({MAX_ORDERS_PER_USER})\n\n"
            "Вы можете повысить бюджет существующих заказов или дождаться их выполнения",
            reply_markup=get_main_menu_kb()
        )
        return
    
    await state.set_state(OrderStates.SELECTING_ORDER_TYPE)
    await callback.message.edit_text(
        "📌 *Выберите тип работы:*",
        reply_markup=get_order_type_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("type_"), OrderStates.SELECTING_ORDER_TYPE)
async def set_order_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    order_type = callback.data.split("_")[1]
    await state.update_data(order_type=order_type)
    await state.set_state(OrderStates.ENTERING_SUBJECT)
    await callback.message.edit_text(
        "📚 *Шаг 1 из 5: Укажите предмет/дисциплину*\n\n"
        "Пример:\n_Математика_\n_Теория вероятностей_\n_Программирование на Python_",
        reply_markup=get_back_kb("back_to_types"),
        parse_mode="Markdown"
    )

@router.message(OrderStates.ENTERING_SUBJECT)
async def enter_subject(message: Message, state: FSMContext):
    subject = message.text
    await state.update_data(subject=subject)
    await state.set_state(OrderStates.ENTERING_DESCRIPTION)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Назад")
    
    await message.answer(
        "📝 *Шаг 2 из 5: Опишите задание подробно*\n\n"
        "Пример:\n_Решить 5 задач по теории вероятностей из учебника Петрова_\n"
        "_Написать курсовую по экономике, 25-30 страниц_",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown"
    )

@router.message(OrderStates.ENTERING_DESCRIPTION)
async def enter_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await state.set_state(OrderStates.ENTERING_DEADLINE)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Назад")
    
    await message.answer(
        "⏰ *Шаг 3 из 5: Укажите срок выполнения*\n\n"
        "Пример:\n_до 20 мая_\n_в течение 3 дней_\n_срочно, сегодня до 18:00_",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown"
    )

@router.message(OrderStates.ENTERING_DEADLINE)
async def enter_deadline(message: Message, state: FSMContext):
    deadline = message.text
    await state.update_data(deadline=deadline)
    await state.set_state(OrderStates.ENTERING_BUDGET)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Назад")
    
    await message.answer(
        "💰 *Шаг 4 из 5: Укажите ваш бюджет*\n\n"
        "Пример:\n_1500 руб_\n_2000 рублей_\n_3000₽_",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown"
    )

@router.message(OrderStates.ENTERING_BUDGET)
async def enter_budget(message: Message, state: FSMContext):
    try:
        budget = int(''.join(filter(str.isdigit, message.text)))
        if budget <= 0:
            raise ValueError
    except (ValueError, TypeError):
        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        builder = ReplyKeyboardBuilder()
        builder.button(text="🔙 Назад")
        
        await message.answer(
            "Пожалуйста, введите корректную сумму (только цифры, больше 0)",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
        return
    
    await state.update_data(budget=budget)
    await state.set_state(OrderStates.UPLOADING_FILE)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пропустить")
    builder.button(text="🔙 Назад")
    
    await message.answer(
        "📎 *Шаг 5 из 5: Прикрепите файл с заданием (если есть)*\n\n"
        "Форматы: PDF, DOCX, TXT\n"
        "Максимальный размер: 5 МБ\n\n"
        "Если файла нет, нажмите 'Пропустить'",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown"
    )

@router.message(OrderStates.UPLOADING_FILE, F.document)
async def handle_file_upload(message: Message, state: FSMContext, bot: Bot):
    from config.settings import UPLOAD_FOLDER, MAX_FILE_SIZE_MB, FILE_TYPES
    from pathlib import Path
    import uuid
    
    file = await bot.get_file(message.document.file_id)
    file_ext = Path(message.document.file_name).suffix.lower()
    
    if file_ext not in FILE_TYPES:
        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        builder = ReplyKeyboardBuilder()
        builder.button(text="Пропустить")
        builder.button(text="🔙 Назад")
        
        await message.answer(
            f"⚠️ Неподдерживаемый формат файла. Разрешены: {', '.join(FILE_TYPES)}",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
        return
    
    if message.document.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        builder = ReplyKeyboardBuilder()
        builder.button(text="Пропустить")
        builder.button(text="🔙 Назад")
        
        await message.answer(
            f"⚠️ Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE_MB} МБ",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
        return
    
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_FOLDER / file_name
    await bot.download_file(file.file_path, destination=file_path)
    
    await state.update_data(file_path=str(file_path))
    await confirm_order(message, state)

@router.message(OrderStates.UPLOADING_FILE, F.text == "Пропустить")
async def skip_file_upload(message: Message, state: FSMContext):
    await confirm_order(message, state)

async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    order_type = data['order_type']
    
    from config.constants import ORDER_TYPES
    emoji, type_display = ORDER_TYPES.get(order_type, ("✏️", "ДРУГОЕ ЗАДАНИЕ"))
    
    confirm_text = (
        f"🔹 *Проверьте данные заказа*\n\n"
        f"{emoji} *Тип работы:* {type_display}\n"
        f"📚 *Предмет:* {data['subject']}\n"
        f"📝 *Описание:*\n{data['description']}\n"
        f"⏰ *Срок:* {data['deadline']}\n"
        f"💰 *Бюджет:* {data['budget']} руб\n\n"
        "Всё верно?"
    )
    
    await state.set_state(OrderStates.CONFIRMING_ORDER)
    await message.answer(
        confirm_text,
        reply_markup=get_order_confirmation_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "final_confirm", OrderStates.CONFIRMING_ORDER)
async def final_confirm_order(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    await callback.answer()
    data = await state.get_data()
    user = callback.from_user
    
    order_data = {
        'type': data['order_type'],
        'subject': data['subject'],
        'description': data['description'],
        'deadline': data['deadline'],
        'budget': data['budget'],
        'file_path': data.get('file_path'),
        'client_id': user.id
    }
    
    order = await order_service.create_order(order_data, user.id)
    if not order:
        from keyboards.common import get_main_menu_kb
        await callback.message.edit_text(
            "⚠️ Не удалось создать заказ. Попробуйте позже.",
            reply_markup=get_main_menu_kb()
        )
        return
    
    from keyboards.order_kb import get_order_created_kb
    emoji, type_display = ORDER_TYPES.get(order.type, ("✏️", "ДРУГОЕ ЗАДАНИЕ"))
    
    await callback.message.edit_text(
        f"✅ *Ваш заказ успешно создан!*\n\n"
        f"{emoji} *Тип:* {type_display}\n"
        f"📚 *Предмет:* {order.subject}\n"
        f"💰 *Бюджет:* {order.budget} руб\n"
        f"⏰ *Срок:* {order.deadline}\n\n"
        f"🆔 *ID:* `{order.order_id}`\n\n"
        "📌 Исполнители уже видят ваш заказ. Ожидайте предложений!",
        reply_markup=get_order_created_kb(order.order_id),
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery, order_service: OrderService):
    await callback.answer()
    order_id = callback.data.split("_")[1]
    executor_id = callback.from_user.id
    
    success = await order_service.accept_order(order_id, executor_id)
    if not success:
        await callback.answer("Не удалось принять заказ", show_alert=True)
        return
    
    await callback.answer("Вы успешно приняли заказ!", show_alert=True)

@router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: CallbackQuery, order_service: OrderService):
    await callback.answer()
    order_id = callback.data.split("_")[1]
    
    success = await order_service.complete_order(order_id)
    if not success:
        await callback.answer("Не удалось завершить заказ", show_alert=True)
        return
    
    await callback.answer("Заказ успешно завершен!", show_alert=True)

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_order(callback: CallbackQuery, order_service: OrderService):
    await callback.answer()
    order_id = callback.data.split("_")[1]
    canceled_by = callback.from_user.id
    
    success = await order_service.cancel_order(order_id, canceled_by)
    if not success:
        await callback.answer("Не удалось отменить заказ", show_alert=True)
        return
    
    await callback.answer("Заказ успешно отменен!", show_alert=True)

@router.callback_query(F.data.startswith("back_to_"))
async def back_to_previous(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    back_to = callback.data.split("_")[-1]
    
    if back_to == "types":
        await state.set_state(OrderStates.SELECTING_ORDER_TYPE)
        await callback.message.edit_text(
            "📌 *Выберите тип работы:*",
            reply_markup=get_order_type_kb(),
            parse_mode="Markdown"
        )
    elif back_to == "subject":
        await state.set_state(OrderStates.ENTERING_SUBJECT)
        await callback.message.edit_text(
            "📚 *Шаг 1 из 5: Укажите предмет/дисциплину*\n\n"
            "Пример:\n_Математика_\n_Теория вероятностей_\n_Программирование на Python_",
            reply_markup=get_back_kb("back_to_types"),
            parse_mode="Markdown"
        )
    elif back_to == "description":
        await state.set_state(OrderStates.ENTERING_DESCRIPTION)
        await callback.message.edit_text(
            "📝 *Шаг 2 из 5: Опишите задание подробно*\n\n"
            "Пример:\n_Решить 5 задач по теории вероятностей из учебника Петрова_\n"
            "_Написать курсовую по экономике, 25-30 страниц_",
            reply_markup=get_back_kb("back_to_subject"),
            parse_mode="Markdown"
        )
    elif back_to == "deadline":
        await state.set_state(OrderStates.ENTERING_DEADLINE)
        await callback.message.edit_text(
            "⏰ *Шаг 3 из 5: Укажите срок выполнения*\n\n"
            "Пример:\n_до 20 мая_\n_в течение 3 дней_\n_срочно, сегодня до 18:00_",
            reply_markup=get_back_kb("back_to_description"),
            parse_mode="Markdown"
        )
    elif back_to == "budget":
        await state.set_state(OrderStates.ENTERING_BUDGET)
        await callback.message.edit_text(
            "💰 *Шаг 4 из 5: Укажите ваш бюджет*\n\n"
            "Пример:\n_1500 руб_\n_2000 рублей_\n_3000₽_",
            reply_markup=get_back_kb("back_to_deadline"),
            parse_mode="Markdown"
        )