import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError
from telegram.constants import ChatMemberStatus

from database import db
from config import ADMIN_IDS, REPORTS_GROUP_ID, REPORTS_TOPIC_ID, PUNISHMENTS_GROUP_ID
from keyboards import get_punishment_keyboard, get_rules_keyboard, get_confirm_punishment_keyboard, \
    get_admin_menu_keyboard, get_submit_report_keyboard, get_start_keyboard, \
    get_mute_duration_keyboard, get_ban_duration_keyboard, \
    get_punished_users_keyboard, get_remove_punishment_keyboard, get_back_button

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States для ConversationHandler
AGAINST_USERNAME, AGAINST_USER_ID, VIOLATION_LINK, DESCRIPTION, SUBMIT_REPORT = range(5)
CUSTOM_MUTE_TIME, CUSTOM_BAN_TIME = range(5, 7)
ADD_RULE_ARTICLE, ADD_RULE_DESC, ADD_RULE_PUNISHMENT = range(5, 8)
CHOOSE_RULE_TYPE, CHOOSE_BAN_DURATION = range(8, 10)
EDIT_RULE_STEP = range(10, 11)

# Хранение данных для форм
user_data_store = {}


# ========== START COMMAND ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    message_text = (
        f"🎎 Привет, {user.first_name}!\n\n"
        "Я создан для подачи жалоб на нарушителей! 📋\n\n"
        "Нажмите кнопку ниже, чтобы подать жалобу на пользователя."
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_start_keyboard()
    )


# ========== ADMIN COMMAND ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    # Проверка, является ли пользователь админом
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав доступа к админ-панели!")
        return
    
    message_text = "🛡️ Админ-панель\n\nВыберите действие:"
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_admin_menu_keyboard()
    )


# ========== REPORT START ==========
async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса подачи жалобы"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data_store[user_id] = {}
    
    message_text = (
        "📝 Подача жалобы\n\n"
        "Шаг 1️⃣: Введите username пользователя, на которого вы подаёте жалобу"
        " (без @):"
    )
    
    await query.edit_message_text(message_text)
    
    return AGAINST_USERNAME


# ========== GET AGAINST USERNAME ==========
async def get_against_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение username нарушителя"""
    user_id = update.effective_user.id
    username = update.message.text.replace('@', '').strip()
    
    if not username or len(username) < 3:
        await update.message.reply_text("❌ Некорректный username! Попробуйте снова.")
        return AGAINST_USERNAME
    
    user_data_store[user_id]['against_username'] = username
    
    message_text = (
        "📝 Подача жалобы\n\n"
        "Шаг 2️⃣: Введите ID пользователя (получите через @username_to_id_bot):"
    )
    
    await update.message.reply_text(message_text)
    return AGAINST_USER_ID


# ========== GET AGAINST USER ID ==========
async def get_against_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ID нарушителя"""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    
    if not user_input.isdigit():
        await update.message.reply_text("❌ ID должно быть числом! Попробуйте снова.")
        return AGAINST_USER_ID
    
    against_user_id = int(user_input)
    user_data_store[user_id]['against_user_id'] = against_user_id
    
    message_text = (
        "📝 Подача жалобы\n\n"
        "Шаг 3️⃣: Отправьте ссылку на сообщение/пост нарушителя или напишите 'нет' если ссылки нет:"
    )
    
    await update.message.reply_text(message_text)
    return VIOLATION_LINK


# ========== GET VIOLATION LINK ==========
async def get_violation_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ссылки на нарушение"""
    user_id = update.effective_user.id
    link = update.message.text.strip()
    
    if link.lower() == 'нет':
        link = 'Ссылка не предоставлена'
    
    user_data_store[user_id]['violation_link'] = link
    
    message_text = (
        "📝 Подача жалобы\n\n"
        "Шаг 4️⃣: Опишите нарушение (что сделал пользователь):"
    )
    
    await update.message.reply_text(message_text)
    return DESCRIPTION


# ========== GET DESCRIPTION ==========
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания нарушения"""
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    if not description or len(description) < 5:
        await update.message.reply_text("❌ Описание слишком короткое! Напишите подробнее.")
        return DESCRIPTION
    
    user_data_store[user_id]['description'] = description
    
    # Показываем подтверждение
    data = user_data_store[user_id]
    message_text = (
        "📝 Подтверждение жалобы\n\n"
        f"<b>На кого:</b> @{data['against_username']} (ID: {data['against_user_id']})\n"
        f"<b>Ссылка:</b> {data['violation_link']}\n"
        f"<b>Описание:</b> {data['description']}\n\n"
        "Проверьте информацию и нажмите 'Отправить жалобу':"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_submit_report_keyboard(),
        parse_mode='HTML'
    )
    
    return SUBMIT_REPORT


