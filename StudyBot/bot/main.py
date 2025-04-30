import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from bot.handlers import common, order_handlers, dispute_handlers
from config.settings import TOKEN
from handlers import common, order_handlers, dispute_handlers
from middlewares.user_middleware import UserMiddleware
from services.database import Database
import sys
from pathlib import Path

# Добавляем корень проекта в путь поиска модулей
sys.path.append(str(Path(__file__).parent.parent.parent))

from bot.handlers import common, order_handlers, dispute_handlers
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    db = Database()
    
    # Регистрация middleware
    dp.update.middleware(UserMiddleware(db))
    dp.callback_query.middleware(CallbackAnswerMiddleware())
    
    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(order_handlers.router)
    dp.include_router(dispute_handlers.router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())