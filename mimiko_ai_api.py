# from aiogram import types, Router, F
# from typing import List
# import re
# import requests
# import config
# import json
# from datetime import datetime
# from main import bot
# from database import Database

# import logging

# # Настройка логирования
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# db = Database('db.db')

# mimiko_ai_api_router = Router()
# '''    google/gemini-2.0-flash-001'''
# async def query_deepseek_api(user_id: int, user_query: str, model="deepseek/deepseek-chat-v3-0324", temperature: float=0.6) -> str:
#     url = config.API_ENDPOINT
#     headers = {"Authorization": f"Bearer {config.AI_TOKEN}",
#                 "Content-Type": "application/json"}

#     # Получение контекста(список)
#     context_data = db.get_user_context(user_id)
    
#     # Добавляем запрос пользователя
#     context_data.append({"role": "user", "content": user_query})
    
#     payload = {"model": model, "messages": context_data, "temperature": temperature}

#     try:
#         logging.info(f"Отправка запроса к API: {url}, payload: {payload}")  # Логирование

#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         response_data = response.json()

#         if response_data.get("choices"):

#             logging.info(f"Получен ответ от API: {response_data}")  # Логирование

#             mimiko_reply = response_data["choices"][0]["message"]["content"].strip()

#             # Добавляем ответ мимико в контекст и сохраняем в базу данных
#             context_data.append({"role": "mimiko", "content": mimiko_reply})
#             db.save_context(user_id, json.dumps(context_data, ensure_ascii=False), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#             return mimiko_reply
        
#         raise Exception("No response content found in API response")

#     except Exception as e:
#         print(f"🚫 Ошибка API: {str(e)}")
#         return 'Ошибка API. Обратитесь в поддержку.'


# # Функция для сохранения контекста и времени
# def save_user_context(user_id: int, context_data: list):
#     """Функция сохранения контекста"""
#     context_json = json.dumps(context_data, ensure_ascii=False, indent=None)
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     db.save_context(user_id, context_json, timestamp) # сохранение контекста в базу данных

from typing import List

# Функция разбиения текста
def split_text(text: str, max_length: int = 4096) -> List[str]:
    """Разбивает текст на части по максимальной длине."""
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        test_chunk = " ".join(current_chunk + [word])
        if len(test_chunk) <= max_length:
            current_chunk.append(word)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks




def extract_code_blocks(text):
    """
    Извлекает блоки кода, заключенные в ```, из текста.

    Args:
      text: Текст, в котором необходимо найти блоки кода.

    Returns:
      Список строк, представляющих блоки кода. Возвращает пустой список,
      если блоки кода не найдены.
    """
    code_blocks = []
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        code_blocks.append(match.strip())

    return code_blocks




def extract_code_handler(text):
    """
    Обработчик команды /extract_code.
    Извлекает блоки кода из сообщения и отправляет их пользователю.
    """

    code_blocks = extract_code_blocks(text)

    if code_blocks:
        for i, block in enumerate(code_blocks):
            # Важно: экранируем специальные символы MarkdownV2
            escaped_block = block.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\-').replace('.', '\\.').replace('!', '\\!')
            try:
                return f"Блок кода {i+1}:\n```\n{escaped_block}\n```"
            except Exception as e:
                return f"Ошибка при отправке блока кода (возможно, слишком большой или содержит некорректные символы)."
    else:
        return "Блоки кода не найдены."






def fix_code_blocks(text: str) -> str:
    """Разбивает длинные кодовые блоки для Telegram."""
    # Ищем кодовые блоки
    pattern = r'```([\s\S]*?)```'
    # Разбиваем текст на части, чтобы кодовые блоки не превышали 4096 символов
    return re.sub(pattern, lambda m: replace_code_block(m.group(0)), text)

def replace_code_block(code_block: str) -> str:
    """Заменяет проблемный кодовый блок."""
    text = code_block
    # Если кодовый блок слишком длинный, разбиваем его
    while len(text) > 4096:
        split_index = 4096 - 5  # Оставляем немного места для форматирования
        text = text[:split_index] + '\n' + '\n```' + text[split_index:]
    return text

#  Функция экранирования текста для Telegram
def escape_telegram_markdown(text: str) -> str:
    """Экранирует специальные символы для форматирования Telegram."""
    special_chars = ['_', '>', '#', '=', '[', ']', '(', ')', '~', '+', '-', '.', '!', '*']
    text = text.replace('###', '')
    text = text.replace('#', '')
    text = text.replace('**', '')
    text = text.replace('---', '')
    return ''.join(f'\\{char}' if char in special_chars else char for char in text)


# # Ловим все сообщения написанные пользователем
# @mimiko_ai_api_router.message(F.text)
# async def handle_text(message: types.Message):
#     user_input = message.text
#     user_id = message.from_user.id
#     username = message.from_user.username or str(user_id)

#     # Добавлем пользователя в базу, если его нет и он каким-то образом пропустил команду /start
#     db.add_user(user_id, username)
    
#     try:
#         # Получаем ответ от API с сохранением контекста
#         await bot.send_chat_action(message.chat.id, 'typing')
#         response = await query_deepseek_api(user_id, user_input)

#         # Добавляем информацию о количестве отправленных и полученных слов в базу данных для информации в профиль пользователя.
#         db.user_input_data(user_id, len(user_input.split()))
#         db.response_data(user_id, len(response.split()))   
        
#         await bot.send_chat_action(message.chat.id, 'typing')

#         # Экранируем текст для MarkdownV2
#         try:
#             response = escape_telegram_markdown(response)                        

#             if len(response) <= 4096:
#                 await bot.send_chat_action(message.chat.id, 'typing')
#                 await message.answer(response, parse_mode="MarkdownV2")
#             else:
#                 response = fix_code_blocks(response)
#                 response = replace_code_block(response)
#                 chunks = split_text(response)
#                 print(chunks)
#                 for chunk in chunks:
#                     await bot.send_chat_action(message.chat.id, 'typing')
#                     await message.answer(chunk, parse_mode="MarkdownV2")

#         except Exception as e:
#             print(f"Ошибка экранирования: {str(e)}")
#             # Если экранирование не сработало, отправляем текст без разметки
#             if len(response) <= 4096:
#                 await message.answer(response, parse_mode=None)
#             else:
#                 chunks = split_text(response)
#                 for chunk in chunks:
#                     await message.answer(chunk, parse_mode=None)
                
#     except Exception as e:
#         logging.exception(f"Ошибка при обработке сообщения от пользователя: {e}")

#         error_msg = f"Произошла ошибка при обработке вашего запроса: {str(e)}"
#         await message.answer(error_msg)






from aiogram import types, Router, F, Bot
from aiogram.utils.chat_action import ChatActionSender # Для отправки "печатает"
from typing import List
import re
import requests
import config
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database import Database
import logging
from main import bot 

db = Database('db.db')
mimiko_ai_api_router = Router()


async def query_deepseek_api(user_id: int, user_query: str, model: str = "deepseek/deepseek-r1-0528-qwen3-8b", temperature: float = 0.6) -> str:
    """
    Отправляет запрос к API DeepSeek с контекстом пользователя.
    Системный промпт для текущего профиля будет получен автоматически из БД при вызове db.get_user_context().
    """
    url = config.API_ENDPOINT
    headers = {"Authorization": f"Bearer {config.AI_TOKEN}",
               "Content-Type": "application/json"}

    # Получаем текущий контекст пользователя из базы данных.
    # Функция get_user_context уже должна возвращать list со сгенерированным системным промптом.
    messages_context = db.get_user_context(user_id)
    
    # Добавляем запрос пользователя к контексту
    messages_context.append({"role": "user", "content": user_query})
    
    payload = {"model": model, "messages": messages_context, "temperature": temperature}

    try:
        logging.info(f"User {user_id}: Sending request to API. Model: {model}, Temp: {temperature}, Context len: {len(messages_context)}")

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response_data.get("choices"):
            mimiko_reply = response_data["choices"][0]["message"]["content"].strip()

            # Сохраняем обновленный контекст: исходный контекст + запрос пользователя + ответ AI
            # `messages_context` ПЕРЕД этим шагом уже содержит запрос пользователя.
            # Теперь добавляем ответ AI к этому же списку перед сохранением.
            messages_context.append({"role": "assistant", "content": mimiko_reply})
            db.save_context(user_id, messages_context) # Сохраняем полный диалог

            # Сохраняем статистику ввода/вывода
            db.user_input_data(user_id, len(user_query.split()))
            db.response_data(user_id, len(mimiko_reply.split()))

            return mimiko_reply
        
        logging.error(f"User {user_id}: API response did not contain choices.")
        # Если нет успешного ответа от API, все равно сохраняем запрос пользователя, чтобы контекст не терялся
        db.save_context(user_id, messages_context) 
        raise Exception("No response content found in API response")

    except requests.exceptions.RequestException as e:
        logging.error(f"User {user_id}: HTTP Error during API request: {e}")
        return 'Ошибка API: Не удалось подключиться к серверу. Пожалуйста, попробуйте позже.'
    except Exception as e:
        logging.exception(f"User {user_id}: An unexpected error occurred during API call: {e}")
        return f'Произошла внутренняя ошибка. {str(e)}'


