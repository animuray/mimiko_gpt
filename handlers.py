# handlers.py
import random
import string
from datetime import datetime
from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
import keyboards
from database import Database
from ai_api import query_gemini_api
from utils import escape_markdown, split_messages

# Инициализируем роутер и базу данных
router = Router()
db = Database('db.db')

# --- Состояния для машины состояний (FSM) ---
class Promo(StatesGroup):
    waiting_for_code = State()

class AdminPromo(StatesGroup):
    waiting_for_name = State()
    waiting_for_duration = State()
    waiting_for_quantity = State()

# --- 🔽 НОВЫЕ СОСТОЯНИЯ 🔽 ---
class AdminGrantPremium(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_duration = State()
# --- 🔼 КОНЕЦ НОВЫХ СОСТОЯНИЙ 🔼 ---


# --- Вспомогательные функции ---
def generate_random_code_part(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# ----- ОБРАБОТЧИКИ КОМАНД И КНОПОК ОСНОВНОЙ КЛАВИАТУРЫ -----

@router.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot):
    #... (код без изменений)
    db.add_user(message.from_user.id, message.from_user.username)
    if await check_subscription(message.from_user.id, bot):
        await message.answer(f"Привет, {message.from_user.first_name}!\nЯ Мимико, твой ИИ-помощник. Чем могу помочь?", reply_markup=keyboards.main_keyboard)
    else:
        await message.answer("Для доступа к боту, пожалуйста, подпишитесь на наш канал. Это займет всего секунду!", reply_markup=keyboards.subscribe_keyboard)

@router.message(Command("reset"))
@router.message(F.text == "🔄 Сбросить диалог")
async def cmd_reset(message: types.Message):
    #... (код без изменений)
    user_id = message.from_user.id
    current_profile_key = db.get_current_profile_key(user_id)
    db.reset_chat_history(user_id, current_profile_key)
    profile_name = config.PROFILES[current_profile_key]['name']
    await message.answer(f"♻️ Контекст для роли '{profile_name}' успешно сброшен. Начинаем с чистого листа!")




# @router.message(Command("limits"))
# async def cmd_lim(message: types.Message):
#     with open('text_ai.txt', 'r', encoding='utf-8') as f:
#         response = f.read()  # Читаем весь файл в одну строку

#     # Разделяем и отправляем части
#     for part in split_messages(response):
#         await message.answer(
#             text=part,
#             parse_mode="MarkdownV2"
#         )



@router.message(Command("role"))
@router.message(F.text == "🎭 Сменить роль")
async def cmd_role(message: types.Message):
    #... (код без изменений)
    user_id = message.from_user.id
    has_premium = db.check_premium_access(user_id)
    await message.answer("Выберите, в какой роли мне общаться с вами:", reply_markup=keyboards.get_roles_keyboard(has_premium))

@router.message(F.text == "📱 Профиль")
async def show_profile(message: types.Message):
    #... (код без изменений)
    user_id = message.from_user.id
    user_info = db.get_user_info(user_id)
    if not user_info:
        await message.answer("Не удалось найти ваш профиль. Попробуйте /start")
        return
    profile_key = user_info[3]
    profile_name = config.PROFILES.get(profile_key, {}).get('name', "Неизвестная")
    status = "ℹ️ Базовый доступ"
    if db.check_premium_access(user_id):
        sub_end_date_str = user_info[4]
        try:
            sub_end_date = datetime.strptime(sub_end_date_str, "%Y-%m-%d %H:%M:%S")
            status = f"💎 Премиум активен до {sub_end_date.strftime('%d.%m.%Y %H:%M:%S')}"
        except (ValueError, TypeError):
            status = "💎 Премиум активен (ошибка даты)"
    text = (f"👤 <b>Ваш профиль:</b>\n\n<b>ID:</b> <code>{user_info[0]}</code>\n<b>Текущая роль:</b> {profile_name}\n<b>Статус доступа:</b> {status}\n\nДля смены роли используйте кнопку «🎭 Сменить роль».")
    await message.answer(text, parse_mode='HTML')

@router.message(F.text == '💎 Тарифы')
async def show_tariffs(message: types.Message):
    #... (код без изменений)
    text = ("💎 <b>Наши тарифы</b> 💎\n\n<b>Базовый доступ (бесплатно):</b>\n- Доступ к стандартным ролям (Обычный чат, Программист).\n- Обязательная подписка на канал.\n\n<b>Премиум доступ:</b>\n- Доступ ко ВСЕМ ролям, включая эксклюзивные (Доктор, Тролль и другие).\n- Приоритетная поддержка.\n\nДля получения премиум-доступа вы можете воспользоваться промокодом (кнопка «🎁 Промокод») или связаться с администратором.")
    await message.answer(text, parse_mode='HTML')

@router.message(F.text == '❓ F.A.Q.')
async def show_faq(message: types.Message):
    #... (код без изменений)
    text = ("<b>Часто задаваемые вопросы:</b>\n\n<b>В: Как сменить роль (персону) ассистента?</b>\nО: Используйте кнопку «🎭 Сменить роль».\n\n<b>В: Бот перестал отвечать или отвечает странно. Что делать?</b>\nО: Используйте команду /reset или кнопку «🔄 Сбросить диалог», чтобы начать заново.\n\n<b>В: Что такое премиум-доступ?</b>\nО: Это доступ к эксклюзивным и более продвинутым ролям. Нажмите «💎 Тарифы» для подробностей.")
    await message.answer(text, parse_mode='HTML')

# --- 🔽 НОВЫЙ ОБРАБОТЧИК КНОПКИ 'ПОДДЕРЖАТЬ' 🔽 ---
@router.message(F.text == '💖 Поддержать')
async def show_donation_info(message: types.Message):
    """Отправляет сообщение с информацией о донате и инлайн-кнопкой."""
    await message.answer(
        text=config.DONATION_CONFIG['text'],
        reply_markup=keyboards.get_donate_keyboard()
    )
# --- 🔼 КОНЕЦ НОВОГО ОБРАБОТЧИКА 🔼 ---


# ----- СЕКЦИЯ АДМИНИСТРИРОВАНИЯ -----

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await message.answer("Добро пожаловать в админ-панель!", reply_markup=keyboards.admin_keyboard)

# --- Создание промокодов (без изменений) ---
@router.callback_query(F.data == "admin_create_promo")
async def start_promo_creation(callback: types.CallbackQuery, state: FSMContext):
    #... (код без изменений)
    if callback.from_user.id not in config.ADMIN_IDS: return await callback.answer("Недостаточно прав.", show_alert=True)
    await callback.message.edit_text("<b>Шаг 1/3:</b> Введите префикс для промокодов...", parse_mode='HTML')
    await state.set_state(AdminPromo.waiting_for_name)
    await callback.answer()
@router.message(AdminPromo.waiting_for_name)
async def process_promo_name(message: types.Message, state: FSMContext):
    #... (код без изменений)
    await state.update_data(name=message.text.upper().strip())
    await message.answer("<b>Шаг 2/3:</b> ... введите срок действия промокода в днях...", parse_mode='HTML')
    await state.set_state(AdminPromo.waiting_for_duration)
@router.message(AdminPromo.waiting_for_duration)
async def process_promo_duration(message: types.Message, state: FSMContext):
    #... (код без изменений)
    if not message.text.isdigit() or int(message.text) <= 0: return await message.answer("Ошибка: введите целое положительное число.")
    await state.update_data(duration=int(message.text))
    await message.answer("<b>Шаг 3/3:</b> ... сколько таких промокодов нужно сгенерировать...", parse_mode='HTML')
    await state.set_state(AdminPromo.waiting_for_quantity)
@router.message(AdminPromo.waiting_for_quantity)
async def process_promo_quantity(message: types.Message, state: FSMContext):
    #... (код без изменений)
    if not message.text.isdigit() or int(message.text) <= 0: return await message.answer("Ошибка: введите целое положительное число.")
    user_data = await state.get_data()
    prefix, duration, quantity = user_data['name'], user_data['duration'], int(message.text)
    await state.clear()
    await message.answer(f"Начинаю генерацию {quantity} промокодов...")
    generated_codes = [f"{prefix}-{generate_random_code_part()}" for _ in range(quantity)]
    db.add_promo_codes_batch(generated_codes, duration, quantity)
    codes_text = "\n".join(generated_codes)
    final_message = f"✅ <b>Готово!</b>\n\nСгенерировано {quantity} промокодов со сроком действия {duration} дн.:\n\n<code>{codes_text}</code>"
    if len(final_message) > 4096: await message.answer("Слишком много кодов. Они успешно добавлены в базу.")
    else: await message.answer(final_message, parse_mode='HTML')

# --- 🔽 НОВАЯ СЕКЦИЯ: ВЫДАЧА ПРЕМИУМА ПО ID 🔽 ---
@router.callback_query(F.data == "admin_grant_premium")
async def start_premium_grant(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс ручной выдачи премиума."""
    if callback.from_user.id not in config.ADMIN_IDS:
        return await callback.answer("Недостаточно прав.", show_alert=True)
    
    await callback.message.edit_text("<b>Шаг 1/2:</b> Введите User ID пользователя, которому нужно выдать премиум.", parse_mode='HTML')
    await state.set_state(AdminGrantPremium.waiting_for_user_id)
    await callback.answer()

@router.message(AdminGrantPremium.waiting_for_user_id)
async def process_grant_user_id(message: types.Message, state: FSMContext):
    """Шаг 1: Получение User ID."""
    if not message.text.isdigit():
        await message.answer("Ошибка: User ID должен быть числом. Попробуйте снова.")
        return
    
    await state.update_data(user_id=int(message.text))
    await message.answer("<b>Шаг 2/2:</b> Отлично. Теперь введите срок действия премиума в днях (например, `30`).", parse_mode='HTML')
    await state.set_state(AdminGrantPremium.waiting_for_duration)

@router.message(AdminGrantPremium.waiting_for_duration)
async def process_grant_duration(message: types.Message, state: FSMContext):
    """Шаг 2: Получение срока и выдача премиума."""
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Ошибка: Срок действия должен быть целым положительным числом. Попробуйте снова.")
        return
        
    user_data = await state.get_data()
    user_id = user_data['user_id']
    duration_days = int(message.text)
    
    await state.clear()
    
    success, msg = db.grant_premium_to_user(user_id, duration_days)
    
    await message.answer(msg) # Отправляем админу результат операции
# --- 🔼 КОНЕЦ НОВОЙ СЕКЦИИ 🔼 ---


# ----- СЕКЦИЯ АКТИВАЦИИ ПРОМОКОДОВ ПОЛЬЗОВАТЕЛЕМ -----
@router.message(F.text == '🎁 Промокод')
async def ask_for_promo(message: types.Message, state: FSMContext):
    #... (код без изменений)
    await message.answer("Введите ваш промокод:")
    await state.set_state(Promo.waiting_for_code)
@router.message(Promo.waiting_for_code)
async def process_promo(message: types.Message, state: FSMContext):
    #... (код без изменений)
    code = message.text.strip()
    success, msg = db.activate_promo_code(message.from_user.id, code)
    if success: await message.answer(f"✅ Успешно! {msg}")
    else: await message.answer(f"❌ Ошибка! {msg}")
    await state.clear()


# ----- ОБРАБОТЧИКИ CALLBACK'ОВ -----
@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: types.CallbackQuery, bot: Bot):
     #... (код без изменений)
    if await check_subscription(callback.from_user.id, bot):
        await callback.message.delete()
        await callback.answer("Спасибо за подписку!", show_alert=True)
        await bot.send_message(callback.from_user.id, "Отлично! Теперь вам доступны все функции. Можете начинать общение.", reply_markup=keyboards.main_keyboard)
    else:
        await callback.answer("Вы еще не подписались. Пожалуйста, подпишитесь на канал.", show_alert=True)
@router.callback_query(F.data.startswith("select_profile:"))
async def callback_select_profile(callback: types.CallbackQuery):
     #... (код без изменений)
    user_id = callback.from_user.id
    profile_key = callback.data.split(":")[1]
    profile = config.PROFILES.get(profile_key)
    if not profile: return await callback.answer("Такой роли не существует.", show_alert=True)
    if profile['is_premium'] and not db.check_premium_access(user_id): return await callback.answer("🔒 Эта роль доступна только по премиум-подписке.", show_alert=True)
    db.update_user_profile(user_id, profile_key)
    await callback.answer()
    await callback.message.edit_text(f"✅ Роль изменена на: <b>{profile['name']}</b>\n\nЧтобы начать новый диалог в этой роли, не забудьте /reset", parse_mode='HTML')


# ----- ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (ДИАЛОГ С ИИ) -----
@router.message(F.text)
async def handle_text_message(message: types.Message, bot: Bot):
     #... (код без изменений)
    user_id = message.from_user.id
    if not await check_subscription(user_id, bot):
        return await message.answer("Для продолжения общения, пожалуйста, подпишитесь на наш канал.", reply_markup=keyboards.subscribe_keyboard)
    await bot.send_chat_action(chat_id=user_id, action="typing")
    current_profile_key = db.get_current_profile_key(user_id)
    profile_settings = config.PROFILES[current_profile_key]
    system_prompt = {"role": "system", "content": profile_settings["prompt"]}
    history = db.get_chat_history(user_id, current_profile_key)
    messages_to_api = [system_prompt] + history + [{"role": "user", "content": message.text}]
    response_text = await query_gemini_api(messages_to_api)
    history.append({"role": "user", "content": message.text})
    history.append({"role": "assistant", "content": response_text})
    db.save_chat_history(user_id, current_profile_key, history)

 
    # if current_profile_key == 'MIMIKO_PROGRAMMER':
    #     pass
    
    # else:
    #     pass
    
    # if len(response_text) > 4096:
    #     parts = split_text(response_text)
    #     for part in parts: await message.answer(escape_markdown(part), parse_mode="MarkdownV2")
    # else:
    #     try: await message.answer(escape_markdown(response_text), parse_mode="MarkdownV2")
    #     except Exception: await message.answer(response_text)

    for part in split_messages(response_text):
            await message.answer(
            text=part,
            parse_mode="MarkdownV2"
        )
