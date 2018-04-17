# -*- coding: utf-8 -*-

import traceback
import logging

logger = logging.getLogger(__name__)


def on_error(bot, update, error):
    logger.error('Update "{}" caused error "{}"'.format(update, error))
    traceback.print_exc()

    if update is not None:
        update.message.reply_text('Внутренняя ошибка')
        update.message.reply_text('{}: {}'.format(type(error).__name__, str(error)))
        update.message.reply_text('Write to @CoderGosha')
        update.message.reply_text('return /mainmenu')


def catch_exceptions(func):
    def wrapper(bot, update, *args, **kwargs):
        try:
            return func(bot, update, *args, **kwargs)
        except Exception as e:
            on_error(bot, update, e)

    return wrapper


def make_db_session(func):
    def wrapper(*args, db_session_maker, **kwargs):
        db = db_session_maker()
        result = func(*args, **kwargs, db=db)
        db.close()
        return result

    return wrapper


