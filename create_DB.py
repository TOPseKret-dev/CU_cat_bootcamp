import aiosqlite
import asyncio


async def create_db():
    async with aiosqlite.connect("project/database.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT
        );
        """)
        await db.commit()
    print("База данных успешно создана!")

if __name__ == "__main__":
    asyncio.run(create_db())