# ========== SUBMIT REPORT ==========
async def submit_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправка жалобы в группу"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = update.effective_user
    
    if user_id not in user_data_store:
        await query.edit_message_text("❌ Данные потеряны. Начните заново с /start")
        return ConversationHandler.END
    
    data = user_data_store[user_id]
    
    # Создаём жалобу в БД
    report_id = db.create_report(
        from_user_id=user_id,
        from_username=user.username or f"ID {user_id}",
        against_user_id=data['against_user_id'],
        against_username=data['against_username'],
        violation_link=data['violation_link'],
        description=data['description']
    )
    
    if not report_id:
        await query.edit_message_text("❌ Ошибка при создании жалобы!")
        del user_data_store[user_id]
        return ConversationHandler.END
    
    # Форматируем сообщение для группы
    from_username = user.username or f"ID {user_id}"
    report_text = (
        f"<b>📋 НОВАЯ ЖАЛОБА #{report_id}</b>\n\n"
        f"<b>От кого:</b> @{from_username}\n"
        f"<b>На кого:</b> @{data['against_username']}\n"
        f"<b>Ссылка на нарушение:</b> {data['violation_link']}\n"
        f"<b>Описание:</b> <i>{data['description']}</i>\n\n"
        f"<b>Статус:</b> 🟡 Открыта"
    )
    
    try:
        # Отправляем в группу/топик
        message = await context.bot.send_message(
            chat_id=REPORTS_GROUP_ID,
            text=report_text,
            reply_markup=get_punishment_keyboard(report_id),
            parse_mode='HTML',
            message_thread_id=REPORTS_TOPIC_ID if REPORTS_TOPIC_ID != 0 else None
        )
        
        # Сохраняем ID сообщения в БД
        db.update_report_message(
            report_id=report_id,
            message_id=message.message_id,
            chat_id=REPORTS_GROUP_ID,
            topic_id=REPORTS_TOPIC_ID
        )
    except TelegramError as e:
        logger.error(f"Ошибка при отправке жалобы в группу: {e}")
        await query.edit_message_text(
            "❌ Ошибка при отправке жалобы в группу. Проверьте конфигурацию."
        )
        del user_data_store[user_id]
        return ConversationHandler.END
    
    # Подтверждение пользователю
    await query.edit_message_text(
        f"✅ Жалоба #{report_id} успешно отправлена!\n\n"
        f"Администраторы разберут вашу жалобу в ближайшее время."
    )
    
    del user_data_store[user_id]
    return ConversationHandler.END


# ========== CANCEL REPORT ==========
async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена подачи жалобы"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    await query.edit_message_text(
        "❌ Подача жалобы отменена.\n\n"
        "Используйте /start для повторной попытки."
    )
    
    return ConversationHandler.END


# ========== APPLY PUNISHMENTS FUNCTIONS ==========

async def apply_mute(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, duration: str):
    """Применение мута (ограничение прав)"""
    if not user_id:
        logger.warning(f"Невозможно применить мут: user_id не найден")
        return
    
    try:
        # Парсим длительность
        mute_minutes = parse_duration(duration)
        logger.info(f"Парсинг длительности: '{duration}' → {mute_minutes} минут")
        
        if mute_minutes:
            until_date = int((datetime.now() + timedelta(minutes=mute_minutes)).timestamp())
        else:
            until_date = None
        
        logger.info(f"Применение мута: user_id={user_id}, chat_id={chat_id}, until_date={until_date}")
        
        # Применяем ограничение прав (мут)
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        logger.info(f"✅ Мут применён пользователю {user_id} в группе {chat_id}")
    except TelegramError as e:
        logger.error(f"Ошибка при применении мута: {e}")


async def apply_kick(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """Применение кика (исключение из группы)"""
    if not user_id:
        logger.warning(f"Невозможно применить кик: user_id не найден")
        return
    
    try:
        # Исключаем пользователя из группы
        await context.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            revoke_messages=False
        )
        
        # Разбаниваем, чтобы пользователь мог заново войти (это кик, не бан)
        await context.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=False
        )
        logger.info(f"✅ Кик применён пользователю {user_id} в группе {chat_id}")
    except TelegramError as e:
        logger.error(f"Ошибка при применении кика: {e}")


