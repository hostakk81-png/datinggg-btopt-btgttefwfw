import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import db
from config import ADMIN_IDS
from keyboards import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States для админ-панели
ADD_RULE_ARTICLE, ADD_RULE_DESC, ADD_RULE_PUNISHMENT = range(0, 3)
SELECT_PUNISHMENT_TYPE, SELECT_BAN_DURATION = range(3, 5)
ADD_TEMPLATE_TITLE, ADD_TEMPLATE_TEXT = range(5, 7)

# Хранение временных данных для админа
admin_data_store = {}


# ========== ADMIN MENU ==========
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню админ-панели"""
    query = update.callback_query
    await query.answer()
    
    message = "🛡️ Админ-панель\n\nВыберите действие:"
    
    await query.edit_message_text(
        message,
        reply_markup=get_admin_menu_keyboard()
    )


# ========== ADMIN RULES MENU ==========
async def admin_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления правилами"""
    query = update.callback_query
    await query.answer()
    
    message = "📋 Управление правилами\n\nВыберите действие:"
    
    await query.edit_message_text(
        message,
        reply_markup=get_admin_rules_menu_keyboard()
    )


# ========== ADD RULE START ==========
async def add_rule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления правила"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_data_store[user_id] = {}
    
    message = (
        "📝 Добавление нового правила\n\n"
        "Шаг 1️⃣: Введите номер статьи (например, 'Статья 1' или 'Спам'):"
    )
    
    await query.edit_message_text(message)
    
    return ADD_RULE_ARTICLE


# ========== GET RULE ARTICLE ==========
async def get_rule_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение номера статьи"""
    user_id = update.effective_user.id
    article = update.message.text.strip()
    
    if not article or len(article) < 2:
        await update.message.reply_text("❌ Некорректный номер статьи! Попробуйте снова.")
        return ADD_RULE_ARTICLE
    
    # Проверяем, есть ли уже такая статья
    if db.get_all_rules():
        existing = [r for r in db.get_all_rules() if r['article'].lower() == article.lower()]
        if existing:
            await update.message.reply_text("❌ Статья с таким названием уже существует!")
            return ADD_RULE_ARTICLE
    
    admin_data_store[user_id]['article'] = article
    
    message = (
        "📝 Добавление нового правила\n\n"
        "Шаг 2️⃣: Введите описание правила:"
    )
    
    await update.message.reply_text(message)
    return ADD_RULE_DESC


# ========== GET RULE DESCRIPTION ==========
async def get_rule_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания правила"""
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    if not description or len(description) < 5:
        await update.message.reply_text("❌ Описание слишком короткое! Напишите подробнее (минимум 5 символов).")
        return ADD_RULE_DESC
    
    admin_data_store[user_id]['description'] = description
    
    message = (
        "📝 Добавление нового правила\n\n"
        "Шаг 3️⃣: Выберите тип наказания:"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=get_punishment_type_keyboard()
    )
    
    return SELECT_PUNISHMENT_TYPE


# ========== SELECT PUNISHMENT TYPE FOR RULE ==========
async def select_punishment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа наказания для правила"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    punishment_type = query.data.split('_')[2]  # rule_type_mute -> mute
    
    admin_data_store[user_id]['punishment_type'] = punishment_type
    
    # Если это мут или кик, пропускаем выбор длительности (опционально)
    # Если это бан, спрашиваем длительность
    
    if punishment_type == 'kick':
        # Для кика не нужна длительность
        admin_data_store[user_id]['punishment_duration'] = 'N/A'
        
        # Показываем подтверждение
        data = admin_data_store[user_id]
        message = (
            f"<b>Подтверждение нового правила</b>\n\n"
            f"<b>Статья:</b> {data['article']}\n"
            f"<b>Описание:</b> {data['description']}\n"
            f"<b>Наказание:</b> <b>{punishment_type.upper()}</b>\n\n"
            f"Сохранить правило?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Сохранить", callback_data='confirm_rule_save')],
            [InlineKeyboardButton("❌ Отмена", callback_data='cancel_add_rule')]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    
    elif punishment_type == 'ban':
        message = (
            "📝 Добавление нового правила\n\n"
            "Шаг 4️⃣: Выберите длительность бана:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_ban_duration_keyboard()
        )
        
        return SELECT_BAN_DURATION
    
    elif punishment_type == 'mute':
        message = (
            "📝 Добавление нового правила\n\n"
            "Шаг 4️⃣: Выберите длительность мута:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_mute_duration_keyboard()
        )
        
        return SELECT_BAN_DURATION


