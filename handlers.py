from aiogram import types, Router
from aiogram.filters import Command
from main import bot
from database import Database
import keyboards
from datetime import datetime
import config
import mimiko_ai_api
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

db = Database('db.db')

handler_router = Router()


async def check_subscription(user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False
    

# Обработчик команды /start
@handler_router.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username)
    db.get_user_context(message.from_user.id)

    if await check_subscription(message.from_user.id, bot):
        await bot.send_chat_action(message.chat.id, 'typing')
        await message.answer('hello', reply_markup=keyboards.keyboard)

    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
            [InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")]
        ])
        await message.answer(
            "Пожалуйста, подпишитесь на наш канал для доступа к боту:",
            reply_markup=keyboard
        )

async def check_subscription_callback(callback: types.CallbackQuery, bot):
    if await check_subscription(callback.from_user.id, bot):
        await callback.message.edit_text("Спасибо за подписку! Теперь вам доступен весь функционал.")
        # await message.answer_photo(photo=photo_links.start_photo, caption=f'Привет, <b>{message.from_user.username}</b> ✨\
        # \nДобро пожаловать в магазин цифровых товаров <a href="https://t.me/testykassaaa_bot">Mimiko_Shop</a>', parse_mode="HTML", reply_markup=keyboards.keyboard)
        
    else:
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)

handler_router.callback_query.register(check_subscription_callback, lambda c: c.data == "check_subscription")


@handler_router.message(Command("reset"))
# Команда для сброса контекста на стандартный
async def cmd_reset(message: types.Message):
    default_context = [{"role": "system", "content": config.PROFILES['DEFAULT_PROFILE']}]
    mimiko_ai_api.save_user_context(message.from_user.id, default_context)
    await message.answer("♻️ Контекст успешно сброшен. Можем начать новый диалог.")


@handler_router.message(Command("role"))
async def cmd_role(message: types.Message):
    text = db.get_user_context(764567038)
    print(text)

@handler_router.message(Command("limits"))
async def cmd_limits(message: types.Message):
    pass


@handler_router.message(Command("gifts"))
async def cmd_gifts(message: types.Message):
    pass


@handler_router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    pass


@handler_router.message(Command("help"))
async def cmd_help(message: types.Message):
    pass



