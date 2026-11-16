import os

import telebot
import requests
import json
import threading
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
webhook_url = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(API_KEY)

media_files = {}
media_timers = {}
media_text = {}


def send_album(group_id, text):
    files = {}

    for i, item in enumerate(media_files[group_id]):
        files[f"files[{i}]"] = (
            f"photo_{i}.jpg",
            item,
            "image/jpeg"
        )

    payload = {
        "payload_json": json.dumps({
            "content": text,
            "username": "repeater bot"
        })
    }

    r = requests.post(webhook_url, files=files, data=payload)
    r.raise_for_status()

    del media_files[group_id]
    del media_timers[group_id]
    del media_text[group_id]


def send_photo(downloaded, text):
    files = {
        "file": ("photo.jpg", downloaded, "image/jpeg")
    }

    payload = {
        "payload_json": json.dumps({
            "content": text,
            "username": "repeater bot"
        })
    }

    r = requests.post(webhook_url, files=files, data=payload)
    r.raise_for_status()


@bot.channel_post_handler(content_types=['text'])
def echo_message(message):
    payload = {
        "payload_json": json.dumps({
            "content": message.text,
            "username": "repeater bot"
        })
    }

    r = requests.post(webhook_url, data=payload)
    r.raise_for_status()


@bot.channel_post_handler(content_types=['photo'])
def photo_handler(message):
    if not message.media_group_id:
        media = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(media.file_path)

        send_photo(downloaded, message.caption or "")

    else:
        group_id = message.media_group_id

        if group_id not in media_files:
            media_files[group_id] = []
            media_text[group_id] = ""

        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        media_files[group_id].append(downloaded)

        #caption saving
        if message.caption:
            media_text[group_id] = message.caption

        #timer reset
        if group_id in media_timers:
            media_timers[group_id].cancel()

        media_timers[group_id] = threading.Timer(
            5,
            send_album,
            args=[group_id, media_text[group_id]]
        )

        media_timers[group_id].start()


bot.infinity_polling(
    timeout=10,
    long_polling_timeout=5
)
