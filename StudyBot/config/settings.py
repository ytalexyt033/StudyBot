from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Настройки бота
TOKEN = "7905009014:AAF2PtwiWkA6sIYLlGrF04JcJPg8oDZA_J4"
ADMIN_CHAT_ID = -1002585261529

# Настройки базы данных
DB_NAME = BASE_DIR / "study_tips_bot.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Лимиты
MAX_ORDERS_PER_USER = 3
MAX_FILE_SIZE_MB = 5
FILE_TYPES = ['.pdf', '.docx', '.doc', '.txt']