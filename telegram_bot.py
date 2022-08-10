import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events


class Telegram:

    def __init__(self):
        self.api_id = 15901021
        self.api_hash = '55bf836ec7e1856d1753e00e0513a303'
        self.token = '5401109253:AAF5vSLfJV2rjhH9JiQ-j7fgbS7VIKffTN4'
        self.phone = '+64212150997'
        self.client = TelegramClient('session', self.api_id, self.api_hash)

    def send(self, message):
        self.client.connect()
        try:
            receiver = InputPeerUser(5330092176, 0)
            self.client.send_message(receiver, message, parse_mode='html')
        except Exception as e:
            print(e)
        self.client.disconnect()
