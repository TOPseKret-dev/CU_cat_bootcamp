import asyncio
import time
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from db_controller import *
from keys import bot_token, folder_id, api_key, domen


class Form(StatesGroup):
    """
    Класс состояний для взаимодействия с пользователем.
    """
    waiting_for_settings = State()


async def get_answer(user_prompt: str, user_id: int, context_messages: list = None) -> str:
    """
    Отправка запроса к Yandex GPT API и получение ответа.

    :param user_prompt: Введенный пользователем запрос.
    :param user_id: Идентификатор пользователя.
    :param context_messages: История сообщений (опционально).
    :return: Ответ от модели ИИ.
    """
    admin = await is_admin(user_id)
    admin_role = "преподаватель" if admin else "студент"
    system_prompt = await get_system_prompt()

    messages = [{
        'role': 'system',
        'text': (
            f"Вы - ассистент преподавателей. "
            f"Ваш собеседник - {admin_role}. "
            f"Текущие настройки: {system_prompt}"
        )
    }]

    if context_messages:
        messages.extend(context_messages)
    messages.append({'role': 'user', 'text': user_prompt})

    body = {
        'modelUri': f'gpt://{folder_id}/yandexgpt',
        'completionOptions': {'stream': False, 'temperature': 0.3, 'maxTokens': 2000},
        'messages': messages
    }

    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Api-Key {api_key}'}
    response = requests.post(url, headers=headers, json=body)
    operation_id = response.json().get('id')

    while True:
        response = requests.get(f"https://llm.api.cloud.yandex.net:443/operations/{operation_id}", headers=headers)
        if response.json().get("done", False):
            break
        await asyncio.sleep(1)

    return response.json()['response']['alternatives'][0]['message']['text']


async def handle_configure_assistant(message: Message, state: FSMContext):
    """
    Запросить у пользователя настройки ассистента.
    """
    await message.answer("Введите настройки ассистента:")
    await state.set_state(Form.waiting_for_settings)


async def save_assistant_settings(message: Message, state: FSMContext):
    """
    Сохранение пользовательских настроек ассистента.
    """
    await update_system_prompt(message.text)
    await message.answer("Настройки успешно сохранены!")
    await state.clear()


async def command_start(message: Message) -> None:
    """
    Обработчик команды /start.
    """
    user_id = message.from_user.id
    web_app_url = f"{domen}/?user_id={user_id}"
    if await is_admin(user_id):
        kb_list = [[KeyboardButton(text="Настроить ассистента"),
                    KeyboardButton(text="Добавить событие", web_app=WebAppInfo(url=web_app_url))]]
        await message.answer("Привет! Я бот-ассистент для преподавателей.",
                             reply_markup=ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True))
    else:
        await message.answer("Привет! Чем могу помочь?")


async def reminder_loop(bot: Bot):
    """
    Фоновый процесс для отправки напоминаний пользователям.
    """
    while True:
        now = int(time.time())
        async with aiosqlite.connect("database.db") as conn:
            async with conn.execute(
                    "SELECT id, user_id, event_text FROM events WHERE reminder_time <= ? AND notified = 0",
                    (now,)) as cursor:
                events = await cursor.fetchall()
            for event in events:
                event_id, user_id, event_text = event
                try:
                    await bot.send_message(user_id, f"Напоминание: {event_text}")
                except Exception as e:
                    print(f"Ошибка при отправке напоминания: {e}")
                await conn.execute("UPDATE events SET notified = 1 WHERE id = ?", (event_id,))
            await conn.commit()
        await asyncio.sleep(60)


async def main() -> None:
    """
    Запуск бота и процессов обработки сообщений.
    """
    await init_db()
    dp = Dispatcher()
    dp.message.register(command_start, Command("start"))
    dp.message.register(handle_configure_assistant, F.text == "Настроить ассистента")
    dp.message.register(save_assistant_settings, Form.waiting_for_settings)

    bot = Bot(token=bot_token)
    asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
