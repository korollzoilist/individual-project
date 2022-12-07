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
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INT PRIMARY KEY, username TEXT, languages TEXT, proficiency )")

class Form(StatesGroup):
	languages = State()
	proficiency = State()
	methods = State()

@dp.message_handler()
async def echo(message: types.Message):
	await message.answer(message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
