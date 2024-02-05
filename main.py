import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, FSInputFile
from buttons import (change_data_button, add_lang_button, finish_button, remove_button, cancel_action_button,
                     cancel_button)

logging.basicConfig(level=logging.INFO)
AIOGRAM_API_TOKEN = os.environ.get("AIOGRAM_API_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
con = sqlite3.connect("database.db")
cur = con.cursor()
bot = Bot(token=AIOGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
cur.execute("CREATE TABLE IF NOT EXISTS Students (ID INTEGER PRIMARY KEY, username TEXT NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS Languages"
            "(user_name TEXT NOT NULL, language TEXT NOT NULL, learning_time TEXT NOT NULL, level TEXT NOT NULL, "
            "method TEXT NOT NULL)")


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


@dp.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    if message.from_user.username in [''.join(user) for user in cur.execute("SELECT username FROM Students")]:
        await message.answer("Анкета закончена")
    else:
        kb = [[cancel_button]]
        cancel_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Здравствуйте. Это бот для опроса учащихся МОБУ СОШ села Аркаулово "
                             "имени Баика Айдара насчет знания различных языков\n"
                             "Вы можете в любой момент отказаться от анкеты, нажав на кнопку \"Отказаться от анкеты\"")
        await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили", reply_markup=cancel_markup)
        cur.execute(f"INSERT INTO Students (username) VALUES (\"{message.from_user.username}\")")
        await state.set_state(AddLangForm.language)


@dp.message(F.text == "Отказаться от анкеты")
async def cancel(message: types.Message, state: FSMContext):
    cur.execute(f"DELETE FROM Students WHERE username=\"{message.from_user.username}\"")
    cur.execute(f"DELETE FROM Languages WHERE user_name=\"{message.from_user.username}\"")
    con.commit()
    await state.clear()
    await message.answer("Анкета отменена.")


@dp.message(F.text == "Отмена действия")
async def cancel_action(message: types.Message, state: FSMContext):
    kb = [[change_data_button, add_lang_button, finish_button, remove_button, cancel_button]]
    finish_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Действие отменено\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.clear()


@dp.message(AddLangForm.language)
async def language(message: types.Message, state: FSMContext):
    if message.text in [''.join(lang) for lang in cur.execute(
            f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()]:
        await message.answer("Этот язык уже в списке. Напишите, пожалуйста, другой язык")
    else:
        await state.update_data(languages=message.text)
        await message.answer("Сколько Вы учите этот язык?")
        await state.set_state(AddLangForm.learning_time)


@dp.message(AddLangForm.learning_time)
async def learning_time(message: types.Message, state: FSMContext):
    await state.update_data(learning_time=message.text)
    await message.answer("Оцените свой уровень языка (например, начальный, средний, продвинутый)")
    await state.set_state(AddLangForm.level)


@dp.message(AddLangForm.level)
async def level(message: types.Message, state: FSMContext):
    await state.update_data(level=message.text)
    await message.answer("Напишите, как Вы учите язык (например, просмотр фильмов, сериалов, чтение книг и т.д.)")
    await state.set_state(AddLangForm.method)


@dp.message(AddLangForm.method)
async def method(message: types.Message, state: FSMContext):
    data = await state.update_data(method=message.text)

    cur.execute("INSERT INTO Languages (user_name, language, learning_time, level, method) VALUES"
                f"(\"{message.from_user.username}\", \"{data['languages']}\", \"{data['learning_time']}\", "
                f"\"{data['level']}\", \"{data['method']}\")")
    await message.answer("Весь список добавленных Вами языков:")
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    for lang in langs:
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\n"
                             f"Уровень владения языком: {lang[3]}\nМетоды обучения: {lang[4]}")
    kb = [[change_data_button, add_lang_button, finish_button, remove_button, cancel_button]]
    finish_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.clear()


@dp.message(F.text == "Изменить данные")
async def change_data(message: types.Message, state: FSMContext):
    langs = cur.execute(f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    kb = []
    for lang in langs:
        kb.append(KeyboardButton(text=lang[0]))

    kb.append(cancel_action_button)
    kb.append(cancel_button)
    kb = [kb]
    langs_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Какой язык Вы хотите изменить?", reply_markup=langs_markup)
    await state.set_state(ChangeLangForm.language)


@dp.message(ChangeLangForm.language)
async def change_data_2(message: types.Message, state: FSMContext):
    if message.text not in [''.join(lang) for lang in cur.execute(
            f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()]:
        await message.answer("Такого языка нет среди записанных Вами языков. "
                             "Может, Вы неправильно написали или перепутали язык?")
    elif not cur.execute(f"SELECT language FROM Languages WHERE user_name=\"{message.from_user.username}\""):
        await message.answer("В списке нет ни одного языка. Добавьте как минимум один язык")
    else:
        kb = [[
            KeyboardButton(text="Название языка"), KeyboardButton(text="Время изучения"),
            KeyboardButton(text="Метод изучения"), KeyboardButton(text="Уровень владения языком"), cancel_action_button,
            cancel_button]]
        data_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        await state.update_data(language=message.text)
        await message.answer("Какие данные Вы хотите изменить?", reply_markup=data_markup)
        await state.set_state(ChangeLangForm.what_to_change)


@dp.message(F.text.in_({"Название языка", "Время изучения", "Уровень владения языком", "Метод изучения"}),
            ChangeLangForm.what_to_change)
async def change_data_3(message: types.Message, state: FSMContext):
    await state.update_data(what_to_change=message.text)
    kb = [[cancel_action_button, cancel_button]]
    cancel_action_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer(f"Напишите новые данные про {message.text.lower()}", reply_markup=cancel_action_markup)
    await state.set_state(ChangeLangForm.change_info)


@dp.message(ChangeLangForm.change_info)
async def change_data_4(message: types.Message, state: FSMContext):
    data = await state.get_data()
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
        await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\nУровень владения языком: {lang[3]}\n"
                             f"Методы обучения: {lang[4]}")
    kb = [[change_data_button, add_lang_button, finish_button, remove_button, cancel_button]]
    finish_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Данные успешно обновлены\n"
                         "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                         reply_markup=finish_markup)
    await state.clear()


@dp.message(F.text == "Добавить язык")
async def add_another_language(message: types.Message, state: FSMContext):
    kb = [[cancel_action_button, cancel_button]]
    cancel_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Напишите, пожалуйста, язык, который Вы учите/учили",
                         reply_markup=cancel_markup)
    await state.set_state(AddLangForm.language)


@dp.message(F.text == "Удалить язык")
async def delete(message: types.Message, state: FSMContext):
    langs = cur.execute(f"SELECT * FROM Languages WHERE user_name=\"{message.from_user.username}\"").fetchall()
    if langs:
        kb = []
        for lang in langs:
            kb.append(lang[1])
        kb.append(cancel_action_button)
        kb.append(cancel_button)
        kb = [kb]
        delete_langs_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        await state.set_state(DeleteLangForm.language)
        await message.answer("Какой язык Вы хотите удалить из списка?", reply_markup=delete_langs_markup)
    else:
        await message.answer("Список языков уже пуст")


@dp.message(DeleteLangForm.language)
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
                await message.answer(f"Язык: {lang[1]}\nВремя обучения: {lang[2]}\nУровень владения языком: {lang[3]}\n"
                                     f"Методы обучения: {lang[4]}")
        else:
            await message.answer("Языков нет")
        kb = [[change_data_button, add_lang_button, finish_button, remove_button, cancel_button]]
        finish_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Данные успешно обновлены\n"
                             "Хотите изменить данные, добавить ещё один язык, удалить язык или закончить анкету?",
                             reply_markup=finish_markup)
        await state.clear()


@dp.message(F.text == "Закончить анкету")
async def finish(message: types.Message):
    await message.answer("Спасибо за участие в анкете!", reply_markup=ReplyKeyboardRemove())
    con.commit()
    people_count = len(cur.execute("SELECT ID FROM Students").fetchall())
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{message.from_user.username} заполнил(а) анкету:"
                                                       f"\nОбщее число заполнивших анкету: {people_count}")
    await bot.send_document(chat_id=ADMIN_CHAT_ID, document=FSInputFile("database.db"))


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
