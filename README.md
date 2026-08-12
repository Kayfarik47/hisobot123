# Hisobot Bot

Telegram guruhida xodimlar rasm + izoh ko'rinishida kunlik hisobot topshiradigan bot.

## Ishlash tartibi

- Xodim guruhda **rasm + izoh (caption)** yuboradi -> bot hisobotni bazaga yozadi.
- Hisobot vaqti `DEADLINE_HOUR:DEADLINE_MINUTE` dan oldin bo'lsa -> **Vaqtida**, aks holda -> **Kechikdi**.
- Bir kunda faqat 1 marta hisobot qabul qilinadi (qayta yuborsa, ogohlantirish beriladi).
- Guruhda yozgan har bir foydalanuvchi avtomatik ravishda "xodim" sifatida ro'yxatga olinadi (shu orqali kim hisobot topshirmaganini aniqlash mumkin).

## Admin buyruqlari

Faqat `config.py` dagi `ADMINS` ro'yxatidagi foydalanuvchilar uchun:

| Buyruq | Tavsif |
|---|---|
| `/report` | Buyruqlar ro'yxati |
| `/stats [YYYY-MM-DD]` | Kunlik statistika (topshirgan/kechikkan/topshirmagan) |
| `/late [YYYY-MM-DD]` | Kech topshirganlar ro'yxati |
| `/missed [YYYY-MM-DD]` | Hisobot topshirmaganlar ro'yxati |
| `/excel [YYYY-MM-DD]` | Shu sana bo'yicha Excel fayl (2 varaq: hisobotlar + topshirmaganlar) |
| `/employees` | Ro'yxatga olingan barcha xodimlar |

Sana ko'rsatilmasa, bugungi kun uchun natija chiqadi.

## O'rnatish

```bash
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, GROUP_ID, DEADLINE_HOUR/MINUTE ni to'ldiring
python bot.py
``` 
