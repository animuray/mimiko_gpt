# from aiogram import types, Router
# from aiogram.filters import Command
# from main import bot
# from database import Database
# import keyboards
# from datetime import datetime
# import config
# import mimiko_ai_api
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# db = Database('db.db')

# handler_router = Router()


# async def check_subscription(user_id: int, bot) -> bool:
#     try:
#         member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
#         return member.status in ['member', 'administrator', 'creator']
#     except Exception:
#         return False
    

# # Обработчик команды /start
# @handler_router.message(Command("start"))
# async def cmd_start(message: types.Message):
#     db.add_user(message.from_user.id, message.from_user.username)
#     db.get_user_context(message.from_user.id)

#     if await check_subscription(message.from_user.id, bot):
#         await bot.send_chat_action(message.chat.id, 'typing')
#         await message.answer('hello', reply_markup=keyboards.keyboard)

#     else:
#         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
#             [InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")]
#         ])
#         await message.answer(
#             "Пожалуйста, подпишитесь на наш канал для доступа к боту:",
#             reply_markup=keyboard
#         )

# async def check_subscription_callback(callback: types.CallbackQuery, bot):
#     if await check_subscription(callback.from_user.id, bot):
#         await callback.message.edit_text("Спасибо за подписку! Теперь вам доступен весь функционал.")
#         # await message.answer_photo(photo=photo_links.start_photo, caption=f'Привет, <b>{message.from_user.username}</b> ✨\
#         # \nДобро пожаловать в магазин цифровых товаров <a href="https://t.me/testykassaaa_bot">Mimiko_Shop</a>', parse_mode="HTML", reply_markup=keyboards.keyboard)
        
#     else:
#         await callback.answer("Вы ещё не подписались на канал!", show_alert=True)

# handler_router.callback_query.register(check_subscription_callback, lambda c: c.data == "check_subscription")


# @handler_router.message(Command("reset"))
# # Команда для сброса контекста на стандартный
# async def cmd_reset(message: types.Message):
#     default_context = [{"role": "system", "content": config.mimiko_profile_1}]
#     mimiko_ai_api.save_user_context(message.from_user.id, default_context)
#     await message.answer("♻️ Контекст успешно сброшен. Можем начать новый диалог.")


# @handler_router.message(Command("role"))
# async def cmd_role(message: types.Message):
#     text = db.get_user_context(764567038)
#     for t in text:
#         print(t)

# @handler_router.message(Command("limits"))
# async def cmd_limits(message: types.Message):
#     pass


# @handler_router.message(Command("gifts"))
# async def cmd_gifts(message: types.Message):
#     pass


# @handler_router.message(Command("settings"))
# async def cmd_settings(message: types.Message):
#     pass


# @handler_router.message(Command("help"))
# async def cmd_help(message: types.Message):
#     pass












# handlers.py
from aiogram import types, Router, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery # Импортируем нужные типы
from aiogram.utils.keyboard import InlineKeyboardBuilder # Для генерации клавиатуры
import config
import keyboards # Импортируем файл keyboards для доступа к get_profile_keyboard
import mimiko_ai_api # Для вызова функций из mimiko_ai_api.py
from database import Database

# --- Важно: Импорт бота из main.py ---
# Предполагается, что экземпляр бота определен глобально в main.py и доступен для импорта.
# Если нет, нужно передавать его экземпляр в роутеры или использовать контекст.
from main import bot 

db = Database('db.db') # Инициализируем базу данных
handler_router = Router()

# --- Функция проверки подписки (уже есть у вас) ---
async def check_subscription(user_id: int, bot_instance: Bot) -> bool:
    try:
        member = await bot_instance.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        # logging.error(f"Ошибка проверки подписки для пользователя {user_id}: {e}", exc_info=True)
        return False

# --- Обработчик команды /start (немного изменен для корректного показа клавиатуры) ---
@handler_router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Убедимся, что пользователь есть в базе данных
    db.add_user(user_id, username)
    
    # Проверяем его подписку
    if await check_subscription(user_id, bot):
        await bot.send_chat_action(message.chat.id, 'typing')
        # Показываем основную Reply клавиатуру при успешном старте
        await message.answer(
            f'Привет, {username}! 👋\nДобро пожаловать!\n\nВаш текущий стиль общения: **{config.PROFILES[config.DEFAULT_PROFILE_KEY]["name"]}**.', 
            parse_mode="Markdown", 
            reply_markup=keyboards.keyboard # Используем Reply клавиатуру из keyboards.py
        )
    else:
        # Если не подписан, показываем приглашение к подписке
        subscription_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Подписаться на канал", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
            [InlineKeyboardButton(text="✔️ Я подписался", callback_data="check_subscription")]
        ])
        await message.answer(
            "Пожалуйста, подпишитесь на наш канал, чтобы получить доступ ко всем функциям бота:",
            reply_markup=subscription_keyboard
        )

