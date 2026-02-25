from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ========== START KEYBOARD ==========
def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Подать жалобу", callback_data='start_report')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== REPORT SUBMIT KEYBOARD ==========
def get_submit_report_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Отправить жалобу", callback_data='submit_report')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel_report')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== PUNISHMENT KEYBOARD ==========
def get_punishment_keyboard(report_id):
    keyboard = [
        [InlineKeyboardButton("🔇 Мут", callback_data=f'punishment_mute_{report_id}'),
         InlineKeyboardButton("👉 Кик", callback_data=f'punishment_kick_{report_id}'),
         InlineKeyboardButton("🚫 Бан", callback_data=f'punishment_ban_{report_id}')],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_report_{report_id}')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== RULES SELECTION KEYBOARD ==========
def get_rules_keyboard(rules, report_id, punishment_type):
    """Форматирование правил в inline кнопки"""
    keyboard = []
    for rule in rules:
        article = rule['article'] if isinstance(rule, dict) else rule[1]
        rule_id = rule['rule_id'] if isinstance(rule, dict) else rule[0]
        keyboard.append([
            InlineKeyboardButton(
                f"📄 {article}",
                callback_data=f'rule_{punishment_type}_{report_id}_{rule_id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_punishment_{report_id}')])
    return InlineKeyboardMarkup(keyboard)


# ========== CONFIRM PUNISHMENT KEYBOARD ==========
def get_confirm_punishment_keyboard(report_id, punishment_type, rule_id):
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f'confirm_{punishment_type}_{report_id}_{rule_id}')],
        [InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_punishment_{report_id}')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== ADMIN MENU KEYBOARD ==========
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Правила", callback_data='admin_rules')],
        [InlineKeyboardButton("🚨 Наказания", callback_data='view_punished_users')],
        [InlineKeyboardButton("📝 Шаблоны ответов", callback_data='view_templates')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== ADMIN RULES MENU KEYBOARD ==========
def get_admin_rules_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить правило", callback_data='add_rule')],
        [InlineKeyboardButton("📖 Просмотреть правила", callback_data='view_rules')],
        [InlineKeyboardButton("❌ Назад", callback_data='admin_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== PUNISHMENT TYPE KEYBOARD (for adding rule) ==========
def get_punishment_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔇 Мут", callback_data='rule_type_mute')],
        [InlineKeyboardButton("👉 Кик", callback_data='rule_type_kick')],
        [InlineKeyboardButton("🚫 Бан", callback_data='rule_type_ban')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== BAN DURATION KEYBOARD ==========
def get_ban_duration_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("1 день", callback_data='ban_duration_1'),
            InlineKeyboardButton("3 дня", callback_data='ban_duration_3'),
            InlineKeyboardButton("7 дней", callback_data='ban_duration_7')
        ],
        [
            InlineKeyboardButton("30 дней", callback_data='ban_duration_30'),
            InlineKeyboardButton("Перма", callback_data='ban_duration_perm')
        ],
        [
            InlineKeyboardButton("✏️ Своё время (дней)", callback_data='ban_duration_custom')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== RULES LIST KEYBOARD ==========
def get_rules_list_keyboard(rules):
    keyboard = []
    for rule in rules:
        rule_id = rule['rule_id'] if isinstance(rule, dict) else rule[0]
        article = rule['article'] if isinstance(rule, dict) else rule[1]
        keyboard.append([
            InlineKeyboardButton(
                f"📄 {article}",
                callback_data=f'edit_rule_{rule_id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Назад", callback_data='admin_rules')])
    return InlineKeyboardMarkup(keyboard)


# ========== RULE EDIT KEYBOARD ==========
def get_rule_edit_keyboard(rule_id):
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить", callback_data=f'edit_rule_details_{rule_id}')],
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_rule_{rule_id}')],
        [InlineKeyboardButton("❌ Назад", callback_data='view_rules')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== CONFIRM DELETE RULE KEYBOARD ==========
def get_confirm_delete_keyboard(rule_id):
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f'confirm_delete_rule_{rule_id}')],
        [InlineKeyboardButton("❌ Отмена", callback_data=f'edit_rule_{rule_id}')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== MUTE DURATION KEYBOARD ==========
def get_mute_duration_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("30 мин", callback_data='mute_duration_30'),
            InlineKeyboardButton("1 час", callback_data='mute_duration_60'),
            InlineKeyboardButton("3 часа", callback_data='mute_duration_180')
        ],
        [
            InlineKeyboardButton("1 день", callback_data='mute_duration_1440'),
            InlineKeyboardButton("Без ограничений", callback_data='mute_duration_none')
        ],
        [
            InlineKeyboardButton("✏️ Своё время (минут)", callback_data='mute_duration_custom')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== BACK BUTTON ==========
def get_back_button(callback):
    keyboard = [[InlineKeyboardButton("❌ Назад", callback_data=callback)]]
    return InlineKeyboardMarkup(keyboard)


# ========== ADMIN PUNISHMENTS MENU ==========
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Правила", callback_data='admin_rules')],
        [InlineKeyboardButton("🚨 Наказанные пользователи", callback_data='view_punished_users')],
        [InlineKeyboardButton("📝 Шаблоны ответов", callback_data='view_templates')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== PUNISHED USERS LIST ==========
def get_punished_users_keyboard(punishments):
    keyboard = []
    for punishment in punishments:
        user_id = punishment['user_id']
        username = punishment['username']
        punishment_type = punishment['punishment_type']
        keyboard.append([
            InlineKeyboardButton(
                f"🚨 {username} ({punishment_type.upper()})",
                callback_data=f'view_punishment_{punishment["punishment_id"]}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Назад", callback_data='admin_menu')])
    return InlineKeyboardMarkup(keyboard)


# ========== REMOVE PUNISHMENT KEYBOARD ==========
def get_remove_punishment_keyboard(punishment_id):
    keyboard = [
        [InlineKeyboardButton("🔓 Снять наказание", callback_data=f'remove_punishment_{punishment_id}')],
        [InlineKeyboardButton("❌ Отмена", callback_data='view_punished_users')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== REJECTION TEMPLATES KEYBOARD ==========
def get_rejection_templates_keyboard(report_id):
    """Клавиатура выбора шаблона отклонения"""
    from database import db
    templates = db.get_all_templates()
    
    keyboard = []
    for template in templates:
        keyboard.append([
            InlineKeyboardButton(
                f"📝 {template['title']}", 
                callback_data=f'reject_with_template_{report_id}_{template["template_id"]}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='admin_menu')])
    return InlineKeyboardMarkup(keyboard)
