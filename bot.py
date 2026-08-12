import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from middlewares import EmployeeRegisterMiddleware
from report import router as report_router
from admin import router as admin_router
from employees_import import import_employees_from_excel


async def main():
    await init_db()
    await import_employees_from_excel()  # jim ravishda employees.xlsx dan bazaga qo'shadi

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(EmployeeRegisterMiddleware())

    dp.include_router(report_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
