from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from emoji import emojize


def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    coffee = emojize(" :coffee:", use_aliases=True)
    keyboard.add("VPN")
    keyboard.add(f"{coffee} Coffee")
    keyboard.add("About ")
    return keyboard


async def cmd_start(message: types.Message, state: FSMContext):
    coffee = emojize(" :coffee:", use_aliases=True)
    await state.finish()
    keyboard = get_main_keyboard()
    await message.answer(
        "Привет, Я помогу Вам получить VPN "
        "\r\nИ сделаю вам кофе" + coffee
        + "\r\nПодробнее о проектах @CoderGosha"
          "\r\nhttps://codergosha.com/",
        reply_markup=keyboard
    )


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=get_main_keyboard())


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel,  Text(equals="отмена", ignore_case=True), state="*")
    dp.register_message_handler(cmd_start, Text(equals="about", ignore_case=True), state="*")
