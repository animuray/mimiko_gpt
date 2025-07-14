# database.py
import sqlite3
from datetime import datetime, timedelta
import config
import json

class Database:
    def __init__(self, path_to_db="db.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        """Используем свойство для получения соединения, чтобы оно всегда было свежим."""
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        # Используем 'with' для автоматического закрытия соединения и управления транзакциями
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(sql, parameters)
            data = None
            if commit:
                conn.commit()
            if fetchone:
                data = cursor.fetchone()
            if fetchall:
                data = cursor.fetchall()
            return data

    def create_tables(self):
        """Создает все необходимые таблицы базы данных."""
        self.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TEXT,
            current_profile_key TEXT,
            subscription_end_date TEXT
        );
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            profile_key TEXT,
            history TEXT,
            last_update TEXT,
            FOREIGN KEY (user_id) REFERENCES Users (user_id)
        );
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS PromoCodes (
            code TEXT PRIMARY KEY,
            duration_days INTEGER,
            total_uses INTEGER,
            used_count INTEGER DEFAULT 0
        );
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS PromoCodeActivations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            code TEXT,
            activation_date TEXT,
            UNIQUE(user_id, code)
        );
        """)

    def add_user(self, user_id: int, username: str):
        self.execute(
            'INSERT OR IGNORE INTO Users (user_id, username, join_date, current_profile_key) VALUES (?, ?, ?, ?)',
            (user_id, username, datetime.now().strftime("%d-%m-%Y"), config.DEFAULT_PROFILE_KEY),
            commit=True
        )

    def get_user_info(self, user_id: int):
        return self.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,), fetchone=True)

    def update_user_profile(self, user_id: int, profile_key: str):
        self.execute("UPDATE Users SET current_profile_key = ? WHERE user_id = ?", (profile_key, user_id), commit=True)
    
    def get_current_profile_key(self, user_id: int) -> str:
        result = self.execute("SELECT current_profile_key FROM Users WHERE user_id = ?", (user_id,), fetchone=True)
        return result[0] if result else config.DEFAULT_PROFILE_KEY

    def save_chat_history(self, user_id: int, profile_key: str, history: list):
        history_json = json.dumps(history, ensure_ascii=False)
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        entry = self.execute("SELECT id FROM ChatHistory WHERE user_id = ? AND profile_key = ?", (user_id, profile_key), fetchone=True)
        if entry:
            self.execute("UPDATE ChatHistory SET history = ?, last_update = ? WHERE id = ?", (history_json, now, entry[0]), commit=True)
        else:
            self.execute("INSERT INTO ChatHistory (user_id, profile_key, history, last_update) VALUES (?, ?, ?, ?)", (user_id, profile_key, history_json, now), commit=True)

    def get_chat_history(self, user_id: int, profile_key: str) -> list:
        entry = self.execute("SELECT history FROM ChatHistory WHERE user_id = ? AND profile_key = ?", (user_id, profile_key), fetchone=True)
        if entry and entry[0]:
            return json.loads(entry[0])
        return []

    def reset_chat_history(self, user_id: int, profile_key: str):
        self.execute("DELETE FROM ChatHistory WHERE user_id = ? AND profile_key = ?", (user_id, profile_key), commit=True)

    def check_premium_access(self, user_id: int) -> bool:
        user = self.get_user_info(user_id)
        if user and user[4]:
            try:
                end_date = datetime.strptime(user[4], "%Y-%m-%d %H:%M:%S")
                return end_date > datetime.now()
            except (ValueError, TypeError):
                return False
        return False
    
     # --- 🔽 НОВЫЙ МЕТОД ЗДЕСЬ 🔽 ---

    def grant_premium_to_user(self, user_id: int, duration_days: int):
        """Напрямую выдает или продлевает премиум-статус пользователю."""
        # Проверяем, существует ли пользователь в базе
        user_info = self.get_user_info(user_id)
        if not user_info:
            return False, f"Пользователь с ID {user_id} не найден в базе данных."

        # Логика расчета даты окончания (такая же, как для промокодов)
        current_subscription_end = user_info[4] if user_info else None
        
        start_date = datetime.now()
        if current_subscription_end:
            try:
                current_end_date = datetime.strptime(current_subscription_end, "%Y-%m-%d %H:%M:%S")
                if current_end_date > start_date:
                    start_date = current_end_date  # Продлеваем существующую подписку
            except (ValueError, TypeError):
                pass
        
        new_end_date = start_date + timedelta(days=duration_days)
        new_end_date_str = new_end_date.strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.execute("UPDATE Users SET subscription_end_date = ? WHERE user_id = ?", 
                         (new_end_date_str, user_id), commit=True)
            return True, f"Премиум для пользователя {user_id} успешно выдан до {new_end_date.strftime('%d.%m.%Y %H:%M')}."
        except Exception as e:
            return False, f"Произошла ошибка при обновлении базы данных: {e}"

    # --- 🔼 КОНЕЦ НОВОГО МЕТОДА 🔼 ---

    def add_promo_codes_batch(self, codes: list, duration_days: int, quantity: int):
        with self.connection as conn:
            cursor = conn.cursor()
            parameters = [(code, duration_days, 1) for code in codes]
            cursor.executemany("INSERT OR IGNORE INTO PromoCodes (code, duration_days, total_uses) VALUES (?, ?, ?)", parameters)
            conn.commit()

    def get_promo_code(self, code: str):
        return self.execute("SELECT code, duration_days, total_uses, used_count FROM PromoCodes WHERE code = ?", (code,), fetchone=True)

    def check_user_activation(self, user_id: int, code: str) -> bool:
        result = self.execute("SELECT id FROM PromoCodeActivations WHERE user_id = ? AND code = ?", (user_id, code,), fetchone=True)
        return result is not None

    def activate_promo_code(self, user_id: int, code: str):
        promo = self.get_promo_code(code)
        if not promo:
            return False, "Такой промокод не найден."

        if promo[3] >= promo[2]:
            return False, "Этот промокод уже был использован максимальное количество раз."

        if self.check_user_activation(user_id, code):
            return False, "Вы уже активировали этот промокод."

        duration_days = promo[1]
        user_info = self.get_user_info(user_id)
        current_subscription_end = user_info[4] if user_info else None
        
        start_date = datetime.now()
        if current_subscription_end:
            try:
                current_end_date = datetime.strptime(current_subscription_end, "%Y-%m-%d %H:%M:%S")
                if current_end_date > start_date:
                    start_date = current_end_date
            except (ValueError, TypeError):
                pass
        
        new_end_date = start_date + timedelta(days=duration_days)
        new_end_date_str = new_end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Users SET subscription_end_date = ? WHERE user_id = ?", (new_end_date_str, user_id))
                cursor.execute("UPDATE PromoCodes SET used_count = used_count + 1 WHERE code = ?", (code,))
                cursor.execute("INSERT INTO PromoCodeActivations (user_id, code, activation_date) VALUES (?, ?, ?)", (user_id, code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            return True, f"Доступ продлен до {new_end_date.strftime('%d.%m.%Y %H:%M')}!"
        except Exception as e:
            print(f"Ошибка транзакции при активации промокода: {e}")
            return False, "Произошла ошибка базы данных при активации. Попробуйте снова."