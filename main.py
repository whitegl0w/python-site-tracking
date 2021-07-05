from bs4 import BeautifulSoup
import requests
import telebot
from threading import Thread
from time import sleep
import json

bot = telebot.TeleBot('1802866369:AAFCPMP1huS_apbw44lukzr985UsFAt2Hmo')


def check_free_time(page):
    try:
        request = requests.get(page)
    except Exception:
        print('Ошибка связи')
        return
    if request.status_code != 200:
        print('Сервер не отвечает')
        return
    parser = BeautifulSoup(request.text, 'html.parser')
    return len(parser.select('.error')) == 0


def bot_pool():
    global bot
    keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard1.row('/handler')

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Привет! Для создания напоминания набери /handler', reply_markup=keyboard1)
        with open('info.json', 'r', encoding='utf-8') as f:
            info = json.load(f)
        if message.chat.id not in info['clients']:
            info['clients'].append(message.chat.id)
        with open('info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f)

    @bot.message_handler(commands=['handler'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Напоминание установлено', reply_markup=keyboard1)
        with open('info.json', 'r', encoding='utf-8') as f:
            info = json.load(f)
        if message.chat.id not in info['handlers']:
            info['handlers'].append(message.chat.id)
        with open('info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f)

    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception:
            print('Ошибка соединения')
            sleep(5)


def check_page():
    global bot
    while True:
        if check_free_time('http://portal.guap.ru/?n=priem&p=pr2021_exam_results'):
            print('time')
            with open('info.json', 'r', encoding='utf-8') as f:
                info = json.load(f)
            for handler in info['handlers']:
                bot.send_message(handler, "Время настало")
            info['handlers'] = []
            with open('info.json', 'w', encoding='utf-8') as f:
                json.dump(info, f)
        sleep(300)


def main():
    thread1 = Thread(target=bot_pool)
    thread2 = Thread(target=check_page)
    thread1.start()
    thread2.start()
    thread2.join()


if __name__ == '__main__':
    main()
