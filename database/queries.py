from datetime import date, datetime

import aiosqlite

from .db import DB_PATH

# Salonning ish vaqtlari (soat bo'yicha)
TIMES = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]


# ==================== Foydalanuvchilar ====================
async def add_user(user_id: int, full_name: str, username: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
            (user_id, full_name, username),
        )
        await db.commit()


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cur.fetchall()]


# ==================== Xizmatlar ====================
async def get_services() -> list[tuple]:
    """[(id, name, price), ...]"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name, price FROM services WHERE is_active = 1"
        )
        return await cur.fetchall()


async def get_service(service_id: int) -> tuple | None:
    """(id, name, price) yoki None"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name, price FROM services WHERE id = ?", (service_id,)
        )
        return await cur.fetchone()


async def add_service(name: str, price: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO services (name, price) VALUES (?, ?)", (name, price)
        )
        await db.commit()


async def delete_service(service_id: int) -> None:
    """Xizmatni o'chirmaydi, faqat yashiradi (eski yozilishlar buzilmasligi uchun)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE services SET is_active = 0 WHERE id = ?", (service_id,)
        )
        await db.commit()


# ==================== Yozilishlar ====================
async def get_free_times(day: str) -> list[str]:
    """
    Berilgan kundagi bo'sh vaqtlar. day = '2026-11-12'.
    Bugun bo'lsa, o'tib ketgan soatlar ham chiqarilmaydi.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT time FROM bookings WHERE day = ? AND status != 'cancelled'",
            (day,),
        )
        busy = {row[0] for row in await cur.fetchall()}

    free = [t for t in TIMES if t not in busy]

    if day == date.today().isoformat():
        now = datetime.now().strftime("%H:%M")
        free = [t for t in free if t > now]

    return free


async def add_booking(
    user_id: int,
    service_id: int,
    day: str,
    time: str,
    name: str,
    phone: str,
) -> int | None:
    """Yangi yozilish. Vaqt band bo'lsa None qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cur = await db.execute(
                """INSERT INTO bookings (user_id, service_id, day, time, name, phone)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, service_id, day, time, name, phone),
            )
            await db.commit()
            return cur.lastrowid
        except aiosqlite.IntegrityError:
            return None


async def get_booking(booking_id: int) -> tuple | None:
    """(id, user_id, service_name, day, time, name, phone, status) yoki None"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT b.id, b.user_id, s.name, b.day, b.time, b.name, b.phone, b.status
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.id = ?""",
            (booking_id,),
        )
        return await cur.fetchone()


async def get_user_bookings(user_id: int) -> list[tuple]:
    """Mijozning faol yozilishlari: [(id, service_name, day, time, status), ...]"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT b.id, s.name, b.day, b.time, b.status
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.user_id = ? AND b.status != 'cancelled' AND b.day >= ?
               ORDER BY b.day, b.time""",
            (user_id, date.today().isoformat()),
        )
        return await cur.fetchall()


async def set_booking_status(booking_id: int, status: str) -> None:
    """status: 'pending' | 'confirmed' | 'cancelled'"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id)
        )
        await db.commit()


async def cancel_user_booking(booking_id: int, user_id: int) -> bool:
    """Mijoz faqat o'z yozilishini bekor qila oladi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """UPDATE bookings SET status = 'cancelled'
               WHERE id = ? AND user_id = ? AND status != 'cancelled'""",
            (booking_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def get_bookings_by_day(day: str) -> list[tuple]:
    """Admin uchun: [(id, time, service_name, name, phone, status), ...]"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT b.id, b.time, s.name, b.name, b.phone, b.status
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.day = ? AND b.status != 'cancelled'
               ORDER BY b.time""",
            (day,),
        )
        return await cur.fetchall()


async def get_confirmed_for_reminder(day: str) -> list[tuple]:
    """Eslatma uchun: [(user_id, service_name, time), ...] (tasdiqlanganlar)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT b.user_id, s.name, b.time
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.day = ? AND b.status = 'confirmed'""",
            (day,),
        )
        return await cur.fetchall()
    

async def update_service_price(service_id: int, price: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE services SET price = ? WHERE id = ?", (price, service_id)
        )
        await db.commit()


async def update_service_name(service_id: int, name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE services SET name = ? WHERE id = ?", (name, service_id)
        )
        await db.commit()

async def get_stats(date_from: str, date_to: str) -> dict:
    """date_from va date_to: 'YYYY-MM-DD' (ikkalasi ham kiradi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Holatlar bo'yicha soni
        cur = await db.execute(
            """SELECT status, COUNT(*) FROM bookings
               WHERE day BETWEEN ? AND ? GROUP BY status""",
            (date_from, date_to),
        )
        by_status = {row[0]: row[1] for row in await cur.fetchall()}

        # Taxminiy daromad (faqat tasdiqlanganlar)
        cur = await db.execute(
            """SELECT COALESCE(SUM(s.price), 0)
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.day BETWEEN ? AND ? AND b.status = 'confirmed'""",
            (date_from, date_to),
        )
        (revenue,) = await cur.fetchone()

        # Eng ommabop xizmatlar (bekor qilinmaganlar)
        cur = await db.execute(
            """SELECT s.name, COUNT(*) AS c
               FROM bookings b JOIN services s ON s.id = b.service_id
               WHERE b.day BETWEEN ? AND ? AND b.status != 'cancelled'
               GROUP BY s.id ORDER BY c DESC LIMIT 5""",
            (date_from, date_to),
        )
        top_services = await cur.fetchall()

        # Noyob mijozlar
        cur = await db.execute(
            """SELECT COUNT(DISTINCT user_id) FROM bookings
               WHERE day BETWEEN ? AND ? AND status != 'cancelled'""",
            (date_from, date_to),
        )
        (clients,) = await cur.fetchone()

        # Jami foydalanuvchilar (botga kirganlar)
        cur = await db.execute("SELECT COUNT(*) FROM users")
        (total_users,) = await cur.fetchone()

    return {
        "by_status": by_status,
        "revenue": revenue,
        "top_services": top_services,
        "clients": clients,
        "total_users": total_users,
    }


async def get_pending_reminders(day: str, kind: str) -> list[tuple]:
    """
    Hali eslatma yuborilmagan tasdiqlangan yozilishlar.
    kind: 'day' yoki 'hour'
    Qaytaradi: [(id, user_id, service_name, day, time), ...]
    """
    col = "reminded_day" if kind == "day" else "reminded_hour"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            f"""SELECT b.id, b.user_id, s.name, b.day, b.time
                FROM bookings b JOIN services s ON s.id = b.service_id
                WHERE b.day = ? AND b.status = 'confirmed' AND b.{col} = 0""",
            (day,),
        )
        return await cur.fetchall()


async def mark_reminded(booking_id: int, kind: str) -> None:
    col = "reminded_day" if kind == "day" else "reminded_hour"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE bookings SET {col} = 1 WHERE id = ?", (booking_id,)
        )
        await db.commit()