import logging
import os
import datetime
import traceback
from functools import partial

import telegram
from botanio import botan
from emoji import emojize
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, ConversationHandler, MessageHandler, Filters, RegexHandler

from CGBot.decorator import on_error, catch_exceptions
from CGBot.manager_proxy import proxy_action, proxy_add, proxy_add_commit, proxy_add_url, proxy_del_list, proxy_del
from CGBot.models import Users, Proxy
from .state_bot import *

logger = logging.getLogger(__name__)
CODERGOSHA_ID = "295641973"
users_coffee = dict()


def run_worker(telegram_token, db_session_maker, use_webhook, webhook_domain='', webhook_port=''):
    users_state = dict()

    updater = Updater(telegram_token)
    dp = updater.dispatcher
    dp.add_error_handler(on_error)
    dp.add_handler(CommandHandler('start', partial(start, db_session_maker=db_session_maker),  pass_args=True))
    dp.add_handler(CommandHandler('mainmenu', partial(mainmenu, db_session_maker=db_session_maker,
                                                      users_state=users_state)))
    dp.add_handler(RegexHandler('^Прокси', partial(get_proxy, db_session_maker=db_session_maker,
                                                   users_state=users_state)))
    dp.add_handler(RegexHandler('^Выпить кофе', partial(drink_cofee,
                                                        users_state=users_state)))

    dp.add_handler(RegexHandler('^Уведомления', partial(set_notify, db_session_maker=db_session_maker,
                                                        users_state=users_state)))

    dp.add_handler(ConversationHandler(
        entry_points=[RegexHandler('^Notify', partial(get_notify))],
        states={
            GET_NOTIFY: [
                RegexHandler('^Mainmenu', partial(mainmenu, users_state=users_state)),
                MessageHandler(Filters.text,
                               partial(check_message, users_state=users_state))
            ],

            CHECK_NOTIFY: [
                RegexHandler('^Ok', partial(send_notify, db_session_maker=db_session_maker,
                                                         users_state=users_state))
            ]
        },
        allow_reentry=True,
        fallbacks=[RegexHandler('^Mainmenu', partial(mainmenu, users_state=users_state))]

    ))

    dp.add_handler(ConversationHandler(
        entry_points=[RegexHandler('^Proxy', partial(proxy_action))],
        states={
            PROXY_ACTION: [
                RegexHandler('^Mainmenu', partial(mainmenu, users_state=users_state)),
                RegexHandler('^Add',
                               partial(proxy_add, users_state=users_state)),

                RegexHandler('^Delete', partial(proxy_del_list, db_session_maker=db_session_maker,
                                                users_state=users_state))
            ],


            PROXY_GET_NAME: [
                MessageHandler(Filters.text, partial(proxy_add_url, users_state=users_state))
            ],

            PROXY_GET_URL: [
                MessageHandler(Filters.text, partial(proxy_add_commit, db_session_maker=db_session_maker,
                                                     users_state=users_state))
            ],

            PROXY_DEL_LIST: [
                MessageHandler(Filters.text, partial(proxy_del, db_session_maker=db_session_maker,
                                                     users_state=users_state))
            ]

        },
        allow_reentry=True,
        fallbacks=[RegexHandler('^Mainmenu', partial(mainmenu, users_state=users_state))]

    ))

    dp.add_handler(MessageHandler(Filters.all, partial(mainmenu, db_session_maker=db_session_maker,
                                                       users_state=users_state)))

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


def make_db_session(func):
    def wrapper(*args, db_session_maker, **kwargs):
        db = db_session_maker()
        result = func(*args, **kwargs, db=db)
        db.close()
        return result

    return wrapper


@make_db_session
@catch_exceptions
def start(bot, update, db, args):
    utm_start = " ".join(args)
    # utm_start = args
    # Необходимо вколхозить статку
    # https://telegram.me/MopedGoaBot?start=test_utm

    coffee = emojize(" :coffee:", use_aliases=True)
    update_user_status(db, update.message.from_user.id, True)
    notify_status = user_status_notify(db, update.message.from_user.id)
    update.message.reply_text("Привет, Я помогу Вам получить прокси. \r\n А еще я расскажу о проектах "
                              "@CoderGosha и сделаю вам кофе" + coffee,
                              reply_markup=ReplyKeyboardMarkup(keyboard_mainmenu(user_id=update.message.from_user.id,
                                                                                 notify_status=notify_status),
                                                               one_time_keyboard=True))

    return ConversationHandler.END


