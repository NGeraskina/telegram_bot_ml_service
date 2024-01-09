import asyncio
import json
import logging
import time

import pandas as pd

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from magic_filter import F
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.enums import ParseMode
from aiogram import html
from data_preparation import prepare_data
import joblib
import os

from config_reader import config

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

try:
    bot = Bot(token=config.bot_token.get_secret_value())
except:
    bot = Bot(token=os.environ.get('BOT_TOKEN'))
# Диспетчер
dp = Dispatcher()


class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int] = None


class PredictorsCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int] = None


json_file = 'feedback_ratings.json'

# Load existing feedback ratings from file
try:
    with open(json_file, 'r') as file:
        feedback_ratings = json.load(file)
except FileNotFoundError:
    feedback_ratings = {}


def predict(X):
    _, _, _, ridge = joblib.load(r'./ridge_model.pickle')
    return ridge.predict(X)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    print(feedback_ratings)
    if user_id not in feedback_ratings:
        feedback_ratings[user_id] = {}
    await message.answer(
        "Приветствую! Тут вы можете подать на вход несколько данных о пользователе и получить предсказание")


@dp.message(Command("help"))
async def cmd_special_buttons(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Как пользоваться этим сервисом"),
    )
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


@dp.message(F.text.lower() == "как пользоваться этим сервисом")
async def user_experiense(message: types.Message):
    text = 'Данный бот умеет:\n' \
           '• делать предсказания по одному экземпляру-автомобилю, шаблон высылается\n' \
           '• делать предсказания по батчу автомобилей'

    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text.lower() == "сделать предсказание")
async def user_experiense(message: types.Message):
    builder = InlineKeyboardBuilder()
    for i in range(1, 3):
        builder.button(text=str(i) if i == 1 else 'Более 1', callback_data="predict")
    builder.adjust(2)
    await message.answer(
        "Предсказания для скольки автомобилей вы хотите сделать?",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.callback_query(F.data == "predict")
async def callbacks_predictors(callback: types.CallbackQuery):
    if callback.message.text == '1':
        await callback.message.answer(
            "Пришлите csv файл, в котором содержатся следующие данные об одном автомобиле:",
        )
    else:
        await callback.message.answer(
            "Пришлите csv файл, в котором содержатся следующие данные о нескольких автомобилях:",
        )


@dp.message(F.document)
async def handle_file(message: types.Message):
    if message.document.mime_type == 'text/csv':
        file_bytes = await bot.download(message.document)

        # Read CSV file using pandas
        df = pd.read_csv(file_bytes)
        try:
            item = prepare_data(df)
            pred = predict(item)
        except:
            await message.answer("Пожалуйста, приложите файл необходимого формата")

        if len(df) == 1:
            result_message = f"Предсказанная стоимость автомобиля {df['name'].values[0]}: {pred[0]:0.0f} руб."
        elif len(df) > 1:
            result_message = 'Предсказанные стоимости автомобилей:\n'
            for i in range(len(df)):
                result_message += f"{df['name'].values[i]}: {pred[i]:0.0f} руб.\n"
        await message.answer(result_message, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("Пожалуйста, приложите файл необходимого формата")


@dp.message(F.text.lower() == "оценить работу сервиса")
async def feedback(message: types.Message):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=str(i), callback_data=NumbersCallbackFactory(action="feedback", value=i))
    builder.adjust(5)
    await message.answer(
        "Насколько вам понравилась работа телеграм бота?",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.callback_query(NumbersCallbackFactory.filter())
async def callbacks_num_change_fab(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    timestamp = int(time.time())
    # print(callback.message)
    rating = callback_data.value

    feedback_ratings[user_id][timestamp] = rating

    with open(json_file, 'w') as file:
        json.dump(feedback_ratings, file)
    await callback.message.answer("Благодарю за отзыв!")


@dp.message(F.text.lower() == "вывести статистику по сервису")
async def feedback_stats(message: types.Message):
    with open(json_file, 'r') as file:
        feedback_ratings = json.load(file)
    n = 0
    summ = 0
    users = []
    for i in feedback_ratings:
        for j in feedback_ratings[i].values():
            users.append(i)
            n += 1
            summ += int(j)

    users = set(users)
    await message.answer(
        f"Всего уникальных пользователей: {len(feedback_ratings.keys())}\nОценили сервис: {len(users)} юзеров\nСредняя оценка сервиса: {summ / n if n > 0 else 0:0.2f}",
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
