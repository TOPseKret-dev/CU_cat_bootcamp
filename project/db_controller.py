import aiosqlite

DATABASE = "database.db"


async def init_db():
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_text TEXT NOT NULL,
                event_time INTEGER NOT NULL,
                reminder_time INTEGER NOT NULL,
                notified INTEGER DEFAULT 0
            )
        ''')
        await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT
                );
                ''')
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS global_settings (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        system_prompt TEXT NOT NULL DEFAULT ''
                    )
                ''')
        # Инициализируем дефолтную запись
        await conn.execute('''
                    INSERT OR IGNORE INTO global_settings (id, system_prompt) 
                    VALUES (1, '')
                ''')
        await conn.commit()


async def add_event(user_id, event_text, event_time, reminder_time):
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute(
            "INSERT INTO events (user_id, event_text, event_time, reminder_time) VALUES (?, ?, ?, ?)",
            (user_id, event_text, event_time, reminder_time)
        )
        await conn.commit()


async def get_events():
    async with aiosqlite.connect(DATABASE) as conn:
        async with conn.execute("SELECT * FROM events") as cursor:
            rows = await cursor.fetchall()
            return rows


async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def add_admin(user_id: int, username: str = None):
    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()


async def remove_admin(user_id: int):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_admins() -> str:
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT user_id, username FROM admins") as cursor:
            admins = await cursor.fetchall()

    if not admins:
        return "Админов нет"

    formatted_lines = []
    for user_id, username in admins:
        name = username if username else "не указан"
        formatted_lines.append(f"ID: {user_id} | Username: {name}")

    return "\n".join(formatted_lines)


async def update_system_prompt(prompt_text: str):
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute('''
            INSERT OR REPLACE INTO global_settings (id, system_prompt)
            VALUES (1, ?)
        ''', (prompt_text,))
        await conn.commit()


async def get_system_prompt() -> str:
    async with aiosqlite.connect(DATABASE) as conn:
        async with conn.execute('''
            SELECT system_prompt FROM global_settings WHERE id = 1
        ''') as cursor:
            result = await cursor.fetchone()
            return result[0] if result else ""
