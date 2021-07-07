import asyncio
import sys

from bs4 import BeautifulSoup

from check_bot import NotifyBot, SiteChecker


if __name__ == '__main__':
    bot = NotifyBot(sys.argv[1])
    site = SiteChecker('http://portal.guap.ru/portal/priem/priem2021/mag_exam/index.html')
    site.check_criteria(lambda parser: not len(parser.select('.error')))

    @site.check_criteria
    def checker(parser: BeautifulSoup):
        h1 = parser.select_one('.doc > h1').text
        return h1 != 'Результаты вступительных испытаний при приеме на обучение по программам магистратуры. Дата публикации -  05 июля 2021.'

    try:
        asyncio.run(bot.start_bot(site.check_page, 300))
    except KeyboardInterrupt:
        pass
