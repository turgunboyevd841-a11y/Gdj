import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import config
from database import queries

TZ = ZoneInfo("Asia/Tashkent")


async def _send(bot: Bot, booking_id: int, user_id: int, text: str, kind: str):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logging.warning("Eslatma yuborilmadi (user %s): %s", user_id, e)
    finally:
        # Yuborilmasa ham (bot bloklangan) qayta-qayta urinmaslik uchun belgilaymiz
        await queries.mark_reminded(booking_id, kind)


async def remind_tomorrow(bot: Bot):
    """Har kuni 18:00: ertangi yozilishlar uchun."""
    tomorrow = (datetime.now(TZ) + timedelta(days=1)).date().isoformat()
    for bid, user_id, service, day, time in await queries.get_pending_reminders(tomorrow, "day"):
        text = (
            "⏰ <b>Eslatma</b>\n\n"
            f"Ertaga soat <b>{time}</b> da sizni kutamiz!\n"
            f"💇 {service}\n"
            f"📍 {config.salon_address}\n"
            f"📞 {config.salon_phone}"
        )
        await _send(bot, bid, user_id, text, "day")


async def remind_soon(bot: Bot):
    """Har 10 daqiqada: 2 soat ichida boshlanadigan yozilishlar uchun."""
    now = datetime.now(TZ)
    today = now.date().isoformat()
    for bid, user_id, service, day, time in await queries.get_pending_reminders(today, "hour"):
        start = datetime.strptime(f"{day} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        left = start - now
        if timedelta(0) < left <= timedelta(hours=2):
            text = (
                "⏰ <b>Eslatma</b>\n\n"
                f"Bugun soat <b>{time}</b> da yozilishingiz bor.\n"
                f"💇 {service}\n"
                f"📍 {config.salon_address}\n\nKutib qolamiz! 🌸"
            )
            await _send(bot, bid, user_id, text, "hour")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(remind_tomorrow, "cron", hour=18, minute=0, args=[bot])
    scheduler.add_job(remind_soon, "interval", minutes=10, args=[bot])
    return scheduler