from typing import List

def split_text(text: str, max_length: int = 4096) -> List[str]:
    """Разбивает длинный текст на части, не превышающие max_length."""
    # Этот простой метод разбивает по переносам строк, что часто хорошо работает с форматированием.
    parts = []
    current_part = ""
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 < max_length:
            current_part += line + '\n'
        else:
            parts.append(current_part)
            current_part = line + '\n'
    parts.append(current_part)
    return [p for p in parts if p.strip()]

def escape_markdown(text: str) -> str:
    """Экранирует символы для Telegram MarkdownV2."""
    # Список символов для экранирования
    escape_chars = r'!_*[]()~`>#+-=|{}.'
    # Экранируем, добавляя \ перед каждым специальным символом
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)
