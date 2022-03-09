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


@server.route("/add", methods=["GET"])
def mysql_add():
    payment_link = request.args.get("payment_id")
    payment_rate = request.args.get("payment_rate")
    email = request.args.get("email")
    if payment_link is None or payment_rate is None or email is None:
        return "!", 400

    payment_id = payment_link.split('/')[:-1]

    mysql_query(
        f"INSERT INTO `users` (`payment_id`, `payment_rate`, `email`) "
        f"VALUES ('{payment_id}', '{payment_rate}', '{email}')"
    )
    return "!", 200


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
