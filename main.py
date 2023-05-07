import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile

logging.basicConfig(level=logging.INFO)
AIOGRAM_API_TOKEN = os.environ.get("AIOGRAM_API_TOKEN")
admin_id = "658696815"
con = sqlite3.connect("database.db")
cur = con.cursor()

bot = Bot(token=AIOGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INTEGER PRIMARY KEY, username TEXT NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS Languages"
            "(user_name TEXT NOT NULL, language TEXT NOT NULL, learning_time TEXT NOT NULL, method TEXT NOT NULL)")


class Form(StatesGroup):
    language = State()
    learning_time = State()
    method = State()


class ChangeLangForm(StatesGroup):
    language = State()
    what_to_change = State()
    change_info = State()


class DeleteLangForm(StatesGroup):
    language = State()


@dp.message_handler(commands='start')
async def start(message: types.Message):
    if message.from_user.username in [''.join(user) for user in cur.execute("SELECT username FROM Students")]:
        await message.answer("Анкета закончена")
    else:
        await message.answer("Здравствуйте. Это бот для опроса учащихся МОБУ СОШ села Аркаулово "
                             "имени Баика Айдара насчет знания различных языков")
        await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили")
        cur.execute(f"INSERT INTO Students (username) VALUES (\"{message.from_user.username}\")")
        await Form.language.set()


@dp.message_handler(state="*", commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)

    cur.execute(f"DELETE FROM Students WHERE username=\"{message.from_user.username}\"")

    await state.finish()
    await message.answer('Отменено')


@dp.message_handler(state=Form.language)
async def language(message: types.Message, state: FSMContext):
    if message.text in [''.join(lang) for lang in cur.execute(
            f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()]:
        await message.answer("Этот язык уже в списке. Напишите, пожалуйста, другой язык")
    else:
        async with state.proxy() as data:
            data['languages'] = message.text
        await message.answer("Сколько Вы учите этот язык?")
        await Form.next()


@dp.message_handler(state=Form.learning_time)
async def learning_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['learning_time'] = message.text

    await message.answer("Напишите, как Вы учите язык (например, простмотр фильмов, сериалов, чтение книг и т.д.)")

    await Form.next()


@dp.message_handler(state=Form.method)
async def method(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['method'] = message.text

        cur.execute("INSERT INTO Languages (user_name, language, learning_time, method) VALUES"
                    f"(\"{message.from_user.username}\", \"{data['languages']}\", \"{data['learning_time']}\", "
                    f"\"{data['method']}\")")

    await message.answer("Вот ваш(и) язык(и):")
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\nМетоды обучения: {lang[3]}")
    change_data_button = KeyboardButton("Изменить данные")
    add_lang_button = KeyboardButton("Добавить язык")
    finish_button = KeyboardButton("Закончить анкету")
    remove_button = KeyboardButton("Удалить язык")
    finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.finish()


@dp.message_handler(lambda message: message.text == "Изменить данные")
async def change_data(message: types.Message):
    langs_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    langs = cur.execute(f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        langs_markup.add(KeyboardButton(lang[0]))
    await message.answer("Какой язык Вы хотите изменить?", reply_markup=langs_markup)
    await ChangeLangForm.language.set()


@dp.message_handler(state=ChangeLangForm.language)
async def change_data_2(message: types.Message, state: FSMContext):
    if message.text not in [''.join(lang) for lang in cur.execute(
                        f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()]:
        await message.answer("Такого языка нет среди записанных Вами языков. "
                             "Может, Вы неправильно написали или перепутали язык?")
    elif not cur.execute(f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\""):
        await message.answer("В списке нет ни одного языка. Добавьте как минимум один язык")
    else:
        data_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        data_markup.add(
            KeyboardButton("Название языка"), KeyboardButton("Время изучения"), KeyboardButton("Метод изучения"))
        async with state.proxy() as data:
            data['language'] = message.text
        await message.answer("Какие данные Вы хотите изменить?", reply_markup=data_markup)
        await ChangeLangForm.next()


@dp.message_handler(lambda message: message.text == "Название языка"
                    or message.text == "Время изучения" or message.text == "Метод изучения",
                    state=ChangeLangForm.what_to_change)
async def change_data_3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['what_to_change'] = message.text
    await message.answer(f"Напишите новые данные про {message.text.lower()}")
    await ChangeLangForm.next()


@dp.message_handler(state=ChangeLangForm.change_info)
async def change_data_4(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['what_to_change'] == "Название языка":
            cur.execute(f"UPDATE Languages SET language=\"{message.text}\" "
                        f"WHERE language=\"{data['language']}\" AND user_name=\"{message.from_user.username}\"")
        elif data['what_to_change'] == "Время изучения":
            cur.execute(f"UPDATE Languages SET learning_time=\"{message.text}\" "
                        f"WHERE language=\"{data['language']}\" AND user_name=\"{message.from_user.username}\"")
        elif data['what_to_change'] == "Метод изучения":
            cur.execute(f"UPDATE Languages SET method=\"{message.text}\" "
                        f"WHERE language=\"{data['language']}\" AND user_name=\"{message.from_user.username}\"")
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\nМетоды обучения: {lang[3]}")
    change_data_button = KeyboardButton("Изменить данные")
    add_lang_button = KeyboardButton("Добавить язык")
    finish_button = KeyboardButton("Закончить анкету")
    remove_button = KeyboardButton("Удалить язык")
    finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.finish()


@dp.message_handler(lambda message: message.text == "Добавить язык")
async def add_another_language(message: types.Message):
    await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили")
    await Form.language.set()


@dp.message_handler(lambda message: message.text == "Удалить язык")
async def delete(message: types.Message):
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    if langs:
        delete_langs_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for lang in langs:
            delete_langs_markup.add(lang[1])
        await DeleteLangForm.language.set()
        await message.answer("Какой язык Вы хотите удалить из списка?", reply_markup=delete_langs_markup)
    else:
        await message.answer("Список языков уже пуст")


@dp.message_handler(state=DeleteLangForm.language)
async def delete_2(message: types.Message, state: FSMContext):
    if message.text.lower() not in [''.join(lang).lower() for lang in cur.execute(
            f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"")]:
        await message.answer("Такого языка нет среди записанных Вами языков. "
                             "Может, Вы неправильно написали или перепутали язык?")
    else:
        cur.execute(
            f"DELETE FROM Languages WHERE user_name=\"{message.from_user.username}\" AND language=\"{message.text}\"")
        langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
        if langs:
            for lang in langs:
                await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\nМетоды обучения: {lang[3]}")
        else:
            await message.answer("Языков нет")
        change_data_button = KeyboardButton("Изменить данные")
        add_lang_button = KeyboardButton("Добавить язык")
        finish_button = KeyboardButton("Закончить анкету")
        remove_button = KeyboardButton("Удалить язык")
        finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button)
        await message.answer("Данные успешно обновлены\n"
                             "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                             reply_markup=finish_markup)
        await state.finish()


@dp.message_handler(lambda message: message.text == "Закончить анкету")
async def finish(message: types.Message):
    await message.answer("Спасибо за участие в анкете!")
    con.commit()
    await bot.send_message(chat_id=658696815, text=f"{message.from_user.username} заполнил анкету:")
    await bot.send_document(chat_id=658696815, document=InputFile("database.db"))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
