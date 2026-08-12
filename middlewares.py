from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import GROUP_ID
from database import add_employee


class EmployeeRegisterMiddleware(BaseMiddleware):
    """
    Guruhdagi har bir yozgan foydalanuvchini avtomatik ravishda
    'employees' jadvaliga qo'shib boradi. Shu orqali /missed komandasi
    hali birorta hisobot topshirmagan xodimlarni ham ko'ra oladi.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if (
            event.chat
            and event.chat.id == GROUP_ID
            and event.from_user
            and not event.from_user.is_bot
        ):
            await add_employee(event.from_user.id, event.from_user.full_name)

        return await handler(event, data)
