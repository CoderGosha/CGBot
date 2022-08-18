import logging

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from CGBot.const import ADMIN_ID, BASE_VPN_INSTALL, DEFAULT_TRAFFIC
from CGBot.handlers.common import cmd_cancel, get_main_keyboard
from CGBot.models.vpn import VPNUserState
from CGBot.services.database_service import DBService
from CGBot.services.outline_service import OutlineService
from hurry.filesize import size


class VPNStates(StatesGroup):
    waiting_for_request = State()
    block_choice_type = State()
    block_delete_vpn = State()
    block_black_list_vpn = State()
    block_list_user = State()
    # waiting_for_food_size = State()


def get_message_static(user_id) -> str:
    vpn = DBService.vpn_by_user_id(user_id)
    used_traffic = OutlineService.get_statistics_by_vpn_id(vpn.vpn_uid)
    access_keys = OutlineService.get_access_keys()
    limit_traffic = "-"

    limit = next(
        (limit for limit in access_keys if limit['id'] == vpn.vpn_uid),
        None,
    )
    if limit is not None:
        if 'dataLimit' in limit:
            limit_traffic = size(limit['dataLimit']['bytes'])

    available_traffic = "-"
    if used_traffic is not None and isinstance(limit_traffic, int):
        available = limit_traffic - used_traffic
        if available < 0:
            available = 0
        available_traffic = size(available)
    else:
        available_traffic = limit_traffic

    used_traffic_str = '0'
    if used_traffic is not None:
        used_traffic_str = size(used_traffic)

    msg = "Ваш VPN: " \
          f"\n\nТрафик за 30 дней:\n {used_traffic_str}" \
          f"\n\nДоступный трафик:\n {available_traffic} из {limit_traffic}" \
          f"\n\nКлюч:\n {vpn.vpn_url}" \
          f"\n\nУстановка:\n {BASE_VPN_INSTALL}{vpn.vpn_url}"

    return msg


async def vpn_start(message: types.Message):
    state_request = DBService.check_vpn_state(message.from_user.id)

    if state_request == VPNUserState.Request:
        await message.answer("Ваш запрос уже отправлен. Ожидайте")
        return

    if state_request == VPNUserState.Blocked:
        await message.answer("Ваш запрос был заблокирован. Извините")
        return

    if state_request == VPNUserState.Ready:
        msg = get_message_static(message.from_user.id)
        await message.answer(msg)
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Продолжить")
    keyboard.add("Отмена")
    await message.answer("Ваш запрос будет отправлен на модерацию. Хотите продолжить?", reply_markup=keyboard)
    await VPNStates.waiting_for_request.set()


def get_user_name(from_user) -> str:
    if from_user.username is not None:
        return from_user.username

    if from_user.full_name is not None:
        return from_user.full_name.replace(" ", "_") + str(from_user.id)

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
    msg = get_message_static(user_id=client_id)

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
    access_keys = OutlineService.get_access_keys()
    vpn_user = DBService.vpn_get_all_users()
    vpn_user_dict = {str(x.vpn_uid): x for x in vpn_user}
    count_stat = 0
    msg = "Статистика\nТОП 20"
    for key, value in vpn_statistics.items():
        limit_traffic = "-"

        if key in vpn_user_dict:
            vpn = vpn_user_dict[key]
            limit = next(
                (limit for limit in access_keys if limit['id'] == vpn.vpn_uid),
                None,
            )
            if limit is not None:
                if 'dataLimit' in limit:
                    limit_traffic = size(limit['dataLimit']['bytes'])

            msg += f"\n{vpn.user_info}" \
                   f"\n Traffic: {size(value)}/{limit_traffic}"
            count_stat += 1
            if count_stat > 20:
                continue
    if count_stat > 0:
        await message.answer(msg)
    else:
        await message.answer("Нет доступной статистики")


async def block_list_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    vpn_user = DBService.vpn_get_all_users()
    if vpn_user is None or vpn_user is []:
        await message.answer("Нет доступной статистики")
        return

    msg = "Список пользователей: "
    for user in vpn_user:
        msg += f"\n{user.user_info}" \
               f"\n Status: {user.state}"

        msg += f"\n\n /delete_{user.user_id}"
        if user.state == VPNUserState.Blocked:
            msg += f"\n\n /unblock_{user.user_id}"
        else:
            msg += f"\n\n /block_{user.user_id}"

    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)
    await VPNStates.block_list_user.set()


async def vpn_pre_delete(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    client_id = message.text.replace("/delete_", "")
    vpn = DBService.vpn_by_user_id(user_id=client_id)
    if vpn is None:
        logging.error(f"Didn't found profile by user id: {client_id}")
        return

    msg = f"\n{vpn.user_info}" \
          f"\n Status: {vpn.state}" \
          f"\nДля подтверждения: "

    msg += f"\n\n /full_delete_{vpn.user_id}"

    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)
    await VPNStates.block_delete_vpn.set()


async def vpn_delete(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.finish()
    client_id = message.text.replace("/full_delete_", "")
    vpn = DBService.vpn_by_user_id(user_id=client_id)
    if vpn is None:
        logging.error(f"Didn't found profile by user id: {client_id}")
        return
    OutlineService.delete_vpn_user(vpn.vpn_uid)
    DBService.vpn_delete(user_id=client_id)
    await message.bot.send_message(chat_id=ADMIN_ID, text='Ready')


def register_handlers_vpn(dp: Dispatcher):
    dp.register_message_handler(vpn_start, commands="vpn", state="*")
    dp.register_message_handler(vpn_start, Text(endswith="vpn", ignore_case=True), state="*")
    dp.register_message_handler(vpn_request, Text(equals="продолжить", ignore_case=True),
                                state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_get_requests, Text(endswith="заявки", ignore_case=True), state="*")
    dp.register_message_handler(vpn_static, Text(endswith="статистика", ignore_case=True), state="*")
    dp.register_message_handler(block_list_user, Text(endswith="блокировка", ignore_case=True), state="*")
    dp.register_message_handler(cmd_cancel, state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_accept, filters.RegexpCommandsFilter(regexp_commands=['vpn_accept_([0-9]*)']),
                                state="*")
    dp.register_message_handler(vpn_pre_delete, filters.RegexpCommandsFilter(regexp_commands=['delete_([0-9]*)']),
                                state=VPNStates.block_list_user)
    dp.register_message_handler(vpn_delete, filters.RegexpCommandsFilter(regexp_commands=['full_delete_([0-9]*)']),
                                state=VPNStates.block_delete_vpn)
