import aiogram.types
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import KeyboardButton
from emoji import emojize

from CGBot.const import ADMIN_ID


def get_main_keyboard(user_id):
    b_vpn = KeyboardButton(f"🕵 VPN")
    b_coffee = KeyboardButton(f"☕️ Coffee")
    b_about = KeyboardButton("👨🏼‍💻 About ")
    b_donation = KeyboardButton("💰 Donation")
    b_active_request = KeyboardButton(f"🥱 Заявки")
    b_block_vpn = KeyboardButton(f"🧱 Блокировка")
    b_static = KeyboardButton("📈 Статистика ")

    if user_id != ADMIN_ID:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(b_vpn).add(b_coffee).add(b_donation).add(b_about)
        return keyboard
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(b_vpn, b_active_request)
        keyboard.row(b_coffee, b_block_vpn)
        keyboard.row(b_donation, b_static)
        keyboard.row(b_about)
        return keyboard


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = get_main_keyboard(message.from_user.id)
    await message.answer(
        "Привет, Я помогу Вам получить VPN "
        "\r\nИ сделаю вам кофе ☕️"
        + "\r\nПодробнее о проектах @CoderGosha"
          "\r\nhttps://codergosha.com/",
        reply_markup=keyboard
    )


async def cmd_donation(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = get_main_keyboard(message.from_user.id)
    await message.answer(
        "VPN всегда будут бесплатными"
        "\r\nНо если вы хотите поддержать автора️"
        + "\r\nYoo Money: \r\n\r\n410015018607209"
          "\r\n\r\nUSDT: \r\n\r\n0xdb3981D304e6Dc39246e215958E0ea22D8417b60",
        reply_markup=keyboard
    )


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=get_main_keyboard(message.from_user.id))


async def cmd_unknown(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Команда не найдена", reply_markup=get_main_keyboard(message.from_user.id))


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel,  Text(equals="отмена", ignore_case=True), state="*")
    dp.register_message_handler(cmd_start, Text(endswith="about", ignore_case=True), state="*")
    dp.register_message_handler(cmd_donation, Text(endswith="donation", ignore_case=True), state="*")
    # dp.register_message_handler(cmd_unknown, content_types=aiogram.types.ContentTypes.TEXT)
