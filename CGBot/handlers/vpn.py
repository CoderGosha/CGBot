

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from CGBot.handlers.common import cmd_cancel, get_main_keyboard


class VPNStates(StatesGroup):
    waiting_for_request = State()
    # waiting_for_food_size = State()


async def vpn_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Продолжить")
    keyboard.add("Отмена")
    await message.answer("Ваш запрос будет отправлен на модерацию. Хотите продолжить?:", reply_markup=keyboard)
    await VPNStates.waiting_for_request.set()


async def vpn_request(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Ваш запрос отправлен на модерацию. В ближайшее время вам вышлют данные для подключения",
                         reply_markup=get_main_keyboard())


def register_handlers_vpn(dp: Dispatcher):
    dp.register_message_handler(vpn_start, commands="vpn", state="*")
    dp.register_message_handler(vpn_start, Text(equals="vpn", ignore_case=True), state="*")
    dp.register_message_handler(vpn_request, Text(equals="продолжить", ignore_case=True),
                                state=VPNStates.waiting_for_request)
    dp.register_message_handler(cmd_cancel, state=VPNStates.waiting_for_request)
