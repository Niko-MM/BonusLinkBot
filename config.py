from dotenv import load_dotenv
import os

load_dotenv()


BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
ADMIN_ID = int(str(os.getenv("ADMIN_ID")).strip()) 


if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("Invalid .env configuration!")


# Конфиг точек (адреса для клавиатур и сообщений)
CAFES = {
    1: {
        "name": "Центральная кофейня",
        "address": "ул. Центральная, 1"
    },
    2: {
        "name": "Кофейня в ТЦ «Галерея»",
        "address": "ТРЦ «Галерея», 2 этаж"
    },
    3: {
        "name": "Кофейня на Вокзале",
        "address": "пл. Вокзальная, 5"
    }
}
