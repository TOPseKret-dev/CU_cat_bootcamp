import aiosqlite


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

