import openpyxl

from database import add_employee

EXCEL_FILE = "employees.xlsx"


async def import_employees_from_excel(excel_file: str = EXCEL_FILE) -> int:
    """
    employees.xlsx faylidagi xodimlarni bazaga qo'shadi (jim, guruhga hech narsa yozmaydi).
    Fayl ustunlari: 'F.I.SH' va 'Telegram ID' (1-qator sarlavha).
    Qaytaradi: qo'shilgan/yangilangan xodimlar soni.
    """
    try:
        wb = openpyxl.load_workbook(excel_file)
    except FileNotFoundError:
        return 0

    ws = wb.active
    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 2:
            continue
        fullname, telegram_id = row[0], row[1]
        if fullname is None or telegram_id is None:
            continue
        fullname = str(fullname).strip()
        try:
            user_id = int(telegram_id)
        except (TypeError, ValueError):
            continue
        await add_employee(user_id, fullname)
        count += 1

    return count
