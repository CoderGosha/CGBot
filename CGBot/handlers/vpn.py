import logging

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from CGBot.const import ADMIN_ID, BASE_VPN_INSTALL
from CGBot.handlers.common import cmd_cancel, get_main_keyboard
from CGBot.models.vpn import VPNUserState
from CGBot.services.database_service import DBService
from CGBot.services.outline_service import OutlineService
from hurry.filesize import size


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


def get_user_info(from_user) -> str:
    msg = f"\n User id: {from_user.id}" \
          f"\n {from_user.full_name}"

    if from_user.username is not None:
        msg += f"\n @{from_user.username}"

    return msg


async def vpn_request(message: types.Message, state: FSMContext):
    user_info = get_user_info(message.from_user)
    DBService.vpn_request(message.from_user.id, name=get_user_name(message.from_user),
                          user_info=user_info)
    await send_request_to_admin(message, user_info)
    await state.finish()
    await message.answer("Ваш запрос отправлен на модерацию. В ближайшее время вам вышлют данные для подключения",
                         reply_markup=get_main_keyboard(message.from_user.id))


async def vpn_get_requests(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.finish()
    vpn_requests = DBService.vpn_active_request()
    if vpn_requests is None or vpn_requests == []:
        await message.answer("Нет активных заявок")
        return

    msg = ""
    for r in vpn_requests:
        msg = f"Новый запрос на VPN" \
              f"\n{r.user_info}"
        msg += f"\n\n/vpn_accept_{r.user_id}"
        msg += "\n\n"

    await message.answer(msg)


async def vpn_accept(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    client_id = message.text.replace("/vpn_accept_", "")
    state = DBService.check_vpn_state(user_id=client_id)
    if state != VPNUserState.Request:
        await message.bot.send_message(chat_id=ADMIN_ID, text="VPN был подтвержден")
        return

    vpn = DBService.vpn_by_user_id(user_id=client_id)
    if vpn is None:
        logging.error(f"Didn't found profile by user id: {client_id}")
        return
    id, url = OutlineService.create_vpn_user(name=vpn.vpn_name)

    DBService.vpn_accept(client_id, id, url)
    msg = "Ваш VPN: " \
          f"\n\nКлюч:\n {url}" \
          f"\n\nУстановка:\n {BASE_VPN_INSTALL}{url}"

    await message.bot.send_message(chat_id=ADMIN_ID, text="Ready")
    await message.bot.send_message(chat_id=client_id, text=msg)


async def send_request_to_admin(message: types.Message, user_info):
    msg = f"Новый запрос на VPN" \
          f"\n{user_info}"
    msg += f"\n\n/vpn_accept_{message.from_user.id}"
    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)


async def vpn_static(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.finish()
    vpn_statistics = OutlineService.get_statistics()
    if vpn_statistics is None or vpn_statistics == []:
        await message.answer("Нет активной статистики")
        return

    vpn_statistics = {k: v for k, v in sorted(vpn_statistics.items(), key=lambda item: item[1], reverse=True)}
    vpn_user = DBService.vpn_get_all_users()
    vpn_user_dict = {str(x.vpn_uid): x for x in vpn_user}
    count_stat = 0
    msg = "Статистика\nТОП 10\n"
    for key, value in vpn_statistics.items():
        if key in vpn_user_dict:
            vpn = vpn_user_dict[key]
            msg = f"\n{vpn.user_info}" \
                  f"\n Traffic: {size(value)}"
            msg += "\n\n"
            count_stat += 1
            if count_stat > 10:
                continue
    if count_stat > 0:
        await message.answer(msg)
    else:
        await message.answer("Нет доступной статистики")


def register_handlers_vpn(dp: Dispatcher):
    dp.register_message_handler(vpn_start, commands="vpn", state="*")
    dp.register_message_handler(vpn_start, Text(endswith="vpn", ignore_case=True), state="*")
    dp.register_message_handler(vpn_request, Text(equals="продолжить", ignore_case=True),
                                state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_get_requests, Text(endswith="заявки", ignore_case=True), state="*")
    dp.register_message_handler(vpn_static, Text(endswith="статистика", ignore_case=True), state="*")
    dp.register_message_handler(cmd_cancel, state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_accept, filters.RegexpCommandsFilter(regexp_commands=['vpn_accept_([0-9]*)']),
                                state="*")
