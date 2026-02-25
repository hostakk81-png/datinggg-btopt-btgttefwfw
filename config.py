# Конфигурация бота
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'вставьте_ваш_токен_здесь')

# ID группы для жб (пример: -100123456789)
REPORTS_GROUP_ID = int(os.getenv('REPORTS_GROUP_ID', '-100123456789'))

# ID топика в группе (topic_id в группе, 0 если общий чат)
REPORTS_TOPIC_ID = int(os.getenv('REPORTS_TOPIC_ID', '0'))

# ID группы где выдаются наказания (обычная группа)
PUNISHMENTS_GROUP_ID = int(os.getenv('PUNISHMENTS_GROUP_ID', '-100123456789'))

# IDs админов (список)
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else [123456789]

# Опции наказаний
PUNISHMENTS = {
    'mute': 'Мут',
    'kick': 'Кик',
    'ban': 'Бан'
}

# Время мута по умолчанию (минуты)
DEFAULT_MUTE_TIME = 60

# Максимальное время бана (дни)
MAX_BAN_DAYS = 365
