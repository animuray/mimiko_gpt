import asyncio
from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
import config
from database import Database
from handlers import router as main_router # Импортируем роутер из handlers

async def main():
    # Инициализируем базу данных и создаем таблицы, если их нет
    db = Database('db.db')
    db.create_tables()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Включаем роутер из handlers.py
    dp.include_router(main_router)

    # Удаляем вебхуки перед запуском, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем polling
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

