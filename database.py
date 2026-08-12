import aiosqlite
from datetime import datetime

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
        await db.commit()


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
