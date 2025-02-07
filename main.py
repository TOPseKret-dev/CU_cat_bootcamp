import asyncio
from db_controller import *
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
import time
import requests

# Ключи и токены
from keys import bot_token, folder_id, api_key


def get_answer(user_prompt):
    system_prompt = ''
    gpt_model = 'yandexgpt-lite'
    body = {
        'modelUri': f'gpt://{folder_id}/{gpt_model}',
        'completionOptions': {'stream': False, 'temperature': 0.3, 'maxTokens': 2000},
        'messages': [
            {'role': 'system', 'text': system_prompt},
            {'role': 'user', 'text': user_prompt},
        ]
    }
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {api_key}'

    }
    response = requests.post(url, headers=headers, json=body)
    operation_id = response.json().get('id')
    url = f"https://llm.api.cloud.yandex.net:443/operations/{operation_id}"
    headers = {"Authorization": f"Api-Key {api_key}"}

    while True:
        response = requests.get(url, headers=headers)
        done = response.json()["done"]
        if done:
            break
        else:
            time.sleep(1)

    data = response.json()
    answer = data['response']['alternatives'][0]['message']['text']
    return answer


async def command_start(message: Message) -> None:
    user_id = message.from_user.id
    if await is_admin(user_id):
        kb_list = [[KeyboardButton(text="Настроить ассистента")]]
        await message.answer("Привет, я твой бот-ассистент, помогу твоим студентам в обучении!",
                             reply_markup=ReplyKeyboardMarkup(keyboard=kb_list,
                                                              resize_keyboard=True,
                                                              one_time_keyboard=False))
    else:
        await message.answer("Привет, я бот-ассистент, если у тебя есть вопросы, задай их мне, и я помогу!")


async def add_admin_command(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("Только администраторы могут добавить другого администратора")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Используй: /addadmin <user_id> [username]")
        return

    try:
        new_admin_id = int(parts[1])
    except ValueError:
        await message.reply("User ID должен быть числом.")
        return

    username = parts[2] if len(parts) >= 3 else None

    await add_admin(new_admin_id, username)
    await message.reply("Новый администратор добавлен!")


async def remove_admin_command(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("Только администраторы могут удалять других администраторов")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Используй: /removeadmin <user_id>")
        return

    try:
        admin_id = int(parts[1])
    except ValueError:
        await message.reply("User ID должен быть числом.")
        return

    await remove_admin(admin_id)
    await message.reply("Администратор удалён!")


async def get_all_admins(message: Message):
    user_id = message.from_user.id
    if not await is_admin(user_id):
        await message.reply("Только администраторы могут видеть список администраторов")
        return

    admins_str = await get_admins()
    await message.reply(f"Список администраторов:\n{admins_str}")


async def main() -> None:
    dp = Dispatcher()
    dp.message.register(command_start, Command("start"))
    dp.message.register(add_admin_command, Command("addadmin"))
    dp.message.register(remove_admin, Command("removeadmin"))
    dp.message.register(get_all_admins, Command("getalladmins"))

    bot = Bot(token=bot_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
