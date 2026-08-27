from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004317972340"))
ADMINS = [6262166970, 515523963, 6262616970, 387045032]

# Hisobot topshirish uchun so'nggi muddat (shundan keyin "Kechikdi" deb belgilanadi)
DEADLINE_HOUR = int(os.getenv("DEADLINE_HOUR", "14"))
DEADLINE_MINUTE = int(os.getenv("DEADLINE_MINUTE", "0"))
