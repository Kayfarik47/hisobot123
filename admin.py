import os
from datetime import datetime, timezone, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMINS
from database import (
    add_admin,
    get_all_admins,
    get_all_employees,
    get_late_reports,
    get_missed_employees,
    get_reports_by_date,
    is_admin,
    remove_admin,
)
from excel import build_excel_report

router = Router()

TASHKENT_TZ = timezone(timedelta(hours=5))
OWNER_ADMINS = set(ADMINS)


class AdminPanelState(StatesGroup):
    waiting_add_id = State()
    waiting_remove_id = State()


async def _is_admin(message: Message) -> bool:
    return bool(message.from_user and await is_admin(message.from_user.id))


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id in OWNER_ADMINS


def _parse_date(text: str):
    """
    Komanda matnidan sanani ajratib oladi: '/late 2026-08-10' -> '2026-08-10'.
    Sana berilmagan bo'lsa - bugungi sana (Toshkent vaqti). Noto'g'ri format bo'lsa - None.
    """
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return datetime.now(TASHKENT_TZ).date().isoformat()
    try:
        return datetime.strptime(parts[1].strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def _admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin:add")],
        [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="admin:remove")],
        [InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admin:list")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin:close")],
    ])


async def _resolve_user_name(message: Message, user_id: int) -> str:
    """Bot ko'ra olsa Telegramdagi nomini oladi, bo'lmasa ID bilan saqlaydi."""
    try:
        chat = await message.bot.get_chat(user_id)
        if getattr(chat, "full_name", None):
            return chat.full_name
        if getattr(chat, "title", None):
            return chat.title
    except Exception:
        pass
    return f"Admin {user_id}"


async def _extract_target_from_command(message: Message):
    """Reply qilingan foydalanuvchi yoki komanda yonidagi raqamli ID ni oladi."""
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.full_name

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].strip().lstrip("-").isdigit():
        user_id = int(parts[1].strip())
        return user_id, await _resolve_user_name(message, user_id)

    return None, None


async def _send_admin_list(message: Message):
    admins = await get_all_admins()
    if not admins:
        await message.answer("Adminlar ro'yxati bo'sh.")
        return

    lines = [f"👑 <b>Adminlar ({len(admins)}):</b>\n"]
    for i, (user_id, fullname, added_by, added_date) in enumerate(admins, start=1):
        owner = " — asosiy admin" if user_id in OWNER_ADMINS else ""
        lines.append(f"{i}. {fullname}\n   <code>{user_id}</code>{owner}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("adminpanel", "admin"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id if message.from_user else None):
        if await _is_admin(message):
            await message.answer("Bu bo'lim faqat asosiy admin uchun.")
        return

    await state.clear()
    await message.answer(
        "👑 <b>Admin boshqaruvi</b>\n\nKerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=_admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:add")
async def admin_add_callback(callback: CallbackQuery, state: FSMContext):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelState.waiting_add_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "➕ Yangi adminning <b>Telegram ID</b> raqamini yuboring.\n\n"
            "Masalan: <code>123456789</code>\n"
            "Bekor qilish: /cancel",
            parse_mode="HTML",
        )


