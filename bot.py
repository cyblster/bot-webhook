import os
import telebot
from flask import Flask, request

server = Flask(__name__)

logs = []


@server.route('/')
def webhook():
    logs.append(f"{request.args}")
    return request.args


@server.route('/logs')
def logs():
    return "\n".join(logs) if logs else None


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
