"""
Точка входа в Telegram-бота системы лояльности для кафе.

Запускает бота, инициализирует базу данных,
подключает роутеры (роутеры обработчиков клиента, кассира и админа),
а также выводит информацию о запуске в консоль.

Использует:
- aiogram 3.x
- SQLite через отдельные модули
- FSM для административных действий
"""

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from handlers.client_handlers import client_router
from handlers.staff_handlers import staff_router
from handlers.admin_handlers import admin_router

from config import BOT_TOKEN
from database import init_db

import asyncio
from importlib import reload
from config import ADMIN_ID

print(f"CURRENT ADMIN_ID: {ADMIN_ID} (type: {type(ADMIN_ID)})")


async def main():
    """
    Основная асинхронная функция запуска бота.
    
    Что делает:
    - Инициализирует базу данных
    - Создаёт диспетчер и подключает роутеры
    - Запускает polling режим получения обновлений
    """
    init_db()
    default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default)

    dp = Dispatcher()
    dp.include_router(client_router)
    dp.include_router(staff_router)
    dp.include_router(admin_router)
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())