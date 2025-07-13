# import sqlite3
# from datetime import datetime, timedelta
# import config
# import json


# class Database:
#     def __init__(self, path_to_db="db.db"):
#         self.path_to_db = path_to_db
#         self.current_date = datetime.now().date()

#     @property
#     def connection(self):
#         return sqlite3.connect(self.path_to_db)

#     def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
#         if not parameters:
#             parameters = tuple()
#         connection = self.connection
#         cursor = connection.cursor()
#         cursor.execute(sql, parameters)
#         data = None
#         if commit:
#             connection.commit()
#         if fetchone:
#             data = cursor.fetchone()
#         if fetchall:
#             data = cursor.fetchall()
#         connection.close()
#         return data

#     #Добавление пользователя в базу если его нет
#     def add_user(self, user_id: int, username: str):
#         user = self.execute(f'SELECT * FROM Users WHERE user_id = {user_id}', fetchone=True)
#         if not user:
#             self.execute('INSERT INTO Users (user_id, username, join_date) VALUES (?, ?, ?)', (user_id, username, self.current_date), commit=True)


#     #Получение информации о пользователе
#     def get_user_info(self, user_id: int):
#         user_info = self.execute(f'SELECT * FROM Users WHERE user_id = {user_id}', fetchone=True, commit=True)
#         return user_info


#     def user_input_data(self, user_id: int, user_input_data: int):
#         uid = self.execute(f'SELECT user_input_data FROM Users WHERE user_id = {user_id}', fetchone=True, commit=True)
#         new_uid = user_input_data + uid[0]
#         self.execute(f'UPDATE Users SET user_input_data = ? WHERE user_id = {user_id}', (new_uid, ), commit=True)
    

#     def response_data(self, user_id: int, response_data: int):
#         rd = self.execute(f'SELECT response_data FROM Users WHERE user_id = {user_id}', fetchone=True, commit=True)
#         new_rd = response_data + rd[0]
#         self.execute(f'UPDATE Users SET response_data = ? WHERE user_id = {user_id}', (new_rd, ), commit=True)
    

#     def save_context(self, user_id: int, context_json: str, timestamp: str):
#         # Упрощаем до UPDATE без предварительной проверки
#         self.execute(
#             "UPDATE Users SET context_history = ?, last_context_update = ? WHERE user_id = ?",
#             (context_json, timestamp, user_id),
#             commit=True
#         )

#     def get_user_context(self, user_id: int) -> list:
#         result = self.execute(
#             "SELECT context_history FROM Users WHERE user_id = ?",
#             (user_id,),
#             fetchone=True
#         )
        
#         # ОБРАБОТКА 3 СЛУЧАЕВ:
#         # 1. 
#         if not result or not result[0]:
#             return [{"role": "system", "content": config.mimiko_profile_1}]
        
#         try:
#             # Пытаемся распарсить JSON
#             return json.loads(result[0])
#         except (json.JSONDecodeError, TypeError):
#             # Если парсинг не удался, возвращаем базовый контекст
#             return [{"role": "system", "content": config.mimiko_profile_1}]        


#     def sub_notification(user_id):
#         pass
#         # тут будет логика работы подписки пользователя на напоминание о учебе








# database.py
import sqlite3
from datetime import datetime, date # Import date
import config
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Database:
    def __init__(self, path_to_db="db.db"):
        self.path_to_db = path_to_db
        self.current_date = datetime.now().date()
        self.create_tables() # Ensure tables are created on initialization

    @property
    def connection(self):
        conn = sqlite3.connect(self.path_to_db)
        conn.execute("PRAGMA foreign_keys = ON;") # Если используете Foreign keys
        return conn

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        try:
            connection = self.connection
            cursor = connection.cursor()
            cursor.execute(sql, parameters)
            data = None
            if commit:
                connection.commit()
            if fetchone:
                data = cursor.fetchone()
            if fetchall:
                data = cursor.fetchall()
            return data
        finally:
            if connection:
                connection.close()

    def create_tables(self):
        # Создаем таблицу Users, если она не существует
        self.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                join_date DATE,
                context_history TEXT,
                last_context_update TEXT,
                -- Новая колонка для хранения ключа текущего профиля
                current_profile_key TEXT DEFAULT 'default' 
            )
        """, commit=True)
        # Если у вас есть другие таблицы, их создание тоже должно быть тут

    def add_user(self, user_id: int, username: str):
        # Используем INSERT OR IGNORE для безопасного добавления пользователя
        # Устанавливаем ключ профиля по умолчанию при регистрации
        self.execute(
            'INSERT OR IGNORE INTO Users (user_id, username, join_date, current_profile_key) VALUES (?, ?, ?, ?)', 
            (user_id, username, self.current_date, config.DEFAULT_PROFILE_KEY), 
            commit=True
        )

    def get_user_info(self, user_id: int):
        # Возвращаем пользователя с его current_profile_key
        return self.execute(f'SELECT user_id, username, join_date, current_profile_key FROM Users WHERE user_id = {user_id}', fetchone=True)

    def update_user_profile_key(self, user_id: int, profile_key: str):
        # Метод для обновления выбранного профиля пользователя
        self.execute(
            "UPDATE Users SET current_profile_key = ? WHERE user_id = ?",
            (profile_key, user_id),
            commit=True
        )
        logging.info(f"DB: Updated profile key for user {user_id} to '{profile_key}'")

    # Ваши существующие функции для ввода/вывода данных, если они нужны
    def user_input_data(self, user_id: int, user_input_len: int):
        current_data = self.execute(f'SELECT user_input_data FROM Users WHERE user_id = {user_id}', fetchone=True)
        current_count = current_data[0] if current_data and current_data[0] is not None else 0
        new_count = current_count + user_input_len
        self.execute(f'UPDATE Users SET user_input_data = ? WHERE user_id = {user_id}', (new_count, ), commit=True)
    
    def response_data(self, user_id: int, response_len: int):
        current_data = self.execute(f'SELECT response_data FROM Users WHERE user_id = {user_id}', fetchone=True)
        current_count = current_data[0] if current_data and current_data[0] is not None else 0
        new_count = current_count + response_len
        self.execute(f'UPDATE Users SET response_data = ? WHERE user_id = {user_id}', (new_count, ), commit=True)

    def save_context(self, user_id: int, context_data: list):
        """Сохраняет контекст диалога пользователя."""
        try:
            # Преобразуем список сообщений в JSON строку
            context_json = json.dumps(context_data, ensure_ascii=False, indent=None)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.execute(
                "UPDATE Users SET context_history = ?, last_context_update = ? WHERE user_id = ?",
                (context_json, timestamp, user_id),
                commit=True
            )
            logging.debug(f"DB: Saved context for user {user_id}, length: {len(context_data)}")
        except Exception as e:
            logging.error(f"DB: Error saving context for user {user_id}: {e}")

    def get_user_context(self, user_id: int) -> list:
        """
        Получает контекст пользователя, включая системный промпт выбранного профиля.
        """
        # Сперва получаем информацию о пользователе, чтобы узнать его текущий профиль
        user_data = self.execute(
            "SELECT current_profile_key, context_history FROM Users WHERE user_id = ?",
            (user_id,),
            fetchone=True
        )

        if not user_data:
            # Если пользователя нет в базе (что маловероятно, если он уже использовал /start),
            # добавляем его и возвращаем дефолтный контекст.
            logging.warning(f"DB: User {user_id} not found in get_user_context. Adding and returning default.")
            self.add_user(user_id, f"User_{user_id}")
            user_data = self.execute(
                "SELECT current_profile_key, context_history FROM Users WHERE user_id = ?",
                (user_id,),
                fetchone=True
            )
            if not user_data: # Чрезвычайный случай, если и после добавления не найдено
                return [{"role": "system", "content": "An error occurred fetching profile settings."}]

        current_profile_key, context_history_json = user_data

        # Если текущий ключ профиля отсутствует или некорректен, переключаемся на профиль по умолчанию
        if not current_profile_key or current_profile_key not in config.PROFILES:
            current_profile_key = config.DEFAULT_PROFILE_KEY
            # Опционально: обновить базу, если ключ был некорректен
            self.update_user_profile_key(user_id, current_profile_key)

        # Получаем настройки текущего активного профиля
        profile_settings = config.PROFILES[current_profile_key]
        system_prompt_content = profile_settings.get("system_prompt", config.PROFILES[config.DEFAULT_PROFILE_KEY]["system_prompt"])

        # Формируем стартовый список сообщений, который всегда включает системный промпт
        messages_list = [{"role": "system", "content": system_prompt_content}]
        
        # Добавляем историю диалога, если она есть
        if context_history_json:
            try:
                db_history = json.loads(context_history_json)
                # Важно: фильтруем историю, чтобы там был только тот системный промпт, который мы только что установили.
                # Любые старые системные промпты из сохраненной Истории нужно отбросить.
                filtered_db_history = [msg for msg in db_history if msg.get("role") != "system"]
                messages_list.extend(filtered_db_history)
                logging.debug(f"DB: Loaded context for user {user_id}, count: {len(messages_list)}")
            except (json.JSONDecodeError, TypeError):
                logging.warning(f"DB: Failed to parse context history for user {user_id}. Using current system prompt only.")
                # Если JSON некорректен, просто возвращаем системный промпт.
        else:
            logging.debug(f"DB: No context history found for user {user_id}. Using current system prompt only.")

        return messages_list

