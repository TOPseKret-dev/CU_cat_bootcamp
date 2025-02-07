import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db_controller import *
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
import time
import requests

# Ключи и токены
from keys import bot_token, folder_id, api_key, domen


async def get_answer(user_prompt, id):
    admin = await is_admin(id)
    system_prompt = await get_system_prompt()  # Ждём завершения асинхронной функции
    print(system_prompt)
    gpt_model = 'yandexgpt-lite'
    body = {
        'modelUri': f'gpt://{folder_id}/{gpt_model}',
        'completionOptions': {'stream': False, 'temperature': 0.3, 'maxTokens': 2000},
        'messages': [
            {'role': 'system', 'text':
                '''Представьте, что вы ИИ-ассистент, созданный для помощи преподавателям в снижении нагрузки. Ваша 
                задача — автоматизировать рутинные задачи, такие как проверка домашних заданий, составление тестов, 
                ответы на вопросы студентов и создание учебных материалов. Начните с приветствия и предложения 
                выбрать курсы, для которых будет использоваться ассистент. Преподаватель должен указать названия 
                курсов через запятую. Затем попросите его определить типы задач, которые он хотел бы делегировать 
                вам, выбрав из следующих вариантов: проверка домашних заданий, составление тестов, ответы на вопросы 
                студентов, создание учебных материалов.
                
Так же уточни, что для твоей настройки нужно нажать на кнопку "настроить ассистента"

Возможно далее будет указана настройка критериев оценки и параметров проверки для каждой выбранной задачи. Например, 
для проверки домашних заданий могут быть указаны такие критерии, как правильность ответов, оригинальность текста, 
соблюдение требований к оформлению, а также максимальное количество баллов.

Далее настройка параметры для составления тестов: количество вопросов, время на прохождение теста и сложность 
вопросов (легкие, средние, сложные). Если преподаватель выбрал задачу "ответы на вопросы студентов", уточните, 
какие темы и форматы вопросов он ожидает.
Дальнейший текст был отправлен преподавателем, следуй его инструкциям: '''
                + system_prompt + "преподу ты должен помогать в настройке самого себя и распределению его задач, "
                                  "а студентам должен помогать по темам, описанным преподом. Если далее написано "
                                  "True, то перед тобой препод, иначе студент и ты должен общаться соответствующе"
             + str(admin)},
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
        await asyncio.sleep(1)  # Используем await вместо time.sleep(1)

    data = response.json()
    answer = data['response']['alternatives'][0]['message']['text']
    return answer


class Form(StatesGroup):
    waiting_for_settings = State()


async def handle_configure_assistant(message: Message, state: FSMContext):
    await message.answer(f'''Здравствуйте, {message.from_user.username}!

Для эффективной настройки ИИ-ассистента, который поможет вам в работе со студентами, нам необходимо уточнить несколько деталей. Это позволит адаптировать систему под ваши нужды и сделать её максимально удобной и полезной.

Пожалуйста, предоставьте следующую информацию:

1. Курсы, на которых будет использоваться ассистент
Перечислите названия курсов и укажите их специфику. Например:

Для какого уровня обучения предназначен курс (бакалавриат, магистратура, дополнительное образование и т. д.).
Какая основная цель курса (изучение теории, освоение практических навыков, проектная работа и т. д.).


2. Типы задач, которые ассистент должен выполнять
Определите, какие функции вы хотите поручить ассистенту. Возможные варианты:

Проверка домашних заданий (автоматическая оценка, выдача обратной связи, выявление ошибок).
Составление тестов (генерация вопросов по материалу курса, проверка знаний студентов).
Ответы на вопросы студентов (объяснение теоретических аспектов, предоставление справочной информации, помощь с заданиями).
Создание учебных материалов (подготовка конспектов, резюме лекций, объясняющих схем и таблиц).
Вы можете указать несколько задач, которые ассистент будет выполнять параллельно.


3. Критерии оценки домашних заданий
Если ассистенту предстоит проверять работы студентов, уточните, какие параметры оценки для вас важны. Например:

Правильность ответов – должно ли задание оцениваться по четкому списку верных решений?
Оригинальность текста – требуется ли проверка на заимствования и плагиат?
Соблюдение требований к оформлению – учитывать ли форматирование, стиль и структуру работы?
Максимальный балл – сколько баллов можно получить за каждое задание и какие шкалы оценивания использовать?


4. Параметры тестов
Если ассистент будет создавать тесты, уточните, какие настройки важны:

Количество вопросов в одном тесте.
Типы вопросов (множественный выбор, открытые вопросы, соответствия и т. д.).
Время на прохождение – будет ли установлен лимит?
Уровень сложности – задания базового, среднего или продвинутого уровня.


5. Интеграция с другими системами (данная функция находится в разработке)
Если вам требуется, чтобы ассистент работал совместно с другими платформами, уточните:

Нужно ли подключение к личному кабинету студентов?
Поддерживается ли интеграция с вашей LMS (Learning Management System)?
Должен ли ассистент учитывать расписание занятий и дедлайны?


6. Способы получения уведомлений (данная функция находится в разработке)
Каким способом вам удобнее получать оповещения от ассистента? Например:

Email – уведомления о новых заданиях, проверенных работах, вопросах студентов.
Внутренние сообщения в LMS – если ассистент интегрируется с платформой.
Телеграм-бот или другой мессенджер – если вам удобен быстрый доступ к информации.
Дополнительные пожелания
Если у вас есть особые требования или идеи, как можно улучшить работу ассистента, сообщите нам. Мы постараемся учесть все нюансы, чтобы система соответствовала вашим ожиданиям.

Спасибо за предоставленную информацию! Это поможет сделать ИИ-ассистента полезным инструментом для вас и ваших студентов.''')
    await state.set_state(Form.waiting_for_settings)


async def save_assistant_settings(message: Message, state: FSMContext):
    settings_text = message.text
    await update_system_prompt(settings_text)
    await message.answer("Настройки ассистента успешно сохранены!")
    await state.clear()


async def command_start(message: Message) -> None:
    user_id = message.from_user.id
    web_app_url = f"https://{domen}/?user_id={user_id}"
    if await is_admin(user_id):
        kb_list = [[KeyboardButton(text="Настроить ассистента"),
                    KeyboardButton(text="Добавить событие", web_app=WebAppInfo(url=web_app_url))]]
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


async def reminder_loop(bot: Bot):
    while True:
        now = int(time.time())
        async with aiosqlite.connect("database.db") as conn:
            async with conn.execute(
                    "SELECT id, user_id, event_text FROM events WHERE reminder_time <= ? AND notified = 0",
                    (now,)
            ) as cursor:
                events = await cursor.fetchall()
            for event in events:
                event_id, user_id, event_text = event
                try:
                    await bot.send_message(user_id, f"Напоминание: {event_text}")
                except Exception as e:
                    print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")
                await conn.execute("UPDATE events SET notified = 1 WHERE id = ?", (event_id,))
            await conn.commit()
        await asyncio.sleep(60)


async def handle_other_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.waiting_for_settings.state:
        await save_assistant_settings(message, state)
    else:
        user_text = message.text
        ai_response = await get_answer(user_text, message.from_user.id)
        await message.answer(ai_response)


async def main() -> None:
    await init_db()
    dp = Dispatcher()
    dp.message.register(command_start, Command("start"))
    dp.message.register(add_admin_command, Command("addadmin"))
    dp.message.register(remove_admin, Command("removeadmin"))
    dp.message.register(get_all_admins, Command("getalladmins"))
    dp.message.register(handle_configure_assistant, F.text == "Настроить ассистента")
    dp.message.register(save_assistant_settings, Form.waiting_for_settings)
    dp.message.register(handle_other_messages)

    bot = Bot(token=bot_token)
    # await asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