# --- Обработчик колбэка проверки подписки (уже есть у вас, просто убедимся в его корректности) ---
@handler_router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await check_subscription(user_id, bot): # Используем импортированного бота
        await callback_query.message.edit_text("Спасибо за подписку! Теперь вам доступен весь функционал.")
        # После успешной подписки показываем приветственное сообщение и основную клавиатуру
        await callback_query.message.answer(
            f'Привет, {callback_query.from_user.username}! 👋\nДобро пожаловать!\n\nВаш текущий стиль общения: **{config.PROFILES[config.DEFAULT_PROFILE_KEY]["name"]}**.', 
            parse_mode="Markdown",
            reply_markup=keyboards.keyboard # Основная Reply клавиатура
        )
    else:
        # Если пользователь все еще не подписан
        await callback_query.answer("Вы ещё не подписались на канал! Пожалуйста, подпишитесь, чтобы продолжить.", show_alert=True)

# --- НОВАЯ ФУНКЦИЯ: Обработчик команды /role ---
@handler_router.message(Command("role"))
async def cmd_role(message: types.Message):
    # Отправляем пользователю сообщение с инлайн-клавиатурой выбора профиля
    await message.answer(
        "Выберите стиль общения:",
        reply_markup=keyboards.get_profile_keyboard() # Получаем клавиатуру из keyboards.py
    )

# --- НОВАЯ ФУНКЦИЯ: Обработчик колбэк-запросов от инлайн-кнопок выбора профиля ---
@handler_router.callback_query(lambda c: c.data and c.data.startswith("select_profile:"))
async def process_profile_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    callback_data = callback_query.data

    try:
        # Разделяем callback_data: "select_profile:profle_key"
        prefix, profile_key = callback_data.split(":", 1)
        if prefix != "select_profile":
            return # Это не наш колбэк, игнорируем

        # Проверяем, существует ли такой профиль
        if profile_key not in config.PROFILES:
            await callback_query.answer("Ошибка: Такой стиль общения не существует.", show_alert=True)
            return

        # Обновляем ключ текущего профиля пользователя в базе данных
        db.update_user_profile_key(user_id, profile_key)
        print(profile_key)

        # Получаем название выбранного профиля для отображения пользователю
        selected_profile_name = config.PROFILES[profile_key]["name"]

        # Отвечаем на колбэк запроса (информационное уведомление)
        await callback_query.answer(f"Стиль общения изменен на: {selected_profile_name}")
        
        # Редактируем сообщение бота, чтобы показать, какой стиль теперь активен
        await callback_query.message.edit_text(
            f"✅ Ваш стиль общения теперь: **{selected_profile_name}**",
            parse_mode="Markdown"
        )
        
        # Опционально: можно отправить прямое сообщение пользователю, 
        # но редактирование исходного сообщения бота выглядит более наглядно
        await bot.send_message(user_id, f"Стиль общения установлен: {selected_profile_name}")

    except Exception as e:
        # logging.error(f"Ошибка при обработке выбора профиля (user_id: {user_id}): {e}", exc_info=True)
        await callback_query.answer("Произошла ошибка при обработке вашего выбора.", show_alert=True)

# --- Обработчик команды /reset (обновляем его для работы с новым профилем) ---
@handler_router.message(Command("reset"))
async def cmd_reset(message: types.Message):
    user_id = message.from_user.id
    current_context = db.get_user_info(user_id) # берем текущий профиль юзера с базы

    a = config.PROFILES[current_context[-1]]['system_prompt']
    print(a)
    # initial_context = [{"role": "system", "content": a}]
    # db.save_context(user_id, initial_context)

    # await message.answer("♻️ Контекст успешно сброшен до профиля Мимико для новых диалогов. Можем начать.")
    # Если вы хотите показать название профиля, а не просто "Мимико":
    # await message.answer(f"♻️ Контекст сброшен до профиля \"{config.PROFILES[config.DEFAULT_PROFILE_KEY]['name']}\". Можем начать.")


# --- Placeholder for other commands ---
@handler_router.message(Command("limits"))
async def cmd_limits(message: types.Message):
    await message.answer("Функционал лимитов пока не реализован.")


@handler_router.message(Command("gifts"))
async def cmd_gifts(message: types.Message):
    await message.answer("Функционал подарков пока не реализован.")

# Команда /settings может быть альтернативой для вызова выбора профиля, если хотите.
# @handler_router.message(Command("settings"))
# async def cmd_settings(message: types.Message):
#     await message.answer("Выберите нужную настройку:", reply_markup=some_settings_keyboard)

@handler_router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "👋 Добро пожаловать в справку!\n\n"
        "❓ <b>Основные команды:</b>\n"
        "- `/start`: Начать взаимодействие с ботом.\n"
        "- `/role`: Изменить стиль общения бота.\n"
        "- `/reset`: Сбросить текущий диалог к профилю Мимико и начать заново.\n"
        "- `/help`: Показать это сообщение справки.\n\n"
        "🤖 <b>Как сменить стиль:</b>\n"
        "Введите команду `/role`. Появится список стилей общения. Просто нажмите на нужный вам стиль.\n\n"
        "💬 <b>Отправка сообщений:</b>\n"
        "Все ваши обычные сообщения будут обрабатываться в соответствии с выбранным вами стилем."
    )
    await message.answer(help_text, parse_mode="HTML")
