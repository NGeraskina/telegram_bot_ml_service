import asyncio
import json
import logging
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from magic_filter import F
from typing import Optional
from aiogram.filters.callback_data import CallbackData

# from config_reader import config

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# bot = Bot(token=config.bot_token.get_secret_value())
bot = Bot(token='6961024788:AAF6TeMDf-suyWIQDjujs7o51b_lCf8nmgI')
# Диспетчер
dp = Dispatcher()


class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int] = None

json_file = 'feedback_ratings.json'

# Load existing feedback ratings from file
try:
    with open(json_file, 'r') as file:
        feedback_ratings = json.load(file)
except FileNotFoundError:
    feedback_ratings = {}

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in feedback_ratings:
        feedback_ratings[user_id] = {}
    await message.answer(
        "Приветствую! Тут вы можете подать на вход несколько данных о пользователе и получить предсказание")


@dp.message(Command("help"))
async def cmd_special_buttons(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # метод row позволяет явным образом сформировать ряд
    # из одной или нескольких кнопок. Например, первый ряд
    # будет состоять из двух кнопок...
    builder.row(
        types.KeyboardButton(text="Сделать предсказание"),
    )
    builder.row(types.KeyboardButton(
        text="Оценить работу сервиса")
    )
    builder.row(types.KeyboardButton(
        text="Вывести статистику по сервису")
    )

    await message.answer(
        "Выберите действие:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message(F.text.lower() == "оценить работу сервиса")
async def feedback(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for i in range(1, 6):
        builder.add(types.KeyboardButton(text=str(i), callback_data=i))
    builder.adjust(5)
    await message.answer(
        "Насколько вам понравилась работа телеграм бота?",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message(lambda message: message.text.isdigit() and 1 <= int(message.text) <= 5)
async def callbacks_num_change_fab(message: types.Message):
    user_id = message.from_user.id
    timestamp = int(time.time())
    rating = message.text

    # Save the feedback in the dictionary

    feedback_ratings[user_id][timestamp] = rating
    print(feedback_ratings)

    # Save the feedback dictionary to the JSON file
    with open(json_file, 'w') as file:
        json.dump(feedback_ratings, file)
    await message.answer("Благодарю за отзыв!")


@dp.message(F.text.lower() == "вывести статистику по сервису")
async def feedback_stats(message: types.Message):
    with open(json_file, 'r') as file:
        feedback_ratings = json.load(file)
    print(feedback_ratings)
    n = 0
    summ = 0
    users = []
    for i in feedback_ratings:
        for j in feedback_ratings[i].values():
            users.append(i)
            n+=1
            summ+=int(j)

    users = set(users)
    # val_rating = list(feedback_ratings.values())
    # print(val_rating)
    await message.answer(
        f"Всего уникальных пользователей: {len(feedback_ratings.keys())}\nОценили сервис: {len(users)} юзеров\nСредняя оценка сервиса: {summ/n if n>0 else 0:0.2f}",
    )

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
