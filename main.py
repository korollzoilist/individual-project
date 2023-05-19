import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from buttons import *


logging.basicConfig(level=logging.INFO)
AIOGRAM_API_TOKEN = os.environ.get("AIOGRAM_API_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
con = sqlite3.connect("database.db")
cur = con.cursor()
bot = Bot(token=AIOGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INTEGER PRIMARY KEY, username TEXT NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS Languages"
            "(user_name TEXT NOT NULL, language TEXT NOT NULL, learning_time TEXT NOT NULL, level TEXT NOT NULL, method TEXT NOT NULL)")


class AddLangForm(StatesGroup):
    language = State()
    learning_time = State()
    level = State()
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
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        cancel_markup.add(cancel_button)
        await message.answer("Здравствуйте. Это бот для опроса учащихся МОБУ СОШ села Аркаулово "
                             "имени Баика Айдара насчет знания различных языков\n"
                             "Вы можете в любой момент отказаться от анкеты, нажав на кнопку \"Отказаться от анкеты\"")
        await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили", reply_markup=cancel_markup)
        cur.execute(f"INSERT INTO Students (username) VALUES (\"{message.from_user.username}\")")
        await AddLangForm.language.set()


@dp.message_handler(Text(equals="Отказаться от анкеты"), state="*")
async def cancel(message: types.Message, state: FSMContext):
    cur.execute(f"DELETE FROM Students WHERE username=\"{message.from_user.username}\"")
    cur.execute(f"DELETE FROM Languages WHERE user_name=\"{message.from_user.username}\"")
    con.commit()
    await state.finish()
    await message.answer("Анкета отменена.")


@dp.message_handler(Text(equals="Отмена действия"), state="*")
async def cancel_action(message: types.Message, state: FSMContext):
    finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button, cancel_button)
    await message.answer("Действие отменено\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.finish()


@dp.message_handler(state=AddLangForm.language)
async def language(message: types.Message, state: FSMContext):
    if message.text in [''.join(lang) for lang in cur.execute(
            f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()]:
        await message.answer("Этот язык уже в списке. Напишите, пожалуйста, другой язык")
    else:
        async with state.proxy() as data:
            data['languages'] = message.text
        await message.answer("Сколько Вы учите этот язык?")
        await AddLangForm.next()


@dp.message_handler(state=AddLangForm.learning_time)
async def learning_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['learning_time'] = message.text
    await message.answer("Оцените свой уровень языка (например, начальный, средний, продвинутый)")
    await AddLangForm.next()


@dp.message_handler(state=AddLangForm.level)
async def level(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['level'] = message.text
	await message.answer("Напишите, как Вы учите язык (например, простмотр фильмов, сериалов, чтение книг и т.д.)")
	await AddLangForm.next()


@dp.message_handler(state=AddLangForm.method)
async def method(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['method'] = message.text

        cur.execute("INSERT INTO Languages (user_name, language, learning_time, level, method) VALUES"
                    f"(\"{message.from_user.username}\", \"{data['languages']}\", \"{data['learning_time']}\", "
                    f"\"{data['level']}\", \"{data['method']}\")")
    await message.answer("Весь список добавленных Вами языков:")
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\n"
        					 f"Уровень владения языком: {lang[3]}\nМетоды обучения: {lang[4]}")
    finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button, cancel_button)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.finish()


@dp.message_handler(Text(equals="Изменить данные"))
async def change_data(message: types.Message):
    langs_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    langs = cur.execute(f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        langs_markup.add(KeyboardButton(lang[0]))
    langs_markup.add(cancel_action_button, cancel_button)
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
            KeyboardButton("Название языка"), KeyboardButton("Время изучения"), KeyboardButton("Метод изучения"),
            KeyboardButton("Уровень владения языком"), cancel_action_button, cancel_button)
        async with state.proxy() as data:
            data['language'] = message.text
        await message.answer("Какие данные Вы хотите изменить?", reply_markup=data_markup)
        await ChangeLangForm.next()


@dp.message_handler(Text(equals=["Название языка", "Время изучения", "Уровень владения языком", "Метод изучения"]),
                    state=ChangeLangForm.what_to_change)
async def change_data_3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['what_to_change'] = message.text
    cancel_action_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_action_markup.add(cancel_action_button, cancel_button)
    await message.answer(f"Напишите новые данные про {message.text.lower()}", reply_markup=cancel_action_markup)
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
        elif data['what_to_change'] == "Уровень владения языком":
        	cur.execute(f"UPDATE Languages SET level=\"{message.text}\""
        				f"WHERE language=\"{data['language']}\" AND user_name=\"{message.from_user.username}\"")
        elif data['what_to_change'] == "Метод изучения":
            cur.execute(f"UPDATE Languages SET method=\"{message.text}\" "
                        f"WHERE language=\"{data['language']}\" AND user_name=\"{message.from_user.username}\"")
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\n"
        					 f"Методы оучения: {lang[3]}")
    finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button, cancel_button)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.finish()


@dp.message_handler(Text(equals="Добавить язык"))
async def add_another_language(message: types.Message):
    cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(cancel_action_button, cancel_button)
    await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили",
                         reply_markup=cancel_markup)
    await AddLangForm.language.set()


@dp.message_handler(Text(equals="Удалить язык"))
async def delete(message: types.Message):
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    if langs:
        delete_langs_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for lang in langs:
            delete_langs_markup.add(lang[1])
        delete_langs_markup.add(cancel_action_button, cancel_button)
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
        finish_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        finish_markup.add(change_data_button, add_lang_button, finish_button, remove_button, cancel_button)
        await message.answer("Данные успешно обновлены\n"
                             "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                             reply_markup=finish_markup)
        await state.finish()


@dp.message_handler(Text(equals="Закончить анкету"))
async def finish(message: types.Message):
    await message.answer("Спасибо за участие в анкете!", reply_markup=ReplyKeyboardRemove())
    con.commit()
    people_count = len(cur.execute("SELECT ID FROM Students").fetchall())
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{message.from_user.username} заполнил(а) анкету:"
                                                       f"\nОбщее число заполнивших анкету: {people_count}")
    await bot.send_document(chat_id=ADMIN_CHAT_ID, document=InputFile("database.db"))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
