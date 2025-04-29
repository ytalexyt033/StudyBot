import logging
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from telegram.ext import Application
from config import TOKEN, DB_NAME
from bot.services.database import Database
from bot.services.order_manager import OrderManager
from bot.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Инициализация БД и менеджеров
    db = Database(DB_NAME)
    application.bot_data['db'] = db
    application.bot_data['order_manager'] = OrderManager(application, db)
    
    # Регистрация обработчиков
    register_handlers(application)
    
    application.run_polling()

if __name__ == "__main__":
    main()