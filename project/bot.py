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
    waiting_for_settings = State()


async def get_answer(user_prompt: str, user_id: int, context_messages: list = None) -> str:
    admin = await is_admin(user_id)
    admin_role = "преподаватель" if admin else "студент"
    system_prompt = await get_system_prompt()

    messages = await get_user_context(user_id)
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

    answer = response.json()['response']['alternatives'][0]['message']['text']
    await save_message(user_id, 'user', user_prompt)
    await save_message(user_id, 'assistant', answer)
    return answer


async def handle_message(message: Message):
    user_id = message.from_user.id
    response = await get_answer(message.text, user_id)
    await message.answer(response)


async def command_start(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    web_app_url = f"{domen}/?user_id={user_id}"
    sticker_pack_url = "https://t.me/addstickers/CUCat9"
    sticker_id = "CAACAgIAAxkBAAENveZnp1O-zUx4LJ6ziZeqXGXLxoHBhAACV2AAAuAgOElpliPYfQViXDYE"

    if await is_admin(user_id):
        kb_list = [[KeyboardButton(text="Настроить ассистента"),
                    KeyboardButton(text="Добавить событие", web_app=WebAppInfo(url=web_app_url))]]
        await message.answer(
            "Привет! Я бот-ассистент для преподавателей.\n\n"
            f"Также у нас есть стикерпак, посмотри: {sticker_pack_url}",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
        )
    else:
        await message.answer(
            "Привет! Чем могу помочь?\n\n"
            f"Также у нас есть стикерпак, посмотри: {sticker_pack_url}"
        )
    await bot.send_sticker(chat_id=message.chat.id, sticker=sticker_id)


async def main() -> None:
    await init_db()
    dp = Dispatcher()
    dp.message.register(command_start, Command("start"))
    dp.message.register(handle_message)

    bot = Bot(token=bot_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
