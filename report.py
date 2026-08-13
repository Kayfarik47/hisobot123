from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime, timezone, timedelta

from database import add_report, has_reported
from config import GROUP_ID, DEADLINE_HOUR, DEADLINE_MINUTE

router = Router()

TASHKENT_TZ = timezone(timedelta(hours=5))


@router.message(F.chat.id == GROUP_ID, F.photo)
async def report_handler(message: Message):
    now = datetime.now(TASHKENT_TZ)
    today = now.date().isoformat()

    if await has_reported(message.from_user.id, today):
        return

    deadline_passed = (now.hour, now.minute) > (DEADLINE_HOUR, DEADLINE_MINUTE)
    status = "Kechikdi" if deadline_passed else "Vaqtida"

    await add_report(
        message.from_user.id,
        message.from_user.full_name,
        today,
        now.strftime("%H:%M"),
        status
    )
