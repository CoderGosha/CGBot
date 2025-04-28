import logging

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ParseMode

from CGBot.const import ADMIN_ID, BASE_VPN_INSTALL, DEFAULT_TRAFFIC
from CGBot.handlers.common import cmd_cancel, get_main_keyboard
from CGBot.models.vpn import VPNUserState
from CGBot.services.database_service import DBService
from CGBot.services.outline_service import OutlineService
from hurry.filesize import size

from CGBot.services.vpn_service import VPNService


class VPNStates(StatesGroup):
    vpn_type_chosen = State()
    vpn_chosen = State()
    waiting_for_request = State()
    block_choice_type = State()
    block_delete_vpn = State()
    block_black_list_vpn = State()
    block_list_user = State()
    # waiting_for_food_size = State()


def get_message_static(user_id, vpn_service: OutlineService) -> str:
    if vpn_service.vpn_type == "Outline":
        return get_message_static_outline(user_id, vpn_service)

    else:
        return get_static_trojan(user_id, vpn_service)


def get_static_trojan(user_id, vpn_service: OutlineService) -> str:
    vpn = DBService.vpn_by_user_id(user_id, vpn_service.vpn_id)
    vpn_url = VPNService.get_vpn_by_id(vpn_service.vpn_id)

    msg = (
        f'Ваш VPN - {vpn_service.name}:\n\n'
        f'Ваш ключ:\n\n'
        f'Android/MacOS: <a href="https://github.com/hiddify/hiddify-app/releases">Скачать приложение</a>\n\n'
        f'Iphone: Streisand\n\n'
        f'URL:\n<code>{vpn_url.api_url}</code>'
    )
    return msg


def get_message_static_outline(user_id, vpn_service: OutlineService) -> str:

    vpn = DBService.vpn_by_user_id(user_id, vpn_service.vpn_id)
    used_traffic = vpn_service.get_statistics_by_vpn_id(vpn.vpn_uid)
    access_keys = vpn_service.get_access_keys()
    limit_traffic = "-"

    limit = next(
        (limit for limit in access_keys if limit['id'] == vpn.vpn_uid),
        None,
    )
    if limit is not None:
        if 'dataLimit' in limit:
            limit_traffic = size(limit['dataLimit']['bytes'])

    used_traffic_str = '0'
    if used_traffic is not None:
        used_traffic_str = size(used_traffic)

    msg = f"Ваш VPN - {vpn_service.name}: " \
          f"\n\nТрафик за 30 дней:\n {used_traffic_str}" \
          f"\n\nЛимит:\n {limit_traffic}" \
          f"\n\nКлюч:\n {vpn.vpn_url}" \
          f"\n\nУстановка:\n {BASE_VPN_INSTALL}{vpn.vpn_url}"

    return msg


async def vpn_type_choice(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for vpn in VPNService.get_type_vpns():
        keyboard.add(vpn)

    keyboard.add("Отмена")
    await message.answer("Выберите тип VPN", reply_markup=keyboard)
    await VPNStates.vpn_type_chosen.set()


async def vpn_outline_choice(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for vpn in VPNService.get_vpns():
        keyboard.add(vpn.name)

    keyboard.add("Отмена")
    await message.answer("Выберите страну VPN", reply_markup=keyboard)
    await VPNStates.vpn_chosen.set()


async def vpn_trojan_choice(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for vpn in VPNService.get_trojan_vpns():
        keyboard.add(vpn.name)

    keyboard.add("Отмена")
    await message.answer("Выберите страну VPN", reply_markup=keyboard)
    await VPNStates.vpn_chosen.set()


async def vpn_start(message: types.Message, state: FSMContext):
    vpn = VPNService.get_vpn_by_name(message.text)
    if vpn is None:
        await message.answer("VPN не найден")
        return

    state_request = DBService.check_vpn_state(message.from_user.id, vpn.vpn_id)

    if state_request == VPNUserState.Request:
        await message.answer("Ваш запрос уже отправлен. Ожидайте")
        # await state.finish()
        return

    if state_request == VPNUserState.Blocked:
        await message.answer("Ваш запрос был заблокирован. Извините")
        # await state.finish()
        return

    if state_request == VPNUserState.Ready:
        msg = get_message_static(message.from_user.id, vpn)
        await message.answer(msg, parse_mode=ParseMode.HTML)
        # await state.finish()
        return

    async with state.proxy() as data:
        data['request_vpn_id'] = vpn.vpn_id

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Продолжить")
    keyboard.add("Отмена")
    await message.answer("Ваш запрос на новый VPN будет отправлен на модерацию. Хотите продолжить?", reply_markup=keyboard)
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
    vpn_id = None
    async with state.proxy() as data:
        vpn_id = data['request_vpn_id']

    DBService.vpn_request(message.from_user.id, name=get_user_name(message.from_user),
                          user_info=user_info, vpn_config_id=vpn_id)
    await send_request_to_admin(message, user_info, vpn_id, message.from_user.id)
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
        vpn = VPNService.get_vpn_by_id(r.vpn_config_id)

        msg = f"Новый запрос на VPN - {vpn.name}" \
              f"\n{r.user_info}"
        msg += f"\n\n/vpn_accept_{r.vpn_id}"
        msg += "\n\n"

    await message.answer(msg)


async def vpn_accept(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    vpn_id = message.text.replace("/vpn_accept_", "")
    request_vpn = DBService.vpn_by_vpn_id(vpn_id=vpn_id)
    if request_vpn is None:
        logging.error(f"Didn't found profile by vpn id: {vpn_id}")
        return

    if request_vpn.state != VPNUserState.Request:
        await message.bot.send_message(chat_id=ADMIN_ID, text="VPN был подтвержден")
        return

    vpn = VPNService.get_vpn_by_id(request_vpn.vpn_config_id)

    id, url = vpn.create_vpn_user(name=request_vpn.vpn_name)

    DBService.vpn_accept(vpn_id, id, url)
    msg = get_message_static(user_id=request_vpn.user_id, vpn_service=vpn)

    await message.bot.send_message(chat_id=ADMIN_ID, text="Ready")
    await message.bot.send_message(chat_id=request_vpn.user_id, text=msg, parse_mode=ParseMode.HTML)


async def send_request_to_admin(message: types.Message, user_info, vpn_id, user_id):
    vpn = VPNService.get_vpn_by_id(vpn_id)
    if vpn is None:
        await message.answer("VPN не найден")
        return

    request_vpn = DBService.vpn_by_user_id(user_id, vpn_id)

    msg = f"Новый запрос на VPN: {vpn.vpn_type} - {vpn.name}" \
          f"\n{user_info}"
    msg += f"\n\n/vpn_accept_{request_vpn.vpn_id}"
    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)


async def vpn_static(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.finish()
    vpn_services = VPNService.vpn_outline_services
    if len(vpn_services) == 0:
        await message.answer("Нет доступной статистики")

    for vpn_service in vpn_services:
        vpn_statistics = vpn_service.get_statistics()
        if vpn_statistics is None or vpn_statistics == []:
            await message.answer("Нет активной статистики")
            return

        vpn_statistics = {k: v for k, v in sorted(vpn_statistics.items(), key=lambda item: item[1], reverse=True)}
        access_keys = vpn_service.get_access_keys()
        vpn_user = DBService.vpn_get_all_users(vpn_service.vpn_id)
        vpn_user_dict = {str(x.vpn_uid): x for x in vpn_user}
        count_stat = 0
        msg = f"Статистика\nТОП 20 - {vpn_service.name}"
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
            await message.answer(f"Нет доступной статистики - {vpn_service.name}")


async def block_list_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    vpn_services = VPNService.vpn_outline_services
    for vpn_service in vpn_services:
        vpn_user = DBService.vpn_get_all_users(vpn_service.vpn_id)
        if vpn_user is None or vpn_user is []:
            await message.answer(f"Нет доступной статистики - {vpn_service.name}")
            return

        msg = f"Список пользователей - {vpn_service.name}:"
        for user in vpn_user:
            msg += f"\n{user.user_info}" \
                   f"\n Status: {user.state}"

            msg += f"\n\n /delete_{user.vpn_id}"
            if user.state == VPNUserState.Blocked:
                msg += f"\n\n /unblock_{user.vpn_id}"
            else:
                msg += f"\n\n /block_{user.vpn_id}"

        await message.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await VPNStates.block_list_user.set()


async def vpn_pre_delete(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    vpn_id = message.text.replace("/delete_", "")
    vpn = DBService.vpn_by_vpn_id(vpn_id)
    if vpn is None:
        logging.error(f"Didn't found profile by vpn id: {vpn_id}")
        return

    msg = f"\n{vpn.user_info}" \
          f"\n Status: {vpn.state}" \
          f"\nДля подтверждения: "

    msg += f"\n\n /full_delete_{vpn.vpn_id}"

    await message.bot.send_message(chat_id=ADMIN_ID, text=msg)
    await VPNStates.block_delete_vpn.set()


async def vpn_delete(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.finish()
    vpn_id = message.text.replace("/full_delete_", "")
    vpn = DBService.vpn_by_vpn_id(vpn_id)
    if vpn is None:
        logging.error(f"Didn't found profile by vpn_id: {vpn_id}")
        return

    vpn_service = VPNService.get_vpn_by_id(vpn.vpn_config_id)

    vpn_service.delete_vpn_user(vpn.vpn_uid)
    DBService.vpn_delete(vpn_id=vpn_id)
    await message.bot.send_message(chat_id=ADMIN_ID, text='Ready')


def register_handlers_vpn(dp: Dispatcher):
    dp.register_message_handler(vpn_type_choice, commands="vpn", state="*")
    dp.register_message_handler(vpn_type_choice, Text(endswith="VPN", ignore_case=True), state="*")
    dp.register_message_handler(vpn_outline_choice, Text(startswith="Outline", ignore_case=True),
                                state=VPNStates.vpn_type_chosen)
    dp.register_message_handler(vpn_trojan_choice, Text(startswith="Trojan", ignore_case=True),
                                state=VPNStates.vpn_type_chosen)
    dp.register_message_handler(vpn_request, Text(equals="продолжить", ignore_case=True),
                                state=VPNStates.waiting_for_request)
    dp.register_message_handler(vpn_start, state=VPNStates.vpn_chosen)
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