async def apply_ban(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, duration: str):
    """Применение бана (блокировка)"""
    if not user_id:
        logger.warning(f"Невозможно применить бан: user_id не найден")
        return
    
    try:
        # Парсим длительность
        ban_days = parse_ban_duration(duration)
        logger.info(f"Парсинг длительности бана: '{duration}' → {ban_days} дней")
        
        if ban_days:
            until_date = int((datetime.now() + timedelta(days=ban_days)).timestamp())
        else:
            until_date = None  # Перманентный бан
        
        logger.info(f"Применение бана: user_id={user_id}, chat_id={chat_id}, until_date={until_date}")
        
        # Применяем бан
        await context.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            revoke_messages=True,
            until_date=until_date
        )
        logger.info(f"✅ Бан применён пользователю {user_id} в группе {chat_id}")
    except TelegramError as e:
        logger.error(f"Ошибка при применении бана: {e}")


async def send_punishment_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int, rule, punishment_type: str, violation_link: str = None):
    """Отправка уведомления о наказании в ЛС"""
    if not user_id:
        return
    
    try:
        message = (
            f"<b>⚠️ Вам Выдано Наказание</b>\n\n"
            f"<b>📋 Статья:</b> <code>{rule['article']}</code>\n\n"
            f"<b>📝 Описание нарушения:</b>\n"
            f"{rule['description']}\n\n"
            f"<b>⚡ Тип наказания:</b> <b>{punishment_type.upper()}</b>"
        )
        
        if rule['punishment_duration'] and rule['punishment_duration'] != 'N/A':
            message += f"\n<b>⏱️ Длительность:</b> {rule['punishment_duration']}"
        
        if violation_link and violation_link != 'Ссылка не предоставлена':
            message += f"\n\n<b>🔗 Ссылка на нарушение:</b>\n{violation_link}"
        
        message += (
            f"\n\n<i>Если вы считаете, что это несправедливо, нажмите кнопку ниже для обжалования.</i>"
        )
        
        # Создаём клавиатуру с кнопкой для обжалования
        keyboard = [
            [InlineKeyboardButton("📢 Обжаловать наказание", url="https://t.me/nolyktg")]
        ]
        
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"✅ Уведомление о наказании отправлено пользователю {user_id}")
    except TelegramError as e:
        logger.warning(f"Не удалось отправить ЛС пользователю {user_id}: {e}")


def parse_duration(duration_str: str) -> int:
    """Парсит строку длительности мута в минуты"""
    if not duration_str or duration_str == 'N/A':
        return None
    
    duration_str = duration_str.lower().strip()
    
    # 30 минут / 30 мин
    if '30' in duration_str and ('мин' in duration_str or 'sec' in duration_str):
        return 30
    # 1 час
    elif '1' in duration_str and 'час' in duration_str:
        return 60
    # 3 часа
    elif ('3' in duration_str or 'три' in duration_str) and 'часа' in duration_str:
        return 180
    # 1 день
    elif '1' in duration_str and 'день' in duration_str:
        return 1440
    # Без ограничений
    elif 'без' in duration_str or 'none' in duration_str:
        return None
    else:
        try:
            return int(duration_str) * 60
        except:
            logger.warning(f"Не удалось спарсить длительность: {duration_str}")
            return None


def parse_ban_duration(duration_str: str) -> int:
    """Парсит строку длительности бана в дни"""
    if not duration_str:
        return None
    
    duration_str = duration_str.lower().strip()
    
    # Перма / перманентно / навсегда
    if 'перм' in duration_str or 'вечно' in duration_str or 'навсегда' in duration_str:
        return None  # Перманентный бан
    # 1 день
    elif '1' in duration_str and 'день' in duration_str:
        return 1
    # 3 дня
    elif ('3' in duration_str or 'три' in duration_str) and 'дня' in duration_str:
        return 3
    # 7 дней
    elif ('7' in duration_str or 'семь' in duration_str) and 'дней' in duration_str:
        return 7
    # 30 дней
    elif ('30' in duration_str or 'тридцать' in duration_str) and 'дней' in duration_str:
        return 30
    # 365 дней / год
    elif ('365' in duration_str or 'год' in duration_str):
        return 365
    else:
        try:
            return int(duration_str)
        except:
            logger.warning(f"Не удалось спарсить длительность бана: {duration_str}")
            return None


# ========== PUNISHMENT SELECTION ==========
async def select_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа наказания"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем report_id из callback_data
    callback_data = query.data
    
    if callback_data.startswith('punishment_'):
        punishment_type = callback_data.split('_')[1]
        report_id = int(callback_data.split('_')[2])
        
        # Получаем все правила
        rules = db.get_all_rules()
        
        if not rules:
            await query.answer("❌ Нет добавленных правил!")
            return
        
        # Фильтруем правила по типу наказания
        filtered_rules = [r for r in rules if r['punishment_type'] == punishment_type]
        
        if not filtered_rules:
            await query.answer(f"❌ Нет правил для '{punishment_type}'!")
            return
        
        message = (
            f"<b>Выберите статью для {punishment_type}:</b>\n\n"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_rules_keyboard(filtered_rules, report_id, punishment_type),
            parse_mode='HTML'
        )


# ========== SELECT RULE FOR PUNISHMENT ==========
async def select_rule_for_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение выбранного правила"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback
    parts = query.data.split('_')
    punishment_type = parts[1]
    report_id = int(parts[2])
    rule_id = int(parts[3])
    
    # Получаем правило
    rule = db.get_rule(rule_id)
    
    if not rule:
        await query.answer("❌ Правило не найдено!")
        return
    
    # Получаем отчёт
    report = db.get_report(report_id)
    
    message = (
        f"<b>Подтверждение наказания</b>\n\n"
        f"<b>На кого:</b> @{report['against_username']}\n"
        f"<b>Статья:</b> {rule['article']}\n"
        f"<b>Описание:</b> {rule['description']}\n"
        f"<b>Наказание:</b> <b>{rule['punishment_type'].upper()}</b>"
    )
    
    if rule['punishment_duration']:
        message += f"\n<b>Длительность:</b> {rule['punishment_duration']}"
    
    message += "\n\nПодтвердить применение наказания?"
    
    await query.edit_message_text(
        message,
        reply_markup=get_confirm_punishment_keyboard(report_id, punishment_type, rule_id),
        parse_mode='HTML'
    )


