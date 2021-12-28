import os
import telebot
from flask import Flask, request

server = Flask(__name__)

logs = []


@server.route('/')
def webhook():
    return str(request.args)


@server.route('/logs')
def logs():
    return ""


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
