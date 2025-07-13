# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
# from aiogram import Router, F
# from main import bot
# from aiogram.types import BufferedInputFile 

# from io import BytesIO

# keyboard_router = Router()


# # Создаем объекты кнопок
# button_1 = KeyboardButton(text='Профиль📱')
# button_2 = KeyboardButton(text='Что-то тут')

# # Создаем объект клавиатуры, добавляя в него кнопки
# keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2]], resize_keyboard=True)


# @keyboard_router.message(F.text == 'Профиль📱')
# async def user_profile(message: Message):
#     user_data = db.get_user_info(message.from_user.id)
#     profile = f'🌟<b>Пользователь:</b> @{user_data[1]}\n🆔<b>Ваш ID:</b> {user_data[0]}\n\n🔥<b>Действующие подписки: {user_data[3]}</b>\n\n🗓<b>Присоединился:</b> {datetime.fromisoformat(user_data[2]).strftime("%d.%m.%Y")}'
    
#     await message.answer_photo(photo=photo_links.profile_photo2, caption=profile, parse_mode='HTML')
    # pass


# # Создаем клавиатуру
# def get_keyboard() -> InlineKeyboardMarkup:
#     builder = InlineKeyboardBuilder()
#     builder.add(
#         InlineKeyboardButton(text="1 месяц", callback_data="tariff1"),
#         InlineKeyboardButton(text="3 месяца", callback_data="tariff2"),
#         InlineKeyboardButton(text="6 месяцев", callback_data="tariff3"),
#         InlineKeyboardButton(text="12 месяцев", callback_data="tariff4"),
#     )
#     builder.adjust(2)
#     return builder.as_markup()


# @keyboard_router.message(F.text == 'Тарифы 📦')
# async def cmd_start(message: Message):
#     await message.answer(
#         "Вот список тарифов:",
#         reply_markup=get_keyboard()
#     )

# # Обработчики callback-запросов
# @keyboard_router.callback_query(lambda c: c.data == "tariff1")
# async def process_info(callback: CallbackQuery):
#     await callback.message.answer('Отправьте команду для оплаты:\n/buy_for_1_month')
#     await callback.answer()













# keyboards.py
from aiogram import types, Router, F, Bot # Импортируем Bot для типа аргумента
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup # Импорт специфических типов Telegram
import config # Импорт config для доступа к PROFILES
import logging
import pic_links

keyboard_router = Router()

# --- Существующая Reply Keyboard ---
button_1 = types.KeyboardButton(text='Профиль📱')
button_2 = types.KeyboardButton(text='❓ Помощь')
keyboard = types.ReplyKeyboardMarkup(
    keyboard=[[button_1, button_2]], 
    resize_keyboard=True,
    one_time_keyboard=False
)

# --- НОВАЯ Функция генерации Inline Keyboard для выбора профиля ---
def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру с кнопками для каждого доступного профиля.
    """
    builder = InlineKeyboardBuilder()
    # Проходим по всем профилям из конфига
    for profile_key, profile_data in config.PROFILES.items():
        # Создаем кнопку для каждого профиля. Callback data содержит префикс и ключ профиля.
        builder.add(types.InlineKeyboardButton(
            text=profile_data["name"], # Текст кнопки - название профиля
            callback_data=f"select_profile:{profile_key}" # Формат: "префикс:ключ_профиля"
        ))
    # Располагаем кнопки в 1 столбец для удобства
    builder.adjust(2) 
    return builder.as_markup()

# --- Пример обработки вашей существующей клавиатуры ---
@keyboard_router.message(F.text == 'Профиль📱')
async def user_profile(message: Message):
    # Чтобы использовать db и bot, их нужно либо инициализировать здесь, либо импортировать (если они глобальные)
    # Для простоты, предполагаем, что db и бот доступны через импорты или глобальные переменные
    try:
        from database import Database
        db = Database('db.db') # Или получите экземпляр db, если он создается иначе
        
        user_id = message.from_user.id
        user_data = db.get_user_info(user_id) # Получаем информацию пользователя из БД
        
        if user_data:
            # user_data содержит: user_id, username, join_date, current_profile_key
            profile_key = user_data[3] if len(user_data) > 3 and user_data[3] else config.DEFAULT_PROFILE_KEY
            profile_name = config.PROFILES.get(profile_key, config.PROFILES[config.DEFAULT_PROFILE_KEY])['name']
            
            user_info_text = (
                f"🌟 <b>Ваш Профиль</b>\n"
                f"Имя пользователя: @{user_data[1]}\n"
                f"Ваш ID: {user_data[0]}\n"
                f"Зарегистрирован: {user_data[2]}\n" # Дата регистрации
                f"<b>Текущий стиль общения:</b> {profile_name}"
            )
            # Отправляем информацию о профиле, показывая основную Reply клавиатуру
            await message.answer_photo(photo=pic_links.fons['bg_start'], caption=user_info_text, parse_mode='HTML', reply_markup=keyboard)
        else:
            await message.answer("Не удалось получить информацию о вашем профиле.", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды Профиль📱: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении профиля.", reply_markup=keyboard)