# --- Обработчик для всех текстовых сообщений, кроме команд ---
@mimiko_ai_api_router.message(F.text)
async def handle_text(message: types.Message):
    user_input = message.text
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    # Получаем информацию о пользователе
    user_info = db.get_user_info(user_id) 
    if not user_info:
        logging.error(f"User {user_id} not found in DB for handle_text. Attempting add_user again.")
        db.add_user(user_id, username)
        user_info = db.get_user_info(user_id)
        if not user_info: # Если и после повторной попытки нет информации
            await message.answer("Произошла ошибка. Пожалуйста, перезапустите бота командой /start.")
            return
            
    # Cтруктура user_info: user_id, username, join_date, current_profile_key
    # Индекс 3 - это current_profile_key
    current_profile_key = user_info[3] if len(user_info) > 3 and user_info[3] else config.DEFAULT_PROFILE_KEY
    
    # Получаем настройки профиля для отображения
    profile_settings = config.PROFILES.get(current_profile_key, config.PROFILES[config.DEFAULT_PROFILE_KEY])
    profile_display_name = profile_settings["name"]
    
    try:
        # Отправляем действие "печатает" пользователю
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            # Вызываем функцию для получения ответа от API. Она сама возьмет нужный контекст из БД.
            response = await query_deepseek_api(user_id, user_input)

        print(current_profile_key)
        print(type(current_profile_key))

        # --- Обработка и отправка ответа ---
        # Это ваш существующий код для экранирования, разбиения и отправки.
        # Убедитесь, что функции split_text, escape_telegram_markdown, fix_code_blocks доступны.
        # Если они в mimiko_ai_api.py, можно вызывать их как mimiko_ai_api.split_text(...)
        # Или лучше импортировать их индивидуально в начале файла.
        
        # Для простоты, предположим, что они доступны через импорт `mimiko_ai_api`
        # если они определены в том же файле и не экспортированы явно.
        # Лучше всего импортировать их в начале файла handlers.py и mimiko_ai_api.py.
        # Здесь мы предполагаем, что они определены в mimiko_ai_api.py и доступны через `mimiko_ai_api` импорт.

        #
        #
        #
        #
        #

        if current_profile_key == 'mimiko_junior':
            try:
                processed_response = escape_telegram_markdown(response)

                if len(processed_response) > 4093:
                    processed_response = fix_code_blocks(processed_response)
                    
                    chunks = split_text(processed_response) # Или просто split_text()
                    
                    for chunk in chunks:
                        # Отправляем каждую часть с указанным именем профиля и парс-модом
                        await message.answer(
                            f"{profile_display_name}:\n{chunk}",
                            parse_mode="MarkdownV2"
                        )
                else:
                    # Если ответ помещается в одно сообщение
                    await message.answer(
                        f"{profile_display_name}:\n{processed_response}", 
                        parse_mode="MarkdownV2"
                    )
            except Exception as e:
                logging.exception(f"User {user_id}: Ошибка при отправке сообщения или экранировании: {e}")
                # Если возникла ошибка с MarkdownV2, отправляем как простой текст
                await message.answer(f"{profile_display_name}:\n{response}", parse_mode=None)
        
        elif current_profile_key == 'mimiko_middle':
            # f"{profile_display_name}:\n{response}"
            try:
                if len(response) > 4093:
                    chunks = split_text(response) # Или просто split_text()
                    for chunk in chunks:
                        # Отправляем каждую часть с указанным именем профиля и парс-модом
                        await message.answer(
                            f"{profile_display_name}:\n{chunk}",
                            parse_mode="MarkdownV2"
                        )
                else:
                    # Если ответ помещается в одно сообщение
                    await message.answer(
                        f"{profile_display_name}:\n{response}", 
                        parse_mode="MarkdownV2"
                    )
            except Exception as e:
                logging.exception(f"User {user_id}: Ошибка при отправке сообщения или экранировании: {e}")
                # Если возникла ошибка с MarkdownV2, отправляем как простой текст
                await message.answer(f"{profile_display_name}:\n{response}", parse_mode=None)

        elif current_profile_key == 'mimiko_senior':
            try:
                if len(response) > 4093:
                    chunks = split_text(response) # Или просто split_text()
                    for chunk in chunks:
                        # Отправляем каждую часть с указанным именем профиля и парс-модом
                        await message.answer(
                            f"{profile_display_name}:\n{chunk}",
                            parse_mode="MarkdownV2"
                        )
                else:
                    # Если ответ помещается в одно сообщение
                    await message.answer(
                        f"{profile_display_name}:\n{response}", 
                        parse_mode="MarkdownV2"
                    )
            except Exception as e:
                logging.exception(f"User {user_id}: Ошибка при отправке сообщения или экранировании: {e}")
                # Если возникла ошибка с MarkdownV2, отправляем как простой текст
                await message.answer(f"{profile_display_name}:\n{response}", parse_mode=None)

        elif current_profile_key == 'story_teller':
            try:
                if len(response) > 4093:
                    chunks = split_text(response) # Или просто split_text()
                    for chunk in chunks:
                        # Отправляем каждую часть с указанным именем профиля и парс-модом
                        await message.answer(
                            f"{profile_display_name}:\n{chunk}",
                            parse_mode="MarkdownV2"
                        )
                else:
                    # Если ответ помещается в одно сообщение
                    await message.answer(
                        f"{profile_display_name}:\n{response}", 
                        parse_mode="MarkdownV2"
                    )
            except Exception as e:
                logging.exception(f"User {user_id}: Ошибка при отправке сообщения или экранировании: {e}")
                # Если возникла ошибка с MarkdownV2, отправляем как простой текст
                await message.answer(f"{profile_display_name}:\n{response}", parse_mode=None)

        elif current_profile_key == 'mimiko_chat':
            try:
                if len(response) > 4093:
                    chunks = split_text(response) # Или просто split_text()
                    for chunk in chunks:
                        # Отправляем каждую часть с указанным именем профиля и парс-модом
                        await message.answer(
                            f"{profile_display_name}:\n{chunk}",
                            parse_mode="MarkdownV2"
                        )
                else:
                    # Если ответ помещается в одно сообщение
                    await message.answer(
                        f"{profile_display_name}:\n{response}", 
                        parse_mode="MarkdownV2"
                    )
            except Exception as e:
                logging.exception(f"User {user_id}: Ошибка при отправке сообщения или экранировании: {e}")
                # Если возникла ошибка с MarkdownV2, отправляем как простой текст
                await message.answer(f"{profile_display_name}:\n{response}", parse_mode=None)

    except Exception as e:
        logging.exception(f"User {user_id}: Общая ошибка при обработке текстового сообщения: {e}")
        error_msg = f"Произошла ошибка при обработке вашего запроса: {str(e)}"
        await message.answer(error_msg)

