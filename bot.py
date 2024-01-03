import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from magic_filter import F
from typing import Optional
from aiogram.filters.callback_data import CallbackData

from config_reader import config

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())
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
    await message.answer(
        "Приветсвую! Тут вы можете подать на вход несколько данных о пользователе и получить предсказание")


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
    rating = int(message.text)

    # Save the feedback in the dictionary
    feedback_ratings[user_id] = rating

    # Save the feedback dictionary to the JSON file
    with open(json_file, 'w') as file:
        json.dump(feedback_ratings, file)
    await message.answer("Благодарю за отзыв!")


@dp.message(F.text.lower() == "вывести статистику по сервису")
async def feedback_stats(message: types.Message):
    with open(json_file, 'r') as file:
        feedback_ratings = json.load(file)
    val_rating = list(feedback_ratings.values())
    await message.answer(
        f"Средняя оценка сервиса: {sum(val_rating)/len(val_rating) if len(val_rating)>0 else 0}",
    )

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
