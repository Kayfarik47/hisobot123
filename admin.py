import os
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from config import ADMINS
from database import (
    get_reports_by_date,
    get_late_reports,
    get_missed_employees,
    get_all_employees,
)
from excel import build_excel_report

router = Router()


def _is_admin(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id in ADMINS


def _parse_date(text: str):
    """
    Komanda matnidan sanani ajratib oladi: '/late 2026-08-10' -> '2026-08-10'.
    Sana berilmagan bo'lsa - bugungi sana. Noto'g'ri format bo'lsa - None.
    """
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return datetime.now().date().isoformat()
    try:
        return datetime.strptime(parts[1].strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


@router.message(Command("report"))
async def report_cmd(message: Message):
    if not _is_admin(message):
        return
    await message.answer(
        "Hisobot moduli tayyor.\n\n"
        "Buyruqlar:\n"
        "/stats [sana] - kunlik statistika\n"
        "/late [sana] - kech topshirganlar\n"
        "/missed [sana] - topshirmaganlar\n"
        "/excel [sana] - excel fayl yuklab olish\n"
        "/employees - xodimlar ro'yxati\n\n"
        "Sana formati: YYYY-MM-DD, masalan: /late 2026-08-10\n"
        "Sana ko'rsatilmasa - bugungi kun olinadi."
    )


@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not _is_admin(message):
        return
    report_date = _parse_date(message.text)
    if report_date is None:
        await message.answer("Sana formati noto'g'ri. Masalan: /stats 2026-08-10")
        return

    reports = await get_reports_by_date(report_date)
    late = await get_late_reports(report_date)
    missed = await get_missed_employees(report_date)
    employees = await get_all_employees()

    text = (
        f"📊 <b>{report_date}</b> statistikasi\n\n"
        f"👥 Jami xodimlar: {len(employees)}\n"
        f"✅ Topshirganlar: {len(reports)}\n"
        f"⏰ Kech topshirganlar: {len(late)}\n"
        f"❌ Topshirmaganlar: {len(missed)}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("late"))
async def late_cmd(message: Message):
    if not _is_admin(message):
        return
    report_date = _parse_date(message.text)
    if report_date is None:
        await message.answer("Sana formati noto'g'ri. Masalan: /late 2026-08-10")
        return

    late = await get_late_reports(report_date)
    if not late:
        await message.answer(f"{report_date}: kech topshirganlar yo'q. ✅")
        return

    lines = [f"⏰ <b>{report_date}</b> - kech topshirganlar ({len(late)}):\n"]
    for i, (user_id, fullname, report_time) in enumerate(late, start=1):
        lines.append(f"{i}. {fullname} — {report_time}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("missed"))
async def missed_cmd(message: Message):
    if not _is_admin(message):
        return
    report_date = _parse_date(message.text)
    if report_date is None:
        await message.answer("Sana formati noto'g'ri. Masalan: /missed 2026-08-10")
        return

    missed = await get_missed_employees(report_date)
    if not missed:
        await message.answer(f"{report_date}: barcha xodimlar hisobot topshirgan. ✅")
        return

    lines = [f"❌ <b>{report_date}</b> - topshirmaganlar ({len(missed)}):\n"]
    for i, (user_id, fullname) in enumerate(missed, start=1):
        lines.append(f"{i}. {fullname}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("excel"))
async def excel_cmd(message: Message):
    if not _is_admin(message):
        return
    report_date = _parse_date(message.text)
    if report_date is None:
        await message.answer("Sana formati noto'g'ri. Masalan: /excel 2026-08-10")
        return

    status_msg = await message.answer("Excel fayl tayyorlanmoqda...")
    filename = await build_excel_report(report_date)
    try:
        await message.answer_document(
            FSInputFile(filename),
            caption=f"📎 {report_date} sanasi bo'yicha hisobot"
        )
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()


@router.message(Command("employees"))
async def employees_cmd(message: Message):
    if not _is_admin(message):
        return
    employees = await get_all_employees()
    if not employees:
        await message.answer("Hozircha xodimlar ro'yxati bo'sh.")
        return

    lines = [f"👥 Xodimlar ro'yxati ({len(employees)}):\n"]
    for i, (user_id, fullname) in enumerate(employees, start=1):
        lines.append(f"{i}. {fullname}")
    await message.answer("\n".join(lines))