# ========== CONFIRM PUNISHMENT ==========
async def confirm_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Применение наказания"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback
    parts = query.data.split('_')
    punishment_type = parts[1]
    report_id = int(parts[2])
    rule_id = int(parts[3])
    
    # Получаем данные
    report = db.get_report(report_id)
    rule = db.get_rule(rule_id)
    
    if not report or not rule:
        await query.answer("❌ Ошибка при получении данных!")
        return
    
    against_user_id = report['against_user_id'] if 'against_user_id' in dict(report) else None
    against_username = report['against_username']
    
    # Создаём наказание в БД
    punishment_id = db.add_punishment(
        report_id=report_id,
        user_id=against_user_id,
        username=against_username,
        rule_id=rule_id,
        punishment_type=punishment_type,
        punishment_duration=rule['punishment_duration'],
        applied_by=query.from_user.id
    )
    
    # Обновляем статус жалобы
    db.update_report_status(report_id, 'closed')
    
    # Применяем наказание в группе для наказаний
    try:
        if punishment_type == 'mute':
            await apply_mute(context, against_user_id, PUNISHMENTS_GROUP_ID, rule['punishment_duration'])
        elif punishment_type == 'kick':
            await apply_kick(context, against_user_id, PUNISHMENTS_GROUP_ID)
        elif punishment_type == 'ban':
            await apply_ban(context, against_user_id, PUNISHMENTS_GROUP_ID, rule['punishment_duration'])
    except TelegramError as e:
        logger.error(f"Ошибка при применении наказания в группе: {e}")
    
    # Пытаемся отправить ЛС пользователю
    try:
        await send_punishment_notification(context, against_user_id, rule, punishment_type, report['violation_link'])
    except TelegramError as e:
        logger.warning(f"Не удалось отправить ЛС пользователю: {e}")
    
    # Отправляем подтверждающее сообщение админу
    try:
        admin_name = query.from_user.first_name or f"ID {query.from_user.id}"
        confirm_msg = (
            f"✅ <b>Наказание применено</b>\n\n"
            f"<b>Пользователь:</b> @{against_username} (ID: {against_user_id})\n"
            f"<b>Тип наказания:</b> {punishment_type.upper()}\n"
            f"<b>Статья:</b> {rule['article']}"
        )
        if rule['punishment_duration']:
            confirm_msg += f"\n<b>Длительность:</b> {rule['punishment_duration']}"
        await query.edit_message_text(confirm_msg, parse_mode='HTML')
    except:
        pass
    
    # Формируем уведомление
    notification = (
        f"<b>⚠️ Вам выдано наказание</b>\n\n"
        f"<b>Статья:</b> {rule['article']}\n"
        f"<b>Описание:</b> {rule['description']}\n"
        f"<b>Наказание:</b> <b>{punishment_type.upper()}</b>"
    )
    
    if rule['punishment_duration']:
        notification += f"\n<b>Длительность:</b> {rule['punishment_duration']}"
    
    notification += (
        f"\n\n<i>Если вы считаете, что это несправедливо, обратитесь к администраторам.</i>"
    )
    
    # Обновляем сообщение в группе
    closed_text = (
        f"<b>📋 ЖАЛОБА #{report_id}</b>\n\n"
        f"<b>От кого:</b> @{report['from_username']}\n"
        f"<b>На кого:</b> @{against_username}\n"
        f"<b>Ссылка на нарушение:</b> {report['violation_link']}\n"
        f"<b>Описание:</b> <i>{report['description']}</i>\n\n"
        f"<b>Статус:</b> ✅ Закрыта\n\n"
        f"<b>Применённое наказание:</b>\n"
        f"<b>Статья:</b> {rule['article']}\n"
        f"<b>Тип:</b> {punishment_type.upper()}"
    )
    
    if rule['punishment_duration']:
        closed_text += f"\n<b>Длительность:</b> {rule['punishment_duration']}"
    
    try:
        # Удаляем сообщение жалобы из группы
        await context.bot.delete_message(
            chat_id=report['chat_id'],
            message_id=report['message_id']
        )
        logger.info(f"✅ Сообщение жалобы #{report_id} удалено из группы")
    except TelegramError as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    await query.edit_message_text(
        "✅ Наказание применено!",
        parse_mode='HTML'
    )


# ========== CANCEL PUNISHMENT ==========
async def cancel_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена процесса наказания"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    report_id = int(parts[2])
    
    report = db.get_report(report_id)
    
    report_text = (
        f"<b>📋 ЖАЛОБА #{report_id}</b>\n\n"
        f"<b>От кого:</b> @{report['from_username']}\n"
        f"<b>На кого:</b> @{report['against_username']}\n"
        f"<b>Ссылка на нарушение:</b> {report['violation_link']}\n"
        f"<b>Описание:</b> <i>{report['description']}</i>\n\n"
        f"<b>Статус:</b> 🟡 Открыта"
    )
    
    await query.edit_message_text(
        report_text,
        reply_markup=get_punishment_keyboard(report_id),
        parse_mode='HTML'
    )


# ========== CUSTOM DURATION HANDLERS ==========

async def handle_custom_mute_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кастомного ввода времени для мута"""
    user_input = update.message.text.strip()
    
    if not user_input.isdigit():
        await update.message.reply_text("❌ Введите число (количество минут)!")
        return CUSTOM_MUTE_TIME
    
    minutes = int(user_input)
    if minutes < 1 or minutes > 40320:  # Макс 28 дней
        await update.message.reply_text("❌ Введите время от 1 до 40320 минут!")
        return CUSTOM_MUTE_TIME
    
    context.user_data['custom_mute_duration'] = f"{minutes} минут"
    await update.message.reply_text(f"✅ Установлено: {minutes} минут мута")
    return ConversationHandler.END


async def update_message_to_custom_mute_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к запросу кастомного времени мута"""
    query = update.callback_query
    await query.answer()
    
    message = "✏️ Введите количество минут для мута (от 1 до 40320):"
    await query.edit_message_text(message)
    return CUSTOM_MUTE_TIME