# ========== SELECT BAN DURATION ==========
async def select_ban_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор длительности бана/мута"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback = query.data
    
    if callback.startswith('ban_duration_'):
        duration = callback.replace('ban_duration_', '')
    elif callback.startswith('mute_duration_'):
        duration = callback.replace('mute_duration_', '')
    else:
        return
    
    # Конвертируем в понятный вид
    duration_map = {
        '1': '1 день',
        '3': '3 дня',
        '7': '7 дней',
        '30_days': '30 дней',
        'perm': 'Перманентно',
        '30': '30 минут',
        '60': '1 час',
        '180': '3 часа',
        '1440': '1 день',
        'none': 'Без ограничений'
    }
    
    display_duration = duration_map.get(duration, duration)
    admin_data_store[user_id]['punishment_duration'] = display_duration
    
    # Показываем подтверждение
    data = admin_data_store[user_id]
    message = (
        f"<b>Подтверждение нового правила</b>\n\n"
        f"<b>Статья:</b> {data['article']}\n"
        f"<b>Описание:</b> {data['description']}\n"
        f"<b>Наказание:</b> <b>{data['punishment_type'].upper()}</b>\n"
        f"<b>Длительность:</b> {data['punishment_duration']}\n\n"
        f"Сохранить правило?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Сохранить", callback_data='confirm_rule_save')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel_add_rule')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return ConversationHandler.END


# ========== CONFIRM RULE SAVE ==========
async def confirm_rule_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение нового правила"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in admin_data_store:
        await query.edit_message_text("❌ Ошибка! Данные потеряны.")
        return
    
    data = admin_data_store[user_id]
    
    # Сохраняем правило в БД
    rule_id = db.add_rule(
        article=data['article'],
        description=data['description'],
        punishment_type=data['punishment_type'],
        punishment_duration=data['punishment_duration'],
        created_by=user_id
    )
    
    if rule_id:
        await query.edit_message_text(
            f"✅ Правило '{data['article']}' успешно добавлено! (ID: {rule_id})",
            reply_markup=get_admin_rules_menu_keyboard()
        )
        del admin_data_store[user_id]
    else:
        await query.edit_message_text(
            "❌ Ошибка при сохранении правила!",
            reply_markup=get_admin_rules_menu_keyboard()
        )


# ========== CANCEL ADD RULE ==========
async def cancel_add_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления правила"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id in admin_data_store:
        del admin_data_store[user_id]
    
    message = "📋 Управление правилами\n\nВыберите действие:"
    
    await query.edit_message_text(
        message,
        reply_markup=get_admin_rules_menu_keyboard()
    )
    
    return ConversationHandler.END


# ========== VIEW RULES ==========
async def view_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр всех правил"""
    query = update.callback_query
    await query.answer()
    
    rules = db.get_all_rules()
    
    if not rules:
        await query.edit_message_text(
            "❌ Правила не найдены!\n\nДобавьте первое правило.",
            reply_markup=get_admin_rules_menu_keyboard()
        )
        return
    
    message = "<b>📋 Список правил:</b>\n\n"
    
    for rule in rules:
        message += (
            f"<b>ID: {rule['rule_id']}</b>\n"
            f"<b>Статья:</b> {rule['article']}\n"
            f"<b>Наказание:</b> {rule['punishment_type'].upper()}\n"
            f"<b>Длительность:</b> {rule['punishment_duration']}\n"
            f"─────────────────\n"
        )
    
    await query.edit_message_text(
        message,
        reply_markup=get_rules_list_keyboard(rules),
        parse_mode='HTML'
    )


# ========== EDIT RULE ==========
async def edit_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование правила"""
    query = update.callback_query
    await query.answer()
    
    rule_id = int(query.data.split('_')[2])
    rule = db.get_rule(rule_id)
    
    if not rule:
        await query.answer("❌ Правило не найдено!")
        return
    
    message = (
        f"<b>Редактирование правила</b>\n\n"
        f"<b>ID:</b> {rule['rule_id']}\n"
        f"<b>Статья:</b> {rule['article']}\n"
        f"<b>Описание:</b> {rule['description']}\n"
        f"<b>Наказание:</b> {rule['punishment_type'].upper()}\n"
        f"<b>Длительность:</b> {rule['punishment_duration']}\n\n"
        f"Выберите действие:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=get_rule_edit_keyboard(rule_id),
        parse_mode='HTML'
    )


