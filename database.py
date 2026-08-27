import aiosqlite
from datetime import datetime

from config import ADMINS

DB = 'reports.db'


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS reports(
        user_id INTEGER,
        fullname TEXT,
        report_date TEXT,
        report_time TEXT,
        status TEXT,
        UNIQUE(user_id, report_date)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS employees(
        user_id INTEGER PRIMARY KEY,
        fullname TEXT,
        joined_date TEXT,
        active INTEGER DEFAULT 1
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY,
        fullname TEXT,
        added_by INTEGER,
        added_date TEXT,
        active INTEGER DEFAULT 1
        )''')

        # config.py dagi adminlar doim asosiy admin sifatida bazaga kiritiladi.
        # INSERT OR IGNORE mavjud yozuvning nomini/statusini buzmaydi.
        today = datetime.now().date().isoformat()
        for admin_id in ADMINS:
            await db.execute('''
                INSERT OR IGNORE INTO admins(user_id, fullname, added_by, added_date, active)
                VALUES(?, ?, ?, ?, 1)
            ''', (admin_id, f"Asosiy admin ({admin_id})", admin_id, today))
            # Asosiy admin tasodifan nofaol qilingan bo'lsa ham qayta faollashtiriladi.
            await db.execute("UPDATE admins SET active=1 WHERE user_id=?", (admin_id,))

        await db.commit()


# ---------- Admins ----------

async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT 1 FROM admins WHERE user_id=? AND active=1",
            (user_id,)
        ) as cur:
            return await cur.fetchone() is not None


async def add_admin(user_id: int, fullname: str, added_by: int):
    """Yangi adminni qo'shadi yoki oldin o'chirilgan adminni qayta faollashtiradi."""
    async with aiosqlite.connect(DB) as db:
        await db.execute('''
            INSERT INTO admins(user_id, fullname, added_by, added_date, active)
            VALUES(?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                fullname=excluded.fullname,
                added_by=excluded.added_by,
                added_date=excluded.added_date,
                active=1
        ''', (user_id, fullname, added_by, datetime.now().date().isoformat()))
        await db.commit()


async def remove_admin(user_id: int):
    """Adminni o'chirmasdan nofaol holatga o'tkazadi."""
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE admins SET active=0 WHERE user_id=?", (user_id,))
        await db.commit()


async def get_all_admins(active_only=True):
    async with aiosqlite.connect(DB) as db:
        query = "SELECT user_id, fullname, added_by, added_date FROM admins"
        if active_only:
            query += " WHERE active=1"
        query += " ORDER BY fullname"
        async with db.execute(query) as cur:
            return await cur.fetchall()


# ---------- Employees (xodimlar) ----------

async def add_employee(user_id, fullname):
    """
    Xodimni ro'yxatga qo'shadi (agar ID allaqachon mavjud bo'lsa, ismini
    O'ZGARTIRMAYDI - shu ID uchun bazadagi ism doim ustun turadi, Telegram
    profilidagi joriy ismdan qat'i nazar). Faqat faollik holatini yangilaydi.
    """
    async with aiosqlite.connect(DB) as db:
        await db.execute('''
            INSERT INTO employees(user_id, fullname, joined_date, active)
            VALUES(?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET active=1
        ''', (user_id, fullname, datetime.now().date().isoformat()))
        await db.commit()


async def deactivate_employee(user_id):
    """Guruhdan chiqib ketgan xodimni nofaol qiladi (missed ro'yxatidan chiqarish uchun)."""
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE employees SET active=0 WHERE user_id=?", (user_id,))
        await db.commit()


async def get_all_employees(active_only=True):
    async with aiosqlite.connect(DB) as db:
        query = "SELECT user_id, fullname FROM employees"
        if active_only:
            query += " WHERE active=1"
        query += " ORDER BY fullname"
        async with db.execute(query) as cur:
            return await cur.fetchall()


# ---------- Reports (hisobotlar) ----------

async def has_reported(user_id, report_date):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT 1 FROM reports WHERE user_id=? AND report_date=?",
            (user_id, report_date)
        ) as cur:
            return await cur.fetchone() is not None


async def add_report(user_id, fullname, report_date, report_time, status):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?)",
            (user_id, fullname, report_date, report_time, status)
        )
        await db.commit()


async def get_reports_by_date(report_date):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT user_id, fullname, report_time, status FROM reports "
            "WHERE report_date=? ORDER BY report_time",
            (report_date,)
        ) as cur:
            return await cur.fetchall()


async def get_late_reports(report_date):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT user_id, fullname, report_time FROM reports "
            "WHERE report_date=? AND status='Kechikdi' ORDER BY report_time",
            (report_date,)
        ) as cur:
            return await cur.fetchall()


async def get_missed_employees(report_date):
    """Shu sanada hisobot TOPSHIRMAGAN faol xodimlar ro'yxati."""
    async with aiosqlite.connect(DB) as db:
        async with db.execute('''
            SELECT e.user_id, e.fullname FROM employees e
            WHERE e.active = 1 AND e.user_id NOT IN (
                SELECT user_id FROM reports WHERE report_date = ?
            )
            ORDER BY e.fullname
        ''', (report_date,)) as cur:
            return await cur.fetchall()
