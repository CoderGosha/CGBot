import logging
import os
import datetime
from functools import partial

import telegram
from botanio import botan
from emoji import emojize
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, ConversationHandler, MessageHandler, Filters, RegexHandler

from CGBot.decorator import on_error, catch_exceptions

logger = logging.getLogger(__name__)
CODERGOSHA_ID = "295641973"
BOTAN_KEY = os.getenv('BOTAN_KEY')
users_coffee = dict()


def run_worker(telegram_token, use_webhook, webhook_domain='', webhook_port=''):
    users_state = dict()

    updater = Updater(telegram_token)
    dp = updater.dispatcher
    dp.add_error_handler(on_error)
    dp.add_handler(CommandHandler('start', partial(start),  pass_args=True))
    dp.add_handler(CommandHandler('mainmenu', partial(mainmenu, users_state=users_state)))
    dp.add_handler(RegexHandler('^Прокси', partial(get_proxy, users_state=users_state)))
    dp.add_handler(RegexHandler('^Выпить кофе', partial(drink_cofee, users_state=users_state)))
    dp.add_handler(MessageHandler(Filters.all, partial(mainmenu, users_state=users_state)))

    if use_webhook:
        CERT_DIR = os.getenv('CERT_DIR')
        logger.info('Starting webhook at {}:{}'.format(webhook_domain, webhook_port))
        web_hook_url = 'https://{}:{}/{}'.format(webhook_domain, str(webhook_port), telegram_token)
        updater.start_webhook(listen='0.0.0.0', port=webhook_port, url_path=telegram_token, webhook_url=web_hook_url,
                              key=CERT_DIR + 'private.key', cert=CERT_DIR + 'cert.pem',)
    else:
        logger.info('Starting long poll')
        updater.start_polling()

    return updater


def del_state(update, users_state):
    if update.message.from_user.id in users_state:
        del users_state[update.message.from_user.id]


@catch_exceptions
def start(bot, update, args):
    utm_start = " ".join(args)
    # utm_start = args
    # Необходимо вколхозить статку
    # https://telegram.me/MopedGoaBot?start=test_utm
    message_dic = dict()
    message_dic['source'] = utm_start
    botan.track(token=BOTAN_KEY, uid=update.message.from_user.id, message=message_dic, name="/start")

    coffee = emojize(" :coffee:", use_aliases=True)
    update.message.reply_text("Привет, Я помогу Вам получить прокси. \r\n А еще я расскажу о проектах "
                              "@CoderGosha и сделаю вам кофе" + coffee,
                              reply_markup=ReplyKeyboardMarkup(keyboard_mainmenu(), one_time_keyboard=True))

    return ConversationHandler.END


@catch_exceptions
def mainmenu(bot, update, users_state):
    coffee = emojize(" :coffee:", use_aliases=True)
    # update.message.reply_text(_('You have questions? Write: @CoderGosha'))
    update.message.reply_text("Привет, Я помогу Вам получить прокси. \r\n А еще я расскажу о проектах "
                              "@CoderGosha и сделаю вам кофе" + coffee,
                              reply_markup=ReplyKeyboardMarkup(keyboard_mainmenu(), one_time_keyboard=True))
    del_state(update, users_state)
    return ConversationHandler.END


@catch_exceptions
def get_proxy(bot, update, users_state):
    message_dic = dict()
    botan.track(token=BOTAN_KEY, uid=update.message.from_user.id, message=message_dic, name="proxy")

    coffee = emojize(" :coffee:", use_aliases=True)
    url = "https://t.me/socks?server=188.166.32.209&port=1080&user=proxyuser&pass=6LB95AF795"
    # update.message.reply_text(_('You have questions? Write: @CoderGosha'))
    button_list = [InlineKeyboardButton(text="Применить", url=url)]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    msg = "Я приготовил для вас прокси, нажмите кнопку для того что бы применить. \r\n " \
          "Не забудьте сказать спасибо @CoderGosha и угостить его кофе " + coffee
    update.message.reply_text(msg,
                              reply_markup=reply_markup)
    del_state(update, users_state)
    return ConversationHandler.END


@catch_exceptions
def drink_cofee(bot, update, users_state):
    message_dic = dict()
    botan.track(token=BOTAN_KEY, uid=update.message.from_user.id, message=message_dic, name="coffee")

    coffee = emojize(" :coffee:", use_aliases=True)
    if users_coffee.get(update.message.from_user.id) is not None:
        dtT = datetime.datetime.utcnow() + datetime.timedelta(minutes=-15)
        timecofee = users_coffee.get(update.message.from_user.id)
        if timecofee > dtT:
            msg = "Оооу, не так часто :(" + coffee
            update.message.reply_text(msg)
            return ConversationHandler.END

    msg = "Я написал @CoderGosha что Вы хотите выпить с ним кофе, расписание согласую позже" + coffee
    update.message.reply_text(msg)
    link_user = '<a href="tg://user?id=' + str(update.message.from_user.id) + '"> ' +\
                str(update.message.from_user.first_name) + '</a>\r\n\r\n'

    bot.send_message(chat_id=CODERGOSHA_ID, text="С Вами хотят выпить кофе: " + link_user, parse_mode=telegram.ParseMode.HTML)
    users_coffee[update.message.from_user.id] = datetime.datetime.utcnow()

    del_state(update, users_state)
    return ConversationHandler.END


def keyboard_mainmenu():
    collab = emojize(" ⚔", use_aliases=True)
    write = emojize(" 📩", use_aliases=True)
    project = emojize(" ⚙", use_aliases=True)
    coffee = emojize(" :coffee:", use_aliases=True)
    keyboard = ['Прокси' + collab, 'Проекты' + project, 'Написать автору' + write, 'Выпить кофе' +coffee]

    return build_menu(buttons=keyboard, n_cols=2, header_buttons=None, footer_buttons=None)


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