@router.message(AdminPanelState.waiting_add_id)
async def admin_add_state(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id if message.from_user else None):
        await state.clear()
        return

    text = (message.text or "").strip()
    if text.lower() == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=_admin_panel_keyboard())
        return

    if not text.lstrip("-").isdigit():
        await message.answer("Faqat Telegram ID yuboring. Masalan: <code>123456789</code>", parse_mode="HTML")
        return

    user_id = int(text)
    fullname = await _resolve_user_name(message, user_id)
    await add_admin(user_id, fullname, message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ <b>{fullname}</b> admin qilindi.\nID: <code>{user_id}</code>",
        parse_mode="HTML",
        reply_markup=_admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:remove")
async def admin_remove_callback(callback: CallbackQuery, state: FSMContext):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelState.waiting_remove_id)
    admins = await get_all_admins()
    removable = [(uid, name) for uid, name, _, _ in admins if uid not in OWNER_ADMINS]

    await callback.answer()
    if not callback.message:
        return

    if not removable:
        await state.clear()
        await callback.message.answer(
            "O'chirish mumkin bo'lgan qo'shimcha admin yo'q.",
            reply_markup=_admin_panel_keyboard(),
        )
        return

    buttons = [
        [InlineKeyboardButton(text=f"❌ {name[:32]}", callback_data=f"admin:del:{uid}")]
        for uid, name in removable[:40]
    ]
    buttons.append([InlineKeyboardButton(text="↩️ Orqaga", callback_data="admin:back")])
    await callback.message.answer(
        "➖ O'chiriladigan adminni tanlang yoki uning Telegram ID sini yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("admin:del:"))
async def admin_delete_selected(callback: CallbackQuery, state: FSMContext):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    try:
        user_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("ID xato", show_alert=True)
        return

    if user_id in OWNER_ADMINS:
        await callback.answer("Asosiy adminni o'chirib bo'lmaydi", show_alert=True)
        return

    await remove_admin(user_id)
    await state.clear()
    await callback.answer("Admin o'chirildi")
    if callback.message:
        await callback.message.answer(
            f"✅ <code>{user_id}</code> adminlikdan chiqarildi.",
            parse_mode="HTML",
            reply_markup=_admin_panel_keyboard(),
        )


@router.message(AdminPanelState.waiting_remove_id)
async def admin_remove_state(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id if message.from_user else None):
        await state.clear()
        return

    text = (message.text or "").strip()
    if text.lower() == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=_admin_panel_keyboard())
        return

    if not text.lstrip("-").isdigit():
        await message.answer("Telegram ID yuboring. Masalan: <code>123456789</code>", parse_mode="HTML")
        return

    user_id = int(text)
    if user_id in OWNER_ADMINS:
        await message.answer("Asosiy adminni o'chirib bo'lmaydi.")
        return

    await remove_admin(user_id)
    await state.clear()
    await message.answer(
        f"✅ <code>{user_id}</code> adminlikdan chiqarildi.",
        parse_mode="HTML",
        reply_markup=_admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:list")
async def admin_list_callback(callback: CallbackQuery):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await _send_admin_list(callback.message)


@router.callback_query(F.data == "admin:back")
async def admin_back_callback(callback: CallbackQuery, state: FSMContext):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "👑 <b>Admin boshqaruvi</b>",
            parse_mode="HTML",
            reply_markup=_admin_panel_keyboard(),
        )


@router.callback_query(F.data == "admin:close")
async def admin_close_callback(callback: CallbackQuery, state: FSMContext):
    if not _is_owner(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass


@router.message(Command("addadmin"))
async def add_admin_cmd(message: Message):
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    user_id, fullname = await _extract_target_from_command(message)
    if user_id is None:
        await message.answer(
            "Foydalanuvchining xabariga reply qilib <code>/addadmin</code> yozing\n"
            "yoki <code>/addadmin TELEGRAM_ID</code> yuboring.",
            parse_mode="HTML",
        )
        return

    await add_admin(user_id, fullname, message.from_user.id)
    await message.answer(
        f"✅ <b>{fullname}</b> admin qilindi.\nID: <code>{user_id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("deladmin", "removeadmin"))
async def del_admin_cmd(message: Message):
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    user_id, fullname = await _extract_target_from_command(message)
    if user_id is None:
        await message.answer(
            "Foydalanuvchining xabariga reply qilib <code>/deladmin</code> yozing\n"
            "yoki <code>/deladmin TELEGRAM_ID</code> yuboring.",
            parse_mode="HTML",
        )
        return

    if user_id in OWNER_ADMINS:
        await message.answer("Asosiy adminni o'chirib bo'lmaydi.")
        return

    await remove_admin(user_id)
    await message.answer(
        f"✅ <b>{fullname}</b> adminlikdan chiqarildi.\nID: <code>{user_id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("admins"))
async def admins_cmd(message: Message):
    if not await _is_admin(message):
        return
    await _send_admin_list(message)


@router.message(Command("report", "hisobot"))
async def report_cmd(message: Message):
    if not await _is_admin(message):
        return
    panel_line = "\n/adminpanel - admin boshqaruvi" if _is_owner(message.from_user.id) else ""
    await message.answer(
        "Hisobot moduli tayyor.\n\n"
        "Buyruqlar:\n"
        "/stats [sana] - kunlik statistika\n"
        "/late [sana] - kech topshirganlar\n"
        "/missed [sana] - topshirmaganlar\n"
        "/excel [sana] - excel fayl yuklab olish\n"
        "/employees - xodimlar ro'yxati\n"
        "/admins - adminlar ro'yxati"
        f"{panel_line}\n\n"
        "Sana formati: YYYY-MM-DD, masalan: /late 2026-08-10\n"
        "Sana ko'rsatilmasa - bugungi kun olinadi."
    )


@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not await _is_admin(message):
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
    if not await _is_admin(message):
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
    if not await _is_admin(message):
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
    if not await _is_admin(message):
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
    if not await _is_admin(message):
        return
    employees = await get_all_employees()
    if not employees:
        await message.answer("Hozircha xodimlar ro'yxati bo'sh.")
        return

    lines = [f"👥 Xodimlar ro'yxati ({len(employees)}):\n"]
    for i, (user_id, fullname) in enumerate(employees, start=1):
        lines.append(f"{i}. {fullname}")
    await message.answer("\n".join(lines))
