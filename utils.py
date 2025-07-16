import re

def escape_markdown(text: str) -> str:
    """_Экранирует спецсимволы MarkdownV2 для текста вне блоков кода."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Используем lookbehind, чтобы не экранировать уже экранированные символы
    return re.sub(f'(?<!\\\\)([{re.escape(escape_chars)}])', r'\\\1', text)

def finalize_and_split_message(text: str, max_length: int) -> list[str]:
    """Разделяет уже готовый текст на части, если он превышает лимит."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def split_messages(text: str, max_length: int = 4096) -> list[str]:
    """
    Надежно разделяет текст на части <= max_length, сохраняя блоки кода.
    Удаляет '*' из обычного текста и корректно экранирует Markdown V2.
    """
    messages = []
    current_message = ""
    in_code_block = False
    
    # Обрабатываем каждую строку
    for line in text.split('\n'):
        # Проверяем на начало/конец блока кода
        if line.strip().startswith('```'):
            # Если мы внутри блока, эта строка его закрывает
            if in_code_block:
                in_code_block = False
                # Добавляем закрывающую строку. Если блок стал слишком большим,
                # отправляем то, что было до него, и начинаем новый.
                if len(current_message) + len(line) + 1 > max_length:
                    messages.extend(finalize_and_split_message(current_message, max_length))
                    current_message = ""
                current_message += '\n' + line
                
                # Завершаем блок и отправляем его как отдельное сообщение
                messages.extend(finalize_and_split_message(current_message, max_length))
                current_message = ""

            # Если мы были не в блоке, эта строка его открывает
            else:
                in_code_block = True
                # Отправляем весь текст, который был накоплен до этого блока
                if current_message:
                    messages.extend(finalize_and_split_message(current_message, max_length))
                
                # Начинаем новый `current_message` с этим блоком
                current_message = line
        
        # Если мы внутри блока кода
        elif in_code_block:
            # Если добавление новой строки превысит лимит,
            # нужно завершить текущий блок и начать новый
            if len(current_message) + len(line) + 1 > max_length:
                # 1. Завершаем текущий блок
                lang_line = current_message.split('\n')[0]
                lang = lang_line[3:].strip()
                current_message += '\n```'
                messages.extend(finalize_and_split_message(current_message, max_length))
                
                # 2. Начинаем новый блок с тем же языком
                current_message = f'```{lang}\n{line}'
            else:
                current_message += '\n' + line
        
        # Если мы не в блоке кода (обычный текст)
        else:
            # Удаляем '*' и экранируем спецсимволы
            processed_line = escape_markdown(line.replace('*', ''))
            
            if len(current_message) + len(processed_line) + 1 > max_length:
                messages.extend(finalize_and_split_message(current_message, max_length))
                current_message = ""

            # Добавляем разделитель, если сообщение не пустое
            if current_message:
                current_message += '\n' + processed_line
            else:
                current_message = processed_line

    # Добавляем все, что осталось в конце
    if current_message:
        # Если в конце остался незакрытый блок кода, принудительно закроем его
        if in_code_block:
            current_message += '\n```'
        messages.extend(finalize_and_split_message(current_message, max_length))

    return [msg for msg in messages if msg.strip()]