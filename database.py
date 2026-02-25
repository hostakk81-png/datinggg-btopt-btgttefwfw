import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'reports.db'

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица администраторов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица правил
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                punishment_type TEXT NOT NULL,
                punishment_duration TEXT,
                created_by INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица жб
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                from_username TEXT NOT NULL,
                against_user_id INTEGER,
                against_username TEXT NOT NULL,
                violation_link TEXT,
                description TEXT NOT NULL,
                message_id INTEGER,
                chat_id INTEGER,
                topic_id INTEGER,
                status TEXT DEFAULT 'open',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица наказаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punishments (
                punishment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                rule_id INTEGER,
                punishment_type TEXT NOT NULL,
                punishment_duration TEXT,
                applied_by INTEGER,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(report_id),
                FOREIGN KEY (rule_id) REFERENCES rules(rule_id)
            )
        ''')
        
        # Таблица активных мутов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_mutes (
                mute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                punishment_id INTEGER,
                expires_at TIMESTAMP,
                FOREIGN KEY (punishment_id) REFERENCES punishments(punishment_id)
            )
        ''')
        
        # Таблица шаблонов отклонения жалоб
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rejection_templates (
                template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                created_by INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== ADMIN FUNCTIONS ==========
    def add_admin(self, user_id, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)',
                         (user_id, username))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def remove_admin(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def is_admin(self, user_id):
        from config import ADMIN_IDS
        
        # Проверяем сначала в конфиге
        if user_id in ADMIN_IDS:
            return True
        
        # Потом в БД
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_all_admins(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username FROM admins')
        admins = cursor.fetchall()
        conn.close()
        return admins
    
    # ========== RULES FUNCTIONS ==========
    def add_rule(self, article, description, punishment_type, punishment_duration, created_by):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO rules (article, description, punishment_type, punishment_duration, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (article, description, punishment_type, punishment_duration, created_by))
            conn.commit()
            rule_id = cursor.lastrowid
            conn.close()
            return rule_id
        except Exception as e:
            conn.close()
            return None
    
    def get_rule(self, rule_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rules WHERE rule_id = ?', (rule_id,))
        rule = cursor.fetchone()
        conn.close()
        return rule
    
    def get_all_rules(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rules ORDER BY rule_id DESC')
        rules = cursor.fetchall()
        conn.close()
        return rules
    
    def update_rule(self, rule_id, article, description, punishment_type, punishment_duration):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE rules 
                SET article = ?, description = ?, punishment_type = ?, punishment_duration = ?
                WHERE rule_id = ?
            ''', (article, description, punishment_type, punishment_duration, rule_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def delete_rule(self, rule_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rules WHERE rule_id = ?', (rule_id,))
        conn.commit()
        conn.close()
    
    # ========== REPORT FUNCTIONS ==========
    def create_report(self, from_user_id, from_username, against_user_id, against_username, violation_link, description):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO reports (from_user_id, from_username, against_user_id, against_username, violation_link, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (from_user_id, from_username, against_user_id, against_username, violation_link, description))
            conn.commit()
            report_id = cursor.lastrowid
            conn.close()
            return report_id
        except Exception as e:
            conn.close()
            return None
    
    def get_report(self, report_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reports WHERE report_id = ?', (report_id,))
        report = cursor.fetchone()
        conn.close()
        return report
    
    def update_report_message(self, report_id, message_id, chat_id, topic_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE reports 
            SET message_id = ?, chat_id = ?, topic_id = ?
            WHERE report_id = ?
        ''', (message_id, chat_id, topic_id, report_id))
        conn.commit()
        conn.close()
    
    def update_report_status(self, report_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE reports SET status = ? WHERE report_id = ?', (status, report_id))
        conn.commit()
        conn.close()
    
    # ========== PUNISHMENT FUNCTIONS ==========
    def add_punishment(self, report_id, user_id, username, rule_id, punishment_type, punishment_duration, applied_by):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO punishments (report_id, user_id, username, rule_id, punishment_type, punishment_duration, applied_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (report_id, user_id, username, rule_id, punishment_type, punishment_duration, applied_by))
            conn.commit()
            punishment_id = cursor.lastrowid
            conn.close()
            return punishment_id
        except Exception as e:
            conn.close()
            return None
    
    def get_punishment(self, punishment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM punishments WHERE punishment_id = ?', (punishment_id,))
        punishment = cursor.fetchone()
        conn.close()
        return punishment
    
    # ========== MUTE FUNCTIONS ==========
    def add_mute(self, user_id, chat_id, punishment_id, expires_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Проверяем, есть ли уже активный мут
            cursor.execute('''
                DELETE FROM active_mutes WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            cursor.execute('''
                INSERT INTO active_mutes (user_id, chat_id, punishment_id, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, chat_id, punishment_id, expires_at))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def remove_mute(self, user_id, chat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM active_mutes WHERE user_id = ? AND chat_id = ?
        ''', (user_id, chat_id))
        conn.commit()
        conn.close()
    
    def is_muted(self, user_id, chat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mute_id FROM active_mutes 
            WHERE user_id = ? AND chat_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
        ''', (user_id, chat_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    # ========== REJECTION TEMPLATES FUNCTIONS ==========
    def add_rejection_template(self, title, text, created_by):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO rejection_templates (title, text, created_by) 
                VALUES (?, ?, ?)
            ''', (title, text, created_by))
            conn.commit()
            return cursor.lastrowid
        except:
            return None
        finally:
            conn.close()
    
    def get_all_templates(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rejection_templates ORDER BY created_date DESC')
        templates = cursor.fetchall()
        conn.close()
        return templates
    
    def get_template(self, template_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rejection_templates WHERE template_id = ?', (template_id,))
        template = cursor.fetchone()
        conn.close()
        return template
    
    def delete_template(self, template_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rejection_templates WHERE template_id = ?', (template_id,))
        conn.commit()
        conn.close()

# Инициализируем БД глобально
db = Database()
