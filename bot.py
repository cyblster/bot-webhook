import os

import flask
import pymysql
import telebot
import logging

from flask import Flask, request
from datetime import datetime, timedelta


server = Flask(__name__)
bot = telebot.TeleBot(os.environ.get("webhook_token"))
logger = telebot.logger
logger.setLevel(logging.DEBUG)

email_regexp = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

payment_rates = {
    "cryptospace — тариф base": -1001611757287,
    "cryptospace — тариф base x3": -1001667337121,
    "cryptospace — тариф vip": -1001661589284
}


@bot.message_handler(commands=["start"], chat_types=["private"])
def command_start(message):
    text = "Для получения ссылки на канал с торговыми рекомендациями " + \
           "напишите свой e-mail, указанный при регистрации и покупке."

    bot.send_message(
        chat_id=message.chat.id,
        text=text
    )


@bot.message_handler(regexp=email_regexp, chat_types=["private"])
def message_email(message):
    email = message.text

    connection = pymysql.connect(
        host=os.environ.get("mysql_host"),
        user=os.environ.get("mysql_user"),
        password=os.environ.get("mysql_password"),
        database=os.environ.get("mysql_database"),
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM `users` WHERE `email` = '{email}'"
            )
            fetch = cursor.fetchone()

            if fetch is None:
                text = "Почта не найдена."
                bot.send_message(
                    chat_id=message.chat.id,
                    text=text
                )

                return

            email, payment_rate, telegram_id = fetch
            if telegram_id:
                text = "Почта уже используется."

                bot.send_message(
                    chat_id=message.chat.id,
                    text=text
                )

            else:
                cursor.execute(
                    f"UPDATE `users` SET `telegram_id` = '{telegram_id}' WHERE `email` = '{email}'"
                )
                connection.commit()

                channel_id = payment_rates.get(payment_rate.lower())
                if channel_id is None:
                    return

                invite_chat_link = bot.create_chat_invite_link(
                    chat_id=channel_id,
                    member_limit=1,
                    expire_date=datetime.now() + timedelta(days=7)
                ).invite_link

                text = f"Ваша ссылка на канал: {invite_chat_link}"
                bot.send_message(
                    chat_id=message.chat.id,
                    text=text
                )


@server.route(f"/{os.environ.get('webhook_token')}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])

    return "!", 200


@server.route('/add', methods=["GET"])
def add():
    email = request.args.get("email")
    payment_rate = request.args.get("payment_rate")

    if email is None or payment_rate is None:
        return "!", 400

    connection = pymysql.connect(
        host=os.environ.get("mysql_host"),
        user=os.environ.get("mysql_user"),
        password=os.environ.get("mysql_password"),
        database=os.environ.get("mysql_database"),
    )
    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    f"INSERT INTO `users` (`email`, `payment_rate`) VALUES ('{email}', '{payment_rate}')"
                )
            except pymysql.IntegrityError:
                cursor.execute(
                    f"UPDATE `users` SET `payment_rate` = '{payment_rate}' WHERE `email` = '{email}'"
                )
            finally:
                connection.commit()

    return "!", 200


@server.route('/remove', methods=["GET"])
def remove():
    email = request.args.get("email")
    if email is None:
        return "!", 400

    connection = pymysql.connect(
        host=os.environ.get("mysql_host"),
        user=os.environ.get("mysql_user"),
        password=os.environ.get("mysql_password"),
        database=os.environ.get("mysql_database"),
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM `users` WHERE `email` = '{email}'"
            )
            connection.commit()

    return "!", 200


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=os.environ.get("webhook_url") + os.environ.get("webhook_token"))
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