# ========== DELETE RULE ==========
async def delete_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление правила"""
    query = update.callback_query
    await query.answer()
    
    rule_id = int(query.data.split('_')[2])
    rule = db.get_rule(rule_id)
    
    if not rule:
        await query.answer("❌ Правило не найдено!")
        return
    
    message = (
        f"<b>⚠️ Удаление правила</b>\n\n"
        f"<b>Статья:</b> {rule['article']}\n"
        f"<b>Описание:</b> {rule['description']}\n\n"
        f"Вы уверены? Это действие невозможно отменить!"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=get_confirm_delete_keyboard(rule_id),
        parse_mode='HTML'
    )


# ========== CONFIRM DELETE RULE ==========
async def confirm_delete_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления правила"""
    query = update.callback_query
    await query.answer()
    
    rule_id = int(query.data.split('_')[3])
    
    db.delete_rule(rule_id)
    
    await query.edit_message_text(
        "✅ Правило успешно удалено!",
        reply_markup=get_admin_rules_menu_keyboard()
    )


# ========== EDIT RULE DETAILS START ==========
async def edit_rule_details_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало редактирования деталей правила"""
    query = update.callback_query
    await query.answer()
    
    rule_id = int(query.data.split('_')[3])
    user_id = update.effective_user.id
    
    admin_data_store[user_id] = {'rule_id': rule_id}
    
    message = "✏️ Редактирование правила\n\nШаг 1️⃣: Введите новое название статьи:"
    
    await query.edit_message_text(message)
    
    return ADD_RULE_ARTICLE


# ========== REJECTION TEMPLATES ==========
async def view_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр шаблонов отклонения"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Проверка админ статуса
    if not db.is_admin(user_id):
        await query.answer("❌ У вас нет прав доступа!")
        return
    
    templates = db.get_all_templates()
    
    message = "<b>📝 Шаблоны отклонения жалоб</b>\n\n"
    
    if not templates:
        message += "Шаблонов не создано.\n\n"
        keyboard = [
            [InlineKeyboardButton("➕ Добавить шаблон", callback_data='add_template')],
            [InlineKeyboardButton("❌ Назад", callback_data='admin_menu')]
        ]
    else:
        for t in templates:
            message += f"<b>{t['title']}</b>\n"
            message += f"<i>{t['text'][:50]}...</i>\n"
            message += "─────────────────\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить шаблон", callback_data='add_template')],
            [InlineKeyboardButton("❌ Назад", callback_data='admin_menu')]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def add_template_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления шаблона"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_data_store[user_id] = {}
    
    message = "➕ Добавление шаблона\n\n<b>Шаг 1️⃣: Введите название шаблона</b>\n(например: 'Спам', 'Оскорбления')"
    
    await query.edit_message_text(message, parse_mode='HTML')
    
    return ADD_TEMPLATE_TITLE


async def add_template_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия шаблона"""
    user_id = update.effective_user.id
    title = update.message.text.strip()
    
    if not title or len(title) < 2:
        await update.message.reply_text("❌ Название слишком короткое!")
        return ADD_TEMPLATE_TITLE
    
    admin_data_store[user_id]['title'] = title
    
    message = "➕ Добавление шаблона\n\n<b>Шаг 2️⃣: Введите текст ответа</b>\n(это сообщение будет отправлено пользователю при отклонении)"
    
    await update.message.reply_text(message, parse_mode='HTML')
    
    return ADD_TEMPLATE_TEXT


async def add_template_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение текста шаблона"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not text or len(text) < 5:
        await update.message.reply_text("❌ Текст слишком короткий!")
        return ADD_TEMPLATE_TEXT
    
    admin_data_store[user_id]['text'] = text
    
    # Сохраняем шаблон
    template_id = db.add_rejection_template(
        title=admin_data_store[user_id]['title'],
        text=text,
        created_by=user_id
    )
    
    if template_id:
        await update.message.reply_text(
            f"✅ Шаблон '{admin_data_store[user_id]['title']}' успешно добавлен!",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await update.message.reply_text("❌ Ошибка при добавлении шаблона!")
    
    del admin_data_store[user_id]
    return ConversationHandler.END