async def handle_custom_ban_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кастомного ввода времени для бана"""
    user_input = update.message.text.strip()
    
    if not user_input.isdigit():
        await update.message.reply_text("❌ Введите число (количество дней)!")
        return CUSTOM_BAN_TIME
    
    days = int(user_input)
    if days < 1 or days > 365:
        await update.message.reply_text("❌ Введите время от 1 до 365 дней!")
        return CUSTOM_BAN_TIME
    
    context.user_data['custom_ban_duration'] = f"{days} дней"
    await update.message.reply_text(f"✅ Установлено: {days} дней бана")
    return ConversationHandler.END


async def update_message_to_custom_ban_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к запросу кастомного времени бана"""
    query = update.callback_query
    await query.answer()
    
    message = "✏️ Введите количество дней для бана (от 1 до 365):"
    await query.edit_message_text(message)
    return CUSTOM_BAN_TIME


# ========== VIEW PUNISHED USERS ==========

async def view_punished_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр наказанных пользователей с статусом активности"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Проверка админ статуса
    if not db.is_admin(user_id):
        await query.answer("❌ У вас нет прав доступа!")
        return
    
    # Получим все наказания с информацией об активности
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, 
               CASE 
                   WHEN p.punishment_type = 'mute' AND EXISTS (
                       SELECT 1 FROM active_mutes WHERE punishment_id = p.punishment_id AND expires_at > datetime('now')
                   ) THEN 'АКТИВНО'
                   WHEN p.punishment_type = 'ban' AND p.applied_date > datetime('now', '-30 days') THEN 'АКТИВНО'
                   ELSE 'НЕАКТИВНО'
               END as status
        FROM punishments p
        ORDER BY 
            CASE WHEN status = 'АКТИВНО' THEN 0 ELSE 1 END,
            p.applied_date DESC
    ''')
    punishments = cursor.fetchall()
    conn.close()
    
    if not punishments:
        await query.edit_message_text(
            "✅ Нет наказанных пользователей",
            reply_markup=get_back_button('admin_menu')
        )
        return
    
    # Разделяем на активные и неактивные
    active = [p for p in punishments if dict(p).get('status') == 'АКТИВНО']
    inactive = [p for p in punishments if dict(p).get('status') == 'НЕАКТИВНО']
    
    message = f"<b>🚨 Наказанные пользователи ({len(punishments)} всего)</b>\n\n"
    
    if active:
        message += f"<b>✅ АКТИВНЫЕ ({len(active)}):</b>\n"
        for p in active:
            message += (
                f"🔴 @{p['username']} (ID: {p['user_id']})\n"
                f"   └─ {p['punishment_type'].upper()} | {p['applied_date']}\n"
            )
        message += "\n"
    
    if inactive:
        message += f"<b>⬜ НЕАКТИВНЫЕ ({len(inactive)}):</b>\n"
        for p in inactive:
            message += (
                f"⚪ @{p['username']} (ID: {p['user_id']})\n"
                f"   └─ {p['punishment_type'].upper()} | {p['applied_date']}\n"
            )
    
    await query.edit_message_text(
        message,
        reply_markup=get_punished_users_keyboard(punishments),
        parse_mode='HTML'
    )


async def view_punishment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр деталей наказания"""
    query = update.callback_query
    await query.answer()
    
    punishment_id = int(query.data.split('_')[2])
    punishment = db.get_punishment(punishment_id)
    
    if not punishment:
        await query.answer("❌ Наказание не найдено!")
        return
    
    rule = db.get_rule(punishment['rule_id']) if punishment['rule_id'] else None
    
    message = (
        f"<b>🚨 Деталь наказания</b>\n\n"
        f"<b>ID наказания:</b> {punishment['punishment_id']}\n"
        f"<b>Пользователь:</b> {punishment['username']} (ID: {punishment['user_id']})\n"
        f"<b>Тип:</b> {punishment['punishment_type'].upper()}\n"
    )
    
    if rule:
        message += f"<b>Статья:</b> {rule['article']}\n"
    
    if punishment['punishment_duration']:
        message += f"<b>Длительность:</b> {punishment['punishment_duration']}\n"
    
    message += f"<b>Дата:</b> {punishment['applied_date']}\n"
    
    await query.edit_message_text(
        message,
        reply_markup=get_remove_punishment_keyboard(punishment_id),
        parse_mode='HTML'
    )


async def remove_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снятие наказания и удаление из БД"""
    query = update.callback_query
    await query.answer()
    
    punishment_id = int(query.data.split('_')[2])
    punishment = db.get_punishment(punishment_id)
    
    if not punishment:
        await query.answer("❌ Наказание не найдено!")
        return
    
    user_id = punishment['user_id']
    chat_id = PUNISHMENTS_GROUP_ID
    punishment_type = punishment['punishment_type']
    username = punishment['username']
    
    try:
        # Снимаем наказание в группе
        if punishment_type == 'mute':
            # Разрешаем писать сообщения
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            logger.info(f"✅ Мут снят для пользователя {user_id}")
        
        elif punishment_type == 'ban':
            # Разбаниваем
            await context.bot.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            logger.info(f"✅ Бан снят для пользователя {user_id}")
        
        # Отправляем уведомление пользователю
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ <b>Ваше наказание было отменено!</b>\n\nВы можете вернуться в группу.",
                parse_mode='HTML'
            )
        except:
            logger.warning(f"Не удалось отправить ЛС пользователю {user_id}")
        
        # УДАЛЯЕМ наказание из БД
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Удаляем связанные мьюты
        cursor.execute('DELETE FROM active_mutes WHERE punishment_id = ?', (punishment_id,))
        
        # Удаляем само наказание
        cursor.execute('DELETE FROM punishments WHERE punishment_id = ?', (punishment_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Наказание #{punishment_id} удалено из БД")
        
        await query.edit_message_text(
            f"✅ Наказание #{punishment_id} для @{username} успешно снято и удалено!",
            reply_markup=get_back_button('view_punished_users')
        )
    
    except TelegramError as e:
        logger.error(f"Ошибка при снятии наказания: {e}")
        await query.edit_message_text(
            f"❌ Ошибка при снятии наказания: {e}",
            reply_markup=get_back_button('view_punished_users')
        )


# ========== REJECT REPORT ==========
async def reject_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклонение жалобы и выбор шаблона ответа"""
    query = update.callback_query
    await query.answer()
    
    report_id = int(query.data.split('_')[2])
    
    # Проверяем админ статус
    if not db.is_admin(update.effective_user.id):
        await query.answer("❌ У вас нет прав доступа!")
        return
    
    # Получаем шаблоны и показываем их
    from keyboards import get_rejection_templates_keyboard
    
    templates = db.get_all_templates()
    
    if not templates:
        await query.edit_message_text(
            "❌ Нет созданных шаблонов ответов!\n\n"
            "Сначала создайте шаблоны в админ-панели.",
            reply_markup=get_back_button('admin_menu')
        )
        return
    
    message = f"<b>📝 Выберите шаблон ответа для отклонения жалобы #{report_id}</b>\n\n"
    
    await query.edit_message_text(
        message,
        reply_markup=get_rejection_templates_keyboard(report_id),
        parse_mode='HTML'
    )


async def reject_with_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклонение жалобы с отправкой ответа по шаблону"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    report_id = int(parts[3])
    template_id = int(parts[4])
    
    # Получаем жалобу и шаблон
    report = db.get_report(report_id)
    template = db.get_template(template_id)
    
    if not report or not template:
        await query.answer("❌ Жалоба или шаблон не найдены!", show_alert=True)
        return
    
    from_user_id = report['from_user_id']
    
    try:
        # Отправляем ответ по шаблону автору жалобы
        await context.bot.send_message(
            chat_id=from_user_id,
            text=f"<b>📋 Ответ на вашу жалобу #{report_id}</b>\n\n"
                 f"<b>{template['title']}</b>\n\n"
                 f"{template['text']}",
            parse_mode='HTML'
        )
        logger.info(f"✅ Ответ по шаблону '{template['title']}' отправлен пользователю {from_user_id}")
    except TelegramError as e:
        logger.warning(f"Не удалось отправить ответ пользователю {from_user_id}: {e}")
    
    # Обновляем статус жалобы на "отклонена"
    db.update_report_status(report_id, 'rejected')
    
    # Удаляем сообщение жалобы из группы
    try:
        if report['message_id'] and report['chat_id']:
            await context.bot.delete_message(
                chat_id=report['chat_id'],
                message_id=report['message_id']
            )
            logger.info(f"✅ Сообщение отклоненной жалобы #{report_id} удалено из группы")
    except TelegramError as e:
        logger.warning(f"Не удалось удалить сообщение жалобы в группе: {e}")
    
    await query.edit_message_text(
        f"✅ Жалоба #{report_id} отклонена.\n"
        f"Пользователю отправлен ответ: <b>{template['title']}</b>",
        parse_mode='HTML',
        reply_markup=get_back_button('admin_menu')
    )
