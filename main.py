import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputFile

logging.basicConfig(level=logging.INFO)
AIOGRAM_API_TOKEN = os.environ.get("AIOGRAM_API_TOKEN")
con = sqlite3.connect("database.db")
cur = con.cursor()


bot = Bot(token=AIOGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INT PRIMARY KEY, username TEXT, languages TEXT, proficiency TEXT, methods TEXT)")

class Form(StatesGroup):
	languages = State()
	proficiency = State()
	methods = State()

@dp.message_handler(commands='start')
async def start(message: types.Message):
	await message.answer("Здравствуйте. Это бот для опроса учащихся МОБУ СОШ села Аркаулово\
		имени Баика Айдара насчет знания различных языков")
	await message.answer("Напишите, пожалуйста, все языки, которые вы когда-либо учили")

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

	async with state.proxy() as data:
		data['languages'] = message.text

	await Form.next()
	await message.answer("Насколько хорошо вы знаете каждый из языков?\
		(Надо написать про каждый язык через точку с запятой)")

@dp.message_handler(state=Form.proficiency)
async def proficiency(message: types.Message, state: FSMContext):

	async with state.proxy() as data:
		data['proficiency'] = message.text

	await Form.next()
	await message.answer("Какие методы вы используете при изучении языков?")

@dp.message_handler

@dp.message_handler()
async def echo(message: types.Message):
	await message.answer(message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