@make_db_session
@catch_exceptions
def mainmenu(bot, update, db, users_state):
    coffee = emojize(" :coffee:", use_aliases=True)
    notify_status = user_status_notify(db, update.message.from_user.id)
    # update.message.reply_text(_('You have questions? Write: @CoderGosha'))
    update.message.reply_text("Привет, Я помогу Вам получить прокси. \r\n А еще я расскажу о проектах "
                              "@CoderGosha и сделаю вам кофе" + coffee,
                              reply_markup=ReplyKeyboardMarkup(keyboard_mainmenu(user_id=update.message.from_user.id,
                                                                                 notify_status=notify_status),
                                                               one_time_keyboard=True))
    del_state(update, users_state)
    return ConversationHandler.END


@make_db_session
@catch_exceptions
def get_proxy(bot, update, db, users_state):
    coffee = emojize(" :coffee:", use_aliases=True)
    button_list = []
    for prox in db.query(Proxy).filter(Proxy.is_active).all():
        button_list.append(InlineKeyboardButton(text=prox.name, url=prox.link))

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    msg = "Я приготовил для вас пару прокси, нажмите кнопку для того что бы применить. \r\n " \
          "Не забудьте сказать спасибо @CoderGosha и угостить его кофе " + coffee
    update.message.reply_text(msg,
                              reply_markup=reply_markup)
    del_state(update, users_state)
    return ConversationHandler.END


@make_db_session
@catch_exceptions
def set_notify(bot, update, db, users_state):
    notify_status = user_status_notify(db, update.message.from_user.id)
    if notify_status:
        msg = "Я отключаюсь"
        update_user_status(db, update.message.from_user.id, False)
    else:
        msg = "Я буду рад твоей компании, теперь я снова могу тебе писать."
        update_user_status(db, update.message.from_user.id, True)

    update.message.reply_text(msg,
                              reply_markup=ReplyKeyboardMarkup(keyboard_mainmenu(user_id=update.message.from_user.id,
                                                                                 notify_status=not notify_status),
                                                               one_time_keyboard=True))
    return ConversationHandler.END


@catch_exceptions
def get_notify(bot, update):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        msg = "Напиши и я напишу: "
        update.message.reply_text(msg)
        return GET_NOTIFY
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@catch_exceptions
def check_message(bot, update, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        msg = "Отправить? \r\n" + update.message.text
        button = ['Ok', 'Отмена']
        users_state[update.message.from_user.id] = dict()
        users_state[update.message.from_user.id]['notify'] = update.message.text
        update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(build_menu(button, 1),
                                                                        one_time_keyboard=True))
        return CHECK_NOTIFY
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@make_db_session
@catch_exceptions
def send_notify(bot, update, db, users_state):
    # Отправим открытки всем юзерам
    text = users_state[update.message.from_user.id]['notify']
    count = 0
    for user in db.query(Users).filter(Users.send_notify):
        try:
            bot.send_message(user.user_id, text)
            count += 1
        except telegram.error.BadRequest as e:
            if 'chat not found' in e.message.lower():
                logger.warning('Disabling channel because of telegram error: {}'.format(e))
                traceback.print_exc()
                update_user_status(db, user_id=user.user_id, status=False)
            else:
                raise

        except telegram.error.Unauthorized as e:
            logger.warning('Disabling channel because of telegram error: {}'.format(e))
            traceback.print_exc()
            update_user_status(db, user_id=user.user_id, status=False)
    msg = "Message send: %i" % count
    update.message.reply_text(msg)
    update.message.reply_text(" /mainmenu")
    return ConversationHandler.END


@catch_exceptions
def drink_cofee(bot, update, users_state):
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


def keyboard_mainmenu(user_id, notify_status):
    collab = emojize(" ⚔", use_aliases=True)
    write = emojize(" 📩", use_aliases=True)
    project = emojize(" ⚙", use_aliases=True)
    coffee = emojize(" :coffee:", use_aliases=True)

    admin_button = None
    if str(user_id) == CODERGOSHA_ID:
        admin_button = ['Notify', 'Proxy']

    keyboard = ['Прокси' + collab, 'Проекты' + project, 'Написать автору' + write, 'Выпить кофе' + coffee]

    return build_menu(buttons=keyboard, n_cols=2, header_buttons=None, footer_buttons=admin_button)


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


def update_user_status(db, user_id, status):
    user_rec = db.query(Users).filter(Users.user_id == user_id).first()
    if user_rec is None:
        # Новый пользователь
        try:
            user = Users(user_id=str(user_id), send_notify=status)
            db.add(user)
            db.commit()
            return True
        except NameError:
            db.rollback()
            return False

    else:
        user_rec.send_notify = status
        try:
            db.commit()
            return True
        except:
            db.rollback()
            return False


def user_status_notify(db, user_id):
    user_rec = db.query(Users).filter(Users.user_id == user_id).first()
    if user_rec is None:
        return False
    else:
        return user_rec.send_notify


