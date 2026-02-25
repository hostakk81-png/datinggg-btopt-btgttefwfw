import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ConversationHandler, filters
)
from telegram import Update

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from handlers import (
    start, admin_panel, start_report, get_against_username, get_against_user_id,
    get_violation_link, get_description, submit_report, cancel_report,
    select_punishment, select_rule_for_punishment, confirm_punishment,
    cancel_punishment, handle_custom_mute_duration, handle_custom_ban_duration,
    update_message_to_custom_mute_prompt, update_message_to_custom_ban_prompt,
    view_punished_users, view_punishment_details, remove_punishment,
    AGAINST_USERNAME, AGAINST_USER_ID, VIOLATION_LINK, DESCRIPTION, SUBMIT_REPORT,
    CUSTOM_MUTE_TIME, CUSTOM_BAN_TIME
)
from admin_handlers import (
    admin_menu, admin_rules, add_rule_start, get_rule_article, get_rule_desc,
    select_punishment_type, select_ban_duration, confirm_rule_save, cancel_add_rule,
    view_rules, edit_rule, delete_rule, confirm_delete_rule, 
    edit_rule_details_start, view_templates, add_template_start, add_template_title, add_template_text,
    ADD_RULE_ARTICLE, ADD_RULE_DESC, SELECT_PUNISHMENT_TYPE, SELECT_BAN_DURATION,
    ADD_TEMPLATE_TITLE, ADD_TEMPLATE_TEXT
)

from handlers import (
    start, admin_panel, start_report, get_against_username, get_against_user_id,
    get_violation_link, get_description, submit_report, cancel_report,
    cancel_punishment, select_punishment, select_rule_for_punishment, confirm_punishment,
    update_message_to_custom_mute_prompt, handle_custom_mute_duration,
    update_message_to_custom_ban_prompt, handle_custom_ban_duration,
    view_punished_users, view_punishment_details, remove_punishment,
    reject_report, reject_with_template
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== SETUP APPLICATION ==========
def main():
    """Запуск бота"""
    
    # Проверяем, добавлены ли админы
    if not db.get_all_admins() and ADMIN_IDS:
        for admin_id in ADMIN_IDS:
            db.add_admin(admin_id, f"Admin_{admin_id}")
        logger.info(f"Добавлены администраторы из конфига: {ADMIN_IDS}")
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ========== HANDLERS ==========
    
    # Команда /start
    application.add_handler(CommandHandler('start', start))
    
    # Команда /admin
    application.add_handler(CommandHandler('admin', admin_panel))
    
    # ========== CONVERSATION HANDLERS ==========
    
    # ConversationHandler для подачи жалобы
    report_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_report, pattern='^start_report$')],
        states={
            AGAINST_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_against_username)
            ],
            AGAINST_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_against_user_id)
            ],
            VIOLATION_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_violation_link)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
            SUBMIT_REPORT: [
                CallbackQueryHandler(submit_report, pattern='^submit_report$'),
                CallbackQueryHandler(cancel_report, pattern='^cancel_report$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_report, pattern='^cancel_report$')
        ]
    )
    
    application.add_handler(report_conv_handler)
    
    # ConversationHandler для добавления правила
    add_rule_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_rule_start, pattern='^add_rule$')],
        states={
            ADD_RULE_ARTICLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_rule_article),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            ADD_RULE_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_rule_desc),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            SELECT_PUNISHMENT_TYPE: [
                CallbackQueryHandler(select_punishment_type, pattern='^rule_type_'),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            SELECT_BAN_DURATION: [
                CallbackQueryHandler(select_ban_duration, pattern='^(ban|mute)_duration_'),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
        ]
    )
    
    application.add_handler(add_rule_conv_handler)
    
    # ConversationHandler для редактирования правила
    edit_rule_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_rule_details_start, pattern='^edit_rule_details_')],
        states={
            ADD_RULE_ARTICLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_rule_article),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            ADD_RULE_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_rule_desc),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            SELECT_PUNISHMENT_TYPE: [
                CallbackQueryHandler(select_punishment_type, pattern='^rule_type_'),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ],
            SELECT_BAN_DURATION: [
                CallbackQueryHandler(select_ban_duration, pattern='^(ban|mute)_duration_'),
                CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_rule, pattern='^cancel_add_rule$')
        ]
    )
    
    application.add_handler(edit_rule_conv_handler)
    
    # ConversationHandler для кастомного времени мута
    custom_mute_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_message_to_custom_mute_prompt, pattern='^mute_duration_custom$')],
        states={
            CUSTOM_MUTE_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_mute_duration)
            ]
        },
        fallbacks=[]
    )
    application.add_handler(custom_mute_conv_handler)
    
    # ConversationHandler для кастомного времени бана
    custom_ban_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_message_to_custom_ban_prompt, pattern='^ban_duration_custom$')],
        states={
            CUSTOM_BAN_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_ban_duration)
            ]
        },
        fallbacks=[]
    )
    application.add_handler(custom_ban_conv_handler)
    
    # ConversationHandler для добавления шаблонов отклонения
    add_template_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_template_start, pattern='^add_template$')],
        states={
            ADD_TEMPLATE_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_template_title)
            ],
            ADD_TEMPLATE_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_template_text)
            ]
        },
        fallbacks=[]
    )
    application.add_handler(add_template_conv_handler)
    
    # ========== CALLBACK QUERY HANDLERS ==========
    
    # Админ-панель
    application.add_handler(CallbackQueryHandler(admin_menu, pattern='^admin_menu$'))
    application.add_handler(CallbackQueryHandler(admin_rules, pattern='^admin_rules$'))
    
    # Управление правилами
    application.add_handler(CallbackQueryHandler(view_rules, pattern='^view_rules$'))
    application.add_handler(CallbackQueryHandler(edit_rule, pattern='^edit_rule_[0-9]+$'))
    application.add_handler(CallbackQueryHandler(delete_rule, pattern='^delete_rule_[0-9]+$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_rule, pattern='^confirm_delete_rule_[0-9]+$'))
    application.add_handler(CallbackQueryHandler(confirm_rule_save, pattern='^confirm_rule_save$'))
    
    # Жалобы и наказания
    application.add_handler(CallbackQueryHandler(select_punishment, pattern='^punishment_(mute|kick|ban)_'))
    application.add_handler(CallbackQueryHandler(select_rule_for_punishment, pattern='^rule_(mute|kick|ban)_'))
    application.add_handler(CallbackQueryHandler(confirm_punishment, pattern='^confirm_(mute|kick|ban)_'))
    application.add_handler(CallbackQueryHandler(cancel_punishment, pattern='^cancel_punishment_'))
    
    # Отклонение жалоб и шаблоны
    application.add_handler(CallbackQueryHandler(view_templates, pattern='^view_templates$'))
    application.add_handler(CallbackQueryHandler(reject_report, pattern='^reject_report_[0-9]+$'))
    application.add_handler(CallbackQueryHandler(reject_with_template, pattern='^reject_with_template_'))
    application.add_handler(CallbackQueryHandler(cancel_punishment, pattern='^cancel_punishment_'))
    
    # Просмотр и снятие наказаний
    application.add_handler(CallbackQueryHandler(view_punished_users, pattern='^view_punished_users$'))
    application.add_handler(CallbackQueryHandler(view_punishment_details, pattern='^view_punishment_'))
    application.add_handler(CallbackQueryHandler(remove_punishment, pattern='^remove_punishment_'))
    
    # Запуск бота
    logger.info("🤖 Бот запущен!")
    application.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
