import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events


class Telegram:

    def __init__(self):
        self.api_id = 15901021
        self.api_hash = ''
        self.token = ''
        self.phone = ''
        self.client = TelegramClient('session', self.api_id, self.api_hash)

    def send(self, message):
        self.client.connect()
        try:
            receiver = InputPeerUser(, 0)
            self.client.send_message(receiver, message, parse_mode='html')
        except Exception as e:
            print(e)
        self.client.disconnect()
