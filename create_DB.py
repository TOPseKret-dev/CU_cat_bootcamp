import aiosqlite
import asyncio


async def create_db():
    async with aiosqlite.connect("project/database.db") as db:
        await db.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        event_text TEXT NOT NULL,
                        event_time INTEGER NOT NULL,
                        reminder_time INTEGER NOT NULL,
                        notified INTEGER DEFAULT 0
                    )
                ''')
        await db.execute('''
                        CREATE TABLE IF NOT EXISTS admins (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER UNIQUE NOT NULL,
                            username TEXT
                        );
                        ''')
        await db.execute('''
                            CREATE TABLE IF NOT EXISTS assistant_settings (
                                settings_text TEXT NOT NULL
                            )
                        ''')
        await db.commit()
    print("База данных успешно создана!")

if __name__ == "__main__":
    asyncio.run(create_db())
