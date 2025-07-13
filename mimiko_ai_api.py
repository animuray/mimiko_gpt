from aiogram import types, Router, F
from typing import List
import re
import requests
import config
import json
from datetime import datetime
from main import bot
from database import Database

db = Database('db.db')

mimiko_ai_api_router = Router()
print(mimiko_ai_api_router)
async def query_deepseek_api(user_id: int, user_query: str, model="google/gemini-2.0-flash-001", temperature: float=0.6) -> str:
    url = config.API_ENDPOINT
    headers = {"Authorization": f"Bearer {config.AI_TOKEN}",
                "Content-Type": "application/json"}

    # Получение контекста(список)
    context_data = db.get_user_context(user_id)
    
    # Добавляем запрос пользователя
    context_data.append({"role": "user", "content": user_query})
    
    payload = {"model": model, "messages": context_data, "temperature": temperature}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("choices"):
            mimiko_reply = response_data["choices"][0]["message"]["content"].strip()

            # Добавляем ответ мимико в контекст и сохраняем в базу данных
            context_data.append({"role": "mimiko", "content": mimiko_reply})
            db.save_context(user_id, json.dumps(context_data, ensure_ascii=False), datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
            return mimiko_reply
        
        raise Exception("No response content found in API response")

    except Exception as e:
        print(f"🚫 Ошибка API: {str(e)}")
        return 'Ошибка API. Обратитесь в поддержку.'


# Функция для сохранения контекста и времени
def save_user_context(user_id: int, context_data: list):
    """Функция сохранения контекста"""
    context_json = json.dumps(context_data, ensure_ascii=False, indent=None)
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    db.save_context(user_id, context_json, timestamp) # сохранение контекста в базу данных

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
        split_index = 4096 - 1  # Оставляем немного места для форматирования
        text = text[:split_index] + '\n' + '\n```' + text[split_index:]
    return text

#  Функция экранирования текста для Telegram
def escape_telegram_markdown(text: str) -> str:
    """Экранирует специальные символы для форматирования Telegram."""
    special_chars = ['_', '>', '#', '=', '[', ']', '(', ')', '~', '+', '-', '.', '!', '*']
    text = text.replace('###', '')
    text = text.replace('#', '')
    text = text.replace('**', '')
    return ''.join(f'\\{char}' if char in special_chars else char for char in text)


# Ловим все сообщения написанные пользователем
@mimiko_ai_api_router.message(F.text)
async def handle_text(message: types.Message):
    user_input = message.text
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)

    # Добавлем пользователя в базу, если его нет и он каким-то образом пропустил команду /start
    db.add_user(user_id, username)
    
    try:
        # Получаем ответ от API с сохранением контекста
        await bot.send_chat_action(message.chat.id, 'typing')
        response = await query_deepseek_api(user_id, user_input)

        # Добавляем информацию о количестве отправленных и полученных слов в базу данных для информации в профиль пользователя.
        db.user_input_data(user_id, len(user_input.split()))
        db.response_data(user_id, len(response.split()))   
        
        await bot.send_chat_action(message.chat.id, 'typing')

        # Экранируем текст для MarkdownV2
        try:
            response = escape_telegram_markdown(response)                        

            if len(response) <= 4096:
                await bot.send_chat_action(message.chat.id, 'typing')
                await message.answer(response, parse_mode="MarkdownV2")
            else:
                response = fix_code_blocks(response)
                response = replace_code_block(response)
                chunks = split_text(response)
                print(f'\n\n\n{chunks}')
                for chunk in chunks:
                    await bot.send_chat_action(message.chat.id, 'typing')
                    await message.answer(chunk, parse_mode="MarkdownV2")

        except Exception as e:
            print(f"Ошибка экранирования: {str(e)}")
            # Если экранирование не сработало, отправляем текст без разметки
            if len(response) <= 4096:
                await message.answer(response, parse_mode=None)
            else:
                chunks = split_text(response)
                for chunk in chunks:
                    await message.answer(chunk, parse_mode=None)
                
    except Exception as e:
        error_msg = f"Произошла ошибка при обработке вашего запроса: {str(e)}"
        await message.answer(error_msg)



