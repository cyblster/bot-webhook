import os

import flask
import pymysql
import telebot
import logging

from flask import Flask, request


server = Flask(__name__)
bot = telebot.TeleBot(os.environ.get("webhook_token"))
logger = telebot.logger
logger.setLevel(logging.DEBUG)

email_regexp = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


@bot.message_handler(commands=["start"], chat_types=["private"])
def command_start(message):
    text = """
Для получения ссылки на канал с торговыми рекомендациями
напишите свой e-mail, указанный при регистрации и покупке.
"""

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
                f"SELECT `telegram_id` FROM `users` WHERE `email` = '{email}'"
            )
            if cursor.fetchone():
                print("Yes")
            else:
                print("No!")


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
