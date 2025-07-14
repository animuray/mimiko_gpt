from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config


# --- Основная клавиатура с кнопкой "Поддержать" ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📱 Профиль'), KeyboardButton(text='🎭 Сменить роль')],
        [KeyboardButton(text='💎 Тарифы'), KeyboardButton(text='🎁 Промокод')],
        [KeyboardButton(text='❓ F.A.Q.'), KeyboardButton(text='💖 Поддержать')]
    ],
    resize_keyboard=True
)

# --- Админ-клавиатура с кнопкой "Выдать Премиум" ---
admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎁 Создать промокоды", callback_data="admin_create_promo")],
    [InlineKeyboardButton(text="👑 Выдать Премиум", callback_data="admin_grant_premium")]
])

# --- Инлайн-клавиатура для доната ---
def get_donate_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=config.DONATION_CONFIG['link_text'],
        url=config.DONATION_CONFIG['url']
    ))
    return builder.as_markup()


# --- Клавиатура для выбора роли ---
def get_roles_keyboard(has_premium: bool) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для выбора роли.
    Платные роли отмечаются замком 🔒, если у пользователя нет премиума.
    """
    builder = InlineKeyboardBuilder()
    for key, profile in config.PROFILES.items():
        text = profile['name']
        # Если профиль платный и у пользователя нет премиума, добавляем замок
        if profile['is_premium'] and not has_premium:
            text += ' 🔒'
        
        builder.add(InlineKeyboardButton(text=text, callback_data=f"select_profile:{key}"))
    
    # Расставляем кнопки по 2 в ряд
    builder.adjust(2)
    return builder.as_markup()

# --- Клавиатура для проверки подписки на канал ---
subscribe_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↗️ Подписаться на канал", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
    [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")]
])