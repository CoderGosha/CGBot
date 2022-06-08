from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from CGBot.const import ADMIN_ID, BASE_VPN_INSTALL
from CGBot.handlers.common import cmd_cancel, get_main_keyboard
from CGBot.models.vpn import VPNUserState
from CGBot.services.database_service import DBService
from CGBot.services.outline_service import OutlineService


class VPNStates(StatesGroup):
    waiting_for_request = State()
    # waiting_for_food_size = State()


async def vpn_start(message: types.Message):
    state_request = DBService.check_vpn_state(message.from_user.id)

    if state_request == VPNUserState.Request:
        await message.answer("Ваш запрос уже отправлен. Ожидайте")
        return

    if state_request == VPNUserState.Blocked:
        await message.answer("Ваш запрос был заблокирован. Извините")
        return

    if state_request == VPNUserState.Ready:
        url = DBService.vpn_get_link(message.from_user.id)
        msg = "Ваш VPN: " \
              f"\n\nКлюч:\n {url}" \
              f"\n\nУстановка:\n {BASE_VPN_INSTALL}{url}"
        await message.answer(msg)
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Продолжить")
    keyboard.add("Отмена")
    await message.answer("Ваш запрос будет отправлен на модерацию. Хотите продолжить?:", reply_markup=keyboard)
    await VPNStates.waiting_for_request.set()


def get_user_name(from_user) -> str:
    if from_user.username is not None:
        return from_user.username

    if from_user.full_name is not None:
        return from_user.full_name.replace(" ", "_") + from_user.id

    return from_user.id


async def vpn_request(message: types.Message, state: FSMContext):
    DBService.vpn_request(message.from_user.id, name=get_user_name(message.from_user))
    await send_request_to_admin(message)
    await state.finish()
    await message.answer("Ваш запрос отправлен на модерацию. В ближайшее время вам вышлют данные для подключения",
                         reply_markup=get_main_keyboard())


async def vpn_accept(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    client_id = message.text.replace("/vpn_accept_", "")
    state = DBService.check_vpn_state(user_id=message.from_user.id)
    if state != VPNUserState.Request:
        await message.bot.send_message(chat_id=ADMIN_ID, text="VPN был подтвержден")
        return

    name = DBService.vpn_name_by_user_id(user_id=message.from_user.id)
    id, url = OutlineService.create_vpn_user(name=name)

    DBService.vpn_accept(message.from_user.id, id, url)
    msg = "Ваш VPN: " \
          f"\n\nКлюч:\n {url}" \
          f"\n\nУстановка:\n {BASE_VPN_INSTALL}{url}"

    await message.bot.send_message(chat_id=ADMIN_ID, text="Ready")
    await message.bot.send_message(chat_id=client_id, text=msg)


async def send_request_to_admin(message: types.Message):
    msg = f"Новый запрос на VPN" \
          f"\n User id: {message.from_user.id}" \
          f"\n {message.from_user.full_name}"

    if message.from_user.username is not None:
        msg += f"\n @{message.from_user.username}"
    msg += f"\n\n/vpn_accept_{message.from_user.id}"
    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)


def register_handlers_vpn(dp: Dispatcher):
    dp.register_message_handler(vpn_start, commands="vpn", state="*")
    dp.register_message_handler(vpn_start, Text(equals="vpn", ignore_case=True), state="*")
    dp.register_message_handler(vpn_request, Text(equals="продолжить", ignore_case=True),
                                state=VPNStates.waiting_for_request)
    dp.register_message_handler(cmd_cancel, state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_accept, filters.RegexpCommandsFilter(regexp_commands=['vpn_accept_([0-9]*)']),
                                state="*")
