import os
import pymysql

from flask import Flask, request


server = Flask(__name__)

count = 0


@server.route('/add')
def add():
    global count
    email = request.args.get("email")
    payment_rate = request.args.get("payment_rate")

    if email is None or payment_rate is None:
        return ""

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
    count += 1
    print(count)
    return ""


@server.route('/remove')
def remove():
    email = request.args.get("email")
    if email is None:
        return

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

    return ""


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
