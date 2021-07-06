import logging
from typing import Callable, Optional

from bs4 import BeautifulSoup
import requests
import aiohttp
import telebot
import asyncio
from time import sleep
import json

logger = logging.getLogger("check_bot")


class SiteChecker:
    """ Organizes site check """

    def __init__(self, url: str):
        self.url = url
        self.check_criteria_fun = None

    def check_criteria(self, fun: Callable[[BeautifulSoup], bool]) -> None:
        """ Set check criteria function for the page """
        self.check_criteria_fun = fun

    def check_page(self) -> Optional[bool]:
        """ Page load and criterion check """
        try:
            request = requests.get(self.url)
        except requests.exceptions:
            logger.error('Ошибка связи')
            return
        if request.status_code != 200:
            logger.error('Сервер не отвечает')
            return
        parser = BeautifulSoup(request.text, 'html.parser')
        return self.check_criteria_fun(parser) if self.check_criteria_fun else None


class Bot:
    """ Create notifications Telegram bot """

    def __init__(self, api_key: str):
        self.bot = telebot.AsyncTeleBot(api_key)
        self._setup_bot()

    def _setup_bot(self):
        """ Setup bot function """
        keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard1.row('/handler')

        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            self.bot.send_message(message.chat.id, 'Привет! Для создания напоминания набери /handler',
                                  reply_markup=keyboard1)
            with open('info.json', 'r', encoding='utf-8') as f:
                info = json.load(f)
            if message.chat.id not in info['clients']:
                info['clients'].append(message.chat.id)
            with open('info.json', 'w', encoding='utf-8') as f:
                json.dump(info, f)

        @self.bot.message_handler(commands=['handler'])
        def start_message(message):
            self.bot.send_message(message.chat.id, 'Напоминание установлено', reply_markup=keyboard1)
            with open('info.json', 'r', encoding='utf-8') as f:
                info = json.load(f)
            if message.chat.id not in info['handlers']:
                info['handlers'].append(message.chat.id)
            with open('info.json', 'w', encoding='utf-8') as f:
                json.dump(info, f)

    async def start_bot(self, url: str):
        """ Start bot polling and site checking """

        try:
            await asyncio.gather(
                asyncio.to_thread(self.bot.polling, none_stop=True, interval=2),
                asyncio.to_thread(self.check_page, url)
            )

        except Exception:
            print('Ошибка соединения')

    async def check_page(self, url):
        site = SiteChecker(url)

        @site.check_criteria
        def check_fun(parser: BeautifulSoup):
            return len(parser.select('.error')) == 0

        while True:
            if site.check_page():
                print('time')
                with open('info.json', 'r', encoding='utf-8') as f:
                    info = json.load(f)
                for handler in info['handlers']:
                    self.bot.send_message(handler, "Время настало")
                info['handlers'] = []
                with open('info.json', 'w', encoding='utf-8') as f:
                    json.dump(info, f)
            sleep(300)


if __name__ == '__main__':
    bot = Bot('1810448007:AAGsNhpBb598p_x2-N24M1tT6f5NAF-8mI8')
    try:
        tasks = asyncio.gather(bot.start_bot('http://portal.guap.ru/?n=priem&p=pr2021_exam_results'))
        asyncio.get_event_loop().run_until_complete(tasks)
    except KeyboardInterrupt:
        pass
    # finally:
    #     asyncio.get_event_loop().run_until_complete(bot.start_bot())
