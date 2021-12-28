import os
import telebot
from flask import Flask, request

server = Flask(__name__)

arr = []


@server.route('/')
def webhook():
    arr.append(", ".join([f"{key}={value}" for key, value in request.args.items()]))
    print(arr[-1])
    return ", ".join([f"{key}={value}" for key, value in request.args.items()])


@server.route('/logs')
def logs():
    return "<br>".join(arr) if arr else ""


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
