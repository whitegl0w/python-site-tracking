import aiohttp
import asyncio
import json
import logging
import os
import telebot

from bs4 import BeautifulSoup
from logging_setting import ColorHandler
from typing import Callable, Optional, Coroutine, Any

logger = logging.getLogger("NotifyBot")
logger.setLevel(logging.INFO)
logger.addHandler(ColorHandler())


class SiteChecker:
    """ Organizes site check """

    def __init__(self, url: str):
        self.url = url
        self.check_criteria_fun = None

    def check_criteria(self, fun: Callable[[BeautifulSoup], bool]) -> None:
        """ Set check criteria function for the page """
        self.check_criteria_fun = fun

    async def check_page(self) -> Optional[bool]:
        """ Page load and criterion check """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status != 200:
                        logger.error('Server is not responding')
                        return
                    parser = BeautifulSoup(await response.text(), 'html.parser')

        except aiohttp.ClientConnectionError:
            logger.error('Site connection error ')
            return
        return self.check_criteria_fun(parser) if self.check_criteria_fun else None


class NotifyBot:
    """ Create notifications Telegram bot """

    ConfigFile = 'bot_data.json'

    def __init__(self, api_key: str):
        self._bot = telebot.TeleBot(api_key)
        if not os.path.exists(self.ConfigFile):
            with open(self.ConfigFile, 'w', encoding='utf-8') as f:
                json.dump({'clients': [], 'handlers': []}, f)

    def _setup_bot(self):
        """ Setup bot function """
        keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard1.row('/handler')
        keyboard1.row('/delete')

        @self._bot.message_handler(commands=['start'])
        def start_message(message):
            self._bot.send_message(message.chat.id, 'Привет! Для создания напоминания набери /handler',
                                   reply_markup=keyboard1)
            with open(self.ConfigFile, 'r', encoding='utf-8') as f:
                info = json.load(f)
            if message.chat.id not in info['clients']:
                info['clients'].append(message.chat.id)
            with open(self.ConfigFile, 'w', encoding='utf-8') as f:
                json.dump(info, f)

        @self._bot.message_handler(commands=['handler'])
        def handler_message(message):
            logger.info(f'Notifications added for: {message.chat.id}')
            with open(self.ConfigFile, 'r', encoding='utf-8') as f:
                info = json.load(f)
            if message.chat.id not in info['handlers']:
                info['handlers'].append(message.chat.id)
                self._bot.send_message(message.chat.id, 'Напоминание установлено', reply_markup=keyboard1)
            else:
                self._bot.send_message(message.chat.id, 'Напоминание уже есть', reply_markup=keyboard1)
            with open(self.ConfigFile, 'w', encoding='utf-8') as f:
                json.dump(info, f)

        @self._bot.message_handler(commands=['delete'])
        def delete_message(message):
            with open(self.ConfigFile, 'r', encoding='utf-8') as f:
                info = json.load(f)
            if message.chat.id in info['handlers']:
                self._bot.send_message(message.chat.id, 'Напоминание удалено', reply_markup=keyboard1)
                info['handlers'].remove(message.chat.id)
            else:
                self._bot.send_message(message.chat.id, 'Напоминание не найдено', reply_markup=keyboard1)
            with open(self.ConfigFile, 'w', encoding='utf-8') as f:
                json.dump(info, f)

        self._bot.polling(none_stop=True, interval=2)

    async def start_bot(self, criterion: Callable[[], Coroutine[Any, Any, Optional[bool]]], timeout: float) -> None:
        """ Start bot and start checking 'criterion_coro' every 'timeout' seconds """
        try:
            await asyncio.gather(
                asyncio.to_thread(self._setup_bot),
                self._run_checker(criterion, timeout)
            )

        except Exception as e:
            print(e)

    async def _run_checker(self, criterion: Callable[[], Coroutine[Any, Any, Optional[bool]]], timeout: float) -> None:
        """ Check 'criterion_coro' every 'timeout' seconds and send notification if result is True """
        while True:
            if await criterion():
                logger.info('Criterion is TRUE')
                with open(self.ConfigFile, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                for handler in info['handlers']:
                    self._bot.send_message(handler, "Время настало")
                info['handlers'] = []
                with open(self.ConfigFile, 'w', encoding='utf-8') as f:
                    json.dump(info, f)
            await asyncio.sleep(timeout)
