from aiogram import Bot, Dispatcher
import asyncio
import config
from aiogram.methods import DeleteWebhook

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

async def main():
    from handlers import handler_router
    from keyboards import keyboard_router
    from mimiko_ai_api import mimiko_ai_api_router
    
    dp.include_router(handler_router)
    dp.include_router(keyboard_router)
    dp.include_router(mimiko_ai_api_router)

    # Очищаем вебхуки
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    