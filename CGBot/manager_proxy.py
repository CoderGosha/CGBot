import logging
import os

import telegram
from sqlalchemy import func
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, ConversationHandler, MessageHandler, Filters, RegexHandler

from CGBot.common_func import build_menu
from CGBot.decorator import on_error, catch_exceptions, make_db_session

from CGBot.models import Users, Proxy
from .state_bot import *


logger = logging.getLogger(__name__)
CODERGOSHA_ID = "295641973"


@catch_exceptions
def proxy_action(bot, update):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        msg = "Выбери действие"
        button = ['Add proxy', 'Delete Proxy']
        update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(build_menu(button, 1),
                                                                        one_time_keyboard=True))
        return PROXY_ACTION
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@catch_exceptions
def proxy_add(bot, update, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        msg = "Назвение прокси"
        update.message.reply_text(msg)
        return PROXY_GET_NAME
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@catch_exceptions
def proxy_add_url(bot, update, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        users_state[update.message.from_user.id] = dict()
        users_state[update.message.from_user.id]['proxy_name'] = update.message.text
        msg = "SEND URL"
        update.message.reply_text(msg)
        return PROXY_GET_URL
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@make_db_session
@catch_exceptions
def proxy_add_commit(bot, update, db, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        url = update.message.text
        proxy_name = users_state[update.message.from_user.id]['proxy_name']
        max = db.query(Proxy.proxy_id, func.max(Proxy.proxy_id)).first()
        print (max)
        # Вставка в таблицу
        proxy_rec = db.query(Proxy).filter(Proxy.link == url).first()
        if proxy_rec is None:
            # Новый пользователь
            try:
                if max[0] is None:
                    max = 1
                else:
                    max = int(max[0]) + 1

                proxy = Proxy(proxy_id=max, link=url, name=proxy_name, is_active=True)
                db.add(proxy)
                db.commit()
            except NameError:
                db.rollback()

        else:
            proxy_rec.is_active = True
            try:
                db.commit()
            except:
                db.rollback()

        update.message.reply_text("commit \r\n /mainmenu")
        return ConversationHandler.END
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@make_db_session
@catch_exceptions
def proxy_del(bot, update, db, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        id = update.message.text
        proxy_rec = db.query(Proxy).filter(Proxy.proxy_id == id).first()
        if proxy_rec is not None:
            # Новый пользователь
            try:
                db.delete(proxy_rec)
                db.commit()
            except NameError:
                db.rollback()

        update.message.reply_text("DEL - Ok \r\n /mainmenu")
        return ConversationHandler.END
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END


@make_db_session
@catch_exceptions
def proxy_del_list(bot, update, db, users_state):
    if str(update.message.from_user.id) == CODERGOSHA_ID:
        # eto ya
        msg = "Select Proxy for del: \r\n"
        button = []
        for prox in db.query(Proxy).filter(Proxy.is_active):
            msg += "ID: %s . Name: %s, URL: %s \r\n " % (str(prox.proxy_id), prox.name, prox.link)
            button.append(str(prox.proxy_id))
        msg += " \r\n\r\n /mainmenu"

        update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(build_menu(button, 3),
                                                                        one_time_keyboard=True),
                                  parse_mode=telegram.ParseMode.HTML)
        return PROXY_DEL_LIST
    else:
        msg = "Эта темная сторона не для тебя"
        update.message.reply_text(msg)
        return ConversationHandler.END