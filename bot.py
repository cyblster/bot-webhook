import os

import pymysql
import telebot
import logging

from flask import Flask, request
from datetime import datetime, timedelta


APP_URL = os.environ.get("webhook_url")
APP_TOKEN = os.environ.get("webhook_token")
MYSQL_HOST = os.environ.get("mysql_host")
MYSQL_USER = os.environ.get("mysql_user")
MYSQL_PASSWORD = os.environ.get("mysql_password")
MYSQL_DATABASE = os.environ.get("mysql_database")


server = Flask(__name__)
bot = telebot.TeleBot(APP_TOKEN)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

email_regexp = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

payment_rates = {
    "Тариф - Base x3": -1001750121173,
    "Тариф - Base x6": -1001229801856,
    "Тариф - VIP x6": -1001531945348,
    "Тариф - Super VIP x12": -1001601848724
}


def mysql_query(query):
    connection = pymysql.connect(
        host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD,
        db=MYSQL_DATABASE, autocommit=True
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            return cursor


@bot.message_handler(commands=["start"], chat_types=["private"])
def command_start(message):
    text = "Для получения ссылки на закрытый канал Азама Ходжаева " \
           "напишите адрес электронной почты, указанный при Вашей покупке."

    bot.send_message(
        chat_id=message.from_user.id,
        text=text
    )


@bot.message_handler(regexp=email_regexp, chat_types=["private"])
def message_email(message):
    email = message.text.lower()

    cursor = mysql_query(f"SELECT * FROM `users` WHERE `email` = '{email}' AND `telegram_id` IS NULL")
    if not cursor:
        return

    fetchall = cursor.fetchall()

    if not fetchall:
        text = "Адрес электронной почты не найден или уже используется. " \
               "Если произошла ошибка, пожалуйста, свяжитесь с технической поддержкой @azamkhodzhaev_bot"

        bot.send_message(
            chat_id=message.from_user.id,
            text=text
        )

        return

    for fetch in fetchall:
        payment_id, payment_rate, email, telegram_id, telegram_username, telegram_firstname, telegram_lastname = fetch

        telegram_id = message.from_user.id
        telegram_username = message.from_user.username
        telegram_firstname = message.from_user.first_name
        telegram_lastname = message.from_user.last_name

        channel_id = payment_rates.get(payment_rate)
        if not channel_id:
            return

        invite_chat_link = bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=datetime.now() + timedelta(days=7)
        ).invite_link

        text = f"Ваша ссылка на Telegram-канал ({payment_rate}): {invite_chat_link}"
        bot.send_message(
            chat_id=message.from_user.id,
            text=text
        )

        mysql_query(
            f"UPDATE `users` SET `telegram_id` = '{telegram_id}' "
            f"WHERE `payment_id` = '{payment_id}'"
        )

        if telegram_username:
            mysql_query(
                f"UPDATE `users` SET `telegram_username` = '{telegram_username}' "
                f"WHERE `payment_id` = '{payment_id}'"
            )

        if telegram_firstname:
            mysql_query(
                f"UPDATE `users` SET `telegram_firstname` = '{telegram_firstname}' "
                f"WHERE `payment_id` = '{payment_id}'"
            )

        if telegram_lastname:
            mysql_query(
                f"UPDATE `users` SET `telegram_lastname` = '{telegram_lastname}' "
                f"WHERE `payment_id` = '{payment_id}'"
            )


@server.route(f"/{APP_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])

    return "!", 200


@server.route("/add", methods=["GET"])
def mysql_add():
    payment_link = request.args.get("payment_link")
    payment_rate = request.args.get("payment_rate")
    email = request.args.get("email")
    if payment_link is None or payment_rate is None or email is None:
        return "!", 400

    payment_id = payment_link.split("/")[-1]

    mysql_query(
        f"INSERT INTO `users` (`payment_id`, `payment_rate`, `email`) "
        f"VALUES ('{payment_id}', '{payment_rate}', '{email}')"
    )
    return "!", 200


@server.route("/remove", methods=["GET"])
def mysql_remove():
    payment_link = request.args.get("payment_link")
    if payment_link is None:
        return "!", 400

    payment_id = payment_link.split('/')[:-1]

    mysql_query(
        f"DELETE FROM `users` WHERE `payment_id` = '{payment_id}'"
    )
    return "!", 200


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + APP_TOKEN)
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
