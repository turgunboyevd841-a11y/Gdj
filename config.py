import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]
    db_path: str

    salon_name: str
    salon_phone: str
    salon_address: str
    work_hours: str
    latitude: float
    longitude: float

def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN .env faylda topilmadi!")

    raw_ids = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x) for x in raw_ids.split(",") if x.strip()]

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        db_path=os.getenv("DB_PATH", "salon.db"),
        salon_name=os.getenv("SALON_NAME", "Go'zallik saloni"),
        salon_phone=os.getenv("SALON_PHONE", "+998 94 345 08 98"),
        salon_address=os.getenv("SALON_ADDRESS", "Toshkent, ... ko'chasi"),
        work_hours=os.getenv("WORK_HOURS", "10:00 – 19:00"),
        latitude=float(os.getenv("SALON_LAT", "41.1867567040663")),
        longitude=float(os.getenv("SALON_LON", "69.2797")),
    )


config = load_config()