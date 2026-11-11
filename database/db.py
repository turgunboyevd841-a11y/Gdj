import aiosqlite

from config import config

DB_PATH = config.db_path


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                full_name   TEXT,
                username    TEXT,
                phone       TEXT,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS services (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                price       INTEGER NOT NULL,
                is_active   INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                service_id  INTEGER NOT NULL,
                day         TEXT NOT NULL,      -- 2026-11-12
                time        TEXT NOT NULL,      -- 14:00
                name        TEXT NOT NULL,
                phone       TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',  -- pending / confirmed / cancelled
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            );

            -- Bir vaqtga ikkita faol yozilishni oldini oladi
            CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_slot
                ON bookings(day, time)
                WHERE status != 'cancelled';
            """
        )
        await db.commit()

        # Xizmatlar bo'sh bo'lsa, boshlang'ich ma'lumotlarni qo'shamiz
        cur = await db.execute("SELECT COUNT(*) FROM services")
        (count,) = await cur.fetchone()
        if count == 0:
            await db.executemany(
                "INSERT INTO services (name, price) VALUES (?, ?)",
                [
                    ("💇‍♀️ Soch turmaklash", 80_000),
                    ("🎨 Soch bo'yash", 250_000),
                    ("💅 Manikyur", 70_000),
                    ("🦶 Pedikyur", 90_000),
                    ("💄 Makiyaj", 200_000),
                ],
            )
            await db.commit()


        # Eslatma belgilari (eski bazani buzmasdan qo'shiladi)
        for col in ("reminded_day", "reminded_hour"):
            try:
                await db.execute(
                    f"ALTER TABLE bookings ADD COLUMN {col} INTEGER DEFAULT 0"
                )
                await db.commit()
            except aiosqlite.OperationalError:
                pass   # ustun allaqachon bor