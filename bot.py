import os

import flask
import pymysql
import telebot

from flask import Flask, request


server = Flask(__name__)
bot = telebot.TeleBot(os.environ.get("webhook_token"))


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{os.environ.get('webhook_url')}{os.environ.get('webhook_token')}")

    print(request.args)
    return flask.Response(status=200)


@server.route('/add')
def add():
    email = request.args.get("email")
    payment_rate = request.args.get("payment_rate")

    if email is None or payment_rate is None:
        return flask.Response(status=400)

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

    return flask.Response(status=200)


@server.route('/remove')
def remove():
    email = request.args.get("email")
    if email is None:
        return flask.Response(status=400)

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

    return flask.Response(status=200)


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
