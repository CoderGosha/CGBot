import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from CGBot.handlers.coffee import register_handlers_coffee
from CGBot.handlers.common import register_handlers_common
from CGBot.handlers.vpn import register_handlers_vpn

logger = logging.getLogger(__name__)


class CGBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.__registration__()

    def __registration__(self):
        register_handlers_common(self.dp)
        register_handlers_vpn(self.dp)
        register_handlers_coffee(self.dp)

    async def start(self):
        await self.set_commands()
        await self.dp.skip_updates()
        await self.dp.start_polling()

# Регистрация команд, отображаемых в интерфейсе Telegram
    async def set_commands(self):
        commands = [
            BotCommand(command="/start", description="Начать ботить с ботом"),
            BotCommand(command="/vpn", description="Запросить VPN"),
            BotCommand(command="/coffee", description="Позвать на кофе"),
            BotCommand(command="/cancel", description="Отменить")
        ]
        await self.bot.set_my_commands(commands)




