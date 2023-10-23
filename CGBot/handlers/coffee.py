from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from CGBot.const import ADMIN_ID
from CGBot.handlers.common import get_main_keyboard

data_coffee_request_ids = []


class CoffeeStates(StatesGroup):
    waiting_for_request = State()


def get_coffee_message(from_user) -> str:
    msg = f"С тобой хочет выпить кофе: " \
          f"\n @{from_user.username}" \
          f"\n {from_user.full_name}" \
          f"\n User id: {from_user.id}" \
          f"\n\n YES: /coffee_yes_{from_user.id}" \
          f"\n\n\n NO: /coffee_no_{from_user.id}" \
          f"\n\n\n COMPLETED: /coffee_completed_{from_user.id}"

    return msg


async def coffee_start(message: types.Message, state: FSMContext):
    if str(message.from_user.id) in data_coffee_request_ids:
        await message.answer("Вы уже отправляли заявку на кофе. Пожалуйста, ожидайте ответа")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Продолжить")
    keyboard.add("Отмена")
    await message.answer("Вы хотете выпить кофе с @CoderGosha?",
                         reply_markup=keyboard)
    await CoffeeStates.waiting_for_request.set()


async def coffee_accept(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = message.text.replace("/coffee_yes_", "")

    await message.bot.send_message(chat_id=user_id, text="Ваша заявка подтверждена. До встречи за кофе 🖤")
    await state.finish()

    await message.answer("Ready to coffee", reply_markup=get_main_keyboard(message.from_user.id))


async def coffee_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = message.text.replace("/coffee_no_", "")

    await message.bot.send_message(chat_id=user_id, text="Извините, ваша заявка отклонена.")
    await state.finish()
    await message.answer("No ready to coffee", reply_markup=get_main_keyboard(message.from_user.id))


async def coffee_completed(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = message.text.replace("/coffee_completed_", "")
    await state.finish()
    await message.answer("Coffee completed", reply_markup=get_main_keyboard(message.from_user.id))
    data_coffee_request_ids.remove(user_id)


async def coffee_request(message: types.Message, state: FSMContext):
    data_coffee_request_ids.append(str(message.from_user.id))
    await message.bot.send_message(chat_id=ADMIN_ID, text=get_coffee_message(message.from_user))
    await message.answer("Ваш запрос отправлен. В ближайшее время вышлю вам подтверждение",
                         reply_markup=get_main_keyboard(message.from_user.id))


def register_handlers_coffee(dp: Dispatcher):
    dp.register_message_handler(coffee_start, commands="coffee", state="*")
    dp.register_message_handler(coffee_start, Text(endswith=f"coffee", ignore_case=True), state="*")
    dp.register_message_handler(coffee_request, Text(equals="продолжить", ignore_case=True),
                                state=CoffeeStates.waiting_for_request)
    dp.register_message_handler(coffee_accept, filters.RegexpCommandsFilter(regexp_commands=['coffee_yes_([0-9]*)']),
                                state="*")
    dp.register_message_handler(coffee_cancel, filters.RegexpCommandsFilter(regexp_commands=['coffee_no_([0-9]*)']),
                                state="*")

    dp.register_message_handler(coffee_completed,filters.RegexpCommandsFilter(regexp_commands=['coffee_completed_([0-9]*)']),
                                state="*")

