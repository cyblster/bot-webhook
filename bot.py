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
    "cryptospace — тариф base": -1001611757287,
    "cryptospace — тариф base x3": -1001667337121,
    "cryptospace — тариф vip": -1001661589284
}


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

    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM `users` WHERE LOWER(`email`) = '{email}'"
            )
            fetch = cursor.fetchone()

            if fetch is None:
                text = "Адрес электронной почты не найден. " \
                       "Если произошла ошибка, пожалуйста, свяжитесь с технической поддержкой @azamkhodzhaev_bot"
                bot.send_message(
                    chat_id=message.from_user.id,
                    text=text
                )

                return

            email, payment_rate, telegram_id, telegram_username = fetch
            if telegram_id:
                text = "Адрес электронной почты уже используется. " \
                       "Если произошла ошибка, пожалуйста, свяжитесь с технической поддержкой @azamkhodzhaev_bot"

                bot.send_message(
                    chat_id=message.from_user.id,
                    text=text
                )

                return

            telegram_id = message.from_user.id
            telegram_username = message.from_user.username

            channel_id = payment_rates.get(payment_rate.lower())
            if channel_id is None:
                return

            invite_chat_link = bot.create_chat_invite_link(
                chat_id=channel_id,
                member_limit=1,
                expire_date=datetime.now() + timedelta(days=7)
            ).invite_link

            text = f"Ваша ссылка на Telegram-канал: {invite_chat_link}"
            bot.send_message(
                chat_id=message.from_user.id,
                text=text
            )

            if telegram_username:
                cursor.execute(
                    f"UPDATE `users` SET `telegram_id` = '{telegram_id}', `telegram_username` = '{telegram_username}' "
                    f"WHERE LOWER(`email`) = '{email}'"
                )
            else:
                cursor.execute(
                    f"UPDATE `users` SET `telegram_id` = '{telegram_id}' WHERE LOWER(`email`) = '{email}'"
                )

            connection.commit()


@server.route(f"/{APP_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])

    return "!", 200


@server.route('/add', methods=["GET"])
def add():
    email = request.args.get("email").lower()
    payment_rate = request.args.get("payment_rate").lower()

    if email is None or payment_rate is None:
        return "!", 400

    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    f"INSERT INTO `users` (`email`, `payment_rate`) VALUES ('{email}', '{payment_rate}')"
                )
            except pymysql.IntegrityError:
                cursor.execute(
                    f"UPDATE `users` SET `payment_rate` = '{payment_rate}' WHERE LOWER(`email`) = '{email}'"
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
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM `users` WHERE LOWER(`email`) = '{email}'"
            )
            fetch = cursor.fetchone()
            if fetch is None:
                return

            email, payment_rate, telegram_id = fetch
            if telegram_id:
                channel_id = payment_rates.get(payment_rate.lower())
                if channel_id is None:
                    return

                bot.kick_chat_member(
                    chat_id=channel_id,
                    user_id=telegram_id
                )
                bot.unban_chat_member(
                    chat_id=channel_id,
                    user_id=telegram_id
                )

                text = "Ваш период оплаты курса закончился. " \
                       "Если произошла ошибка, пожалуйста, свяжитесь с технической поддержкой @azamkhodzhaev_bot"
                bot.send_message(
                    chat_id=telegram_id,
                    text=text
                )

            cursor.execute(
                f"DELETE FROM `users` WHERE LOWER(`email`) = '{email}'"
            )
            connection.commit()

    return "!", 200


@server.route('/username_by_email', methods=["GET"])
def username_by_email():
    email = request.args.get("email")
    if email is None:
        return "!", 400

    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT `telegram_username` FROM `users` WHERE LOWER(`email`) = '{email}'"
            )
            fetch = cursor.fetchone()
            return fetch, 200 if fetch else "", 400


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + APP_TOKEN)
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
