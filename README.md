# Hisobot Bot

Telegram guruhida xodimlar rasm + izoh ko'rinishida kunlik hisobot topshiradigan bot.

## Ishlash tartibi

- Xodim guruhda rasm yuboradi -> bot hisobotni bazaga yozadi.
- Hisobot vaqti `DEADLINE_HOUR:DEADLINE_MINUTE` dan oldin bo'lsa -> **Vaqtida**, aks holda -> **Kechikdi**.
- Bir kunda faqat 1 marta hisobot qabul qilinadi.
- Guruhda yozgan foydalanuvchilar avtomatik ravishda xodimlar ro'yxatiga qo'shiladi.
- Adminlar SQLite bazada saqlanadi. `reports.db` saqlanib turgan oddiy restartlarda qo'shilgan adminlar ham saqlanadi.

## Admin buyruqlari

| Buyruq | Tavsif |
|---|---|
| `/report` yoki `/hisobot` | Buyruqlar ro'yxati |
| `/stats [YYYY-MM-DD]` | Kunlik statistika |
| `/late [YYYY-MM-DD]` | Kech topshirganlar |
| `/missed [YYYY-MM-DD]` | Hisobot topshirmaganlar |
| `/excel [YYYY-MM-DD]` | Excel hisobot |
| `/employees` | Xodimlar ro'yxati |
| `/admins` | Adminlar ro'yxati |

## Admin boshqaruvi

`config.py` dagi `ADMINS` ro'yxati **asosiy adminlar** hisoblanadi. Faqat ular yangi admin qo'sha/o'chira oladi.

- `/adminpanel` yoki `/admin` — tugmali admin boshqaruv paneli
- `/addadmin TELEGRAM_ID` — yangi admin qo'shish
- Biror foydalanuvchi xabariga reply qilib `/addadmin` — o'sha foydalanuvchini admin qilish
- `/deladmin TELEGRAM_ID` — adminni o'chirish
- Biror foydalanuvchi xabariga reply qilib `/deladmin` — o'sha adminni o'chirish
- `/admins` — barcha faol adminlarni ko'rish

Asosiy adminlarni panel orqali o'chirib bo'lmaydi.

## O'rnatish

```bash
pip install -r requirements.txt
python bot.py
```
