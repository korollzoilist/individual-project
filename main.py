import logging
import os
import re
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)
AIOGRAM_API_TOKEN = "5811386673:AAE3tD2wYOMUJr3g1jmUtLIThmeGpU6VAv0" # os.environ.get("AIOGRAM_API_TOKEN")
admin_id = "658696815"
con = sqlite3.connect("database.db")
cur = con.cursor()

bot = Bot(token=AIOGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INT NOT NULL PRIMARY KEY, username TEXT NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS Languages (username TEXT NOT NULL, language TEXT NOT NULL, learning_time TEXT NOT NULL, method TEXT NOT NULL)")


class Form(StatesGroup):
    language = State()
    learning_time = State()
    method = State()


@dp.message_handler(commands='start')
async def start(message: types.Message):
	# cur.execute(f"INSERT INTO Students (username) VALUES ()")
    await message.answer("Здравствуйте. Это бот для опроса учащихся МОБУ СОШ села Аркаулово "
                         "имени Баика Айдара насчет знания различных языков")
    await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили")

    await Form.languages.set()


@dp.message_handler(state="*", commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)

    await state.finish()
    await message.reply('Отменено')


@dp.message_handler(state=Form.languages)
async def languages(message: types.Message, state: FSMContext):
    if re.findall(r"это вс[её]", message.text, re.IGNORECASE):
        async with state.proxy() as data:
            cur.execute(f"INSERT INTO Students(username, languages) "
                        f"VALUES(?, ?)", (hash(message.from_user.username), ''.join(data['languages'])))
            con.commit()
            con.close()
        await state.finish()
        await message.answer("Спасибо за участие!")

    else:
        async with state.proxy() as data:
            if 'languages' not in data.keys():
                data['languages'] = []
            data['languages'].append(message.text.replace('\n', '; '))

            await message.answer(f"Кол-во языков: {len(data['languages'])}")


@dp.message_handler()
async def echo(message: types.Message):
    await message.reply(message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
