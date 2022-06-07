from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text

from CGBot.handlers.common import get_main_keyboard


async def coffee_start(message: types.Message):

    await message.answer("Сегодня было слишком много кофе...", reply_markup=get_main_keyboard())


def register_handlers_coffee(dp: Dispatcher):
    dp.register_message_handler(coffee_start, commands="coffee", state="*")
    dp.register_message_handler(coffee_start, Text(endswith=f"coffee", ignore_case=True), state="*")

