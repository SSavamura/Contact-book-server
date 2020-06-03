from config import *
import re
from flask import Flask, render_template, redirect, request, url_for
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from database import TechDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, time
import random
from json import dumps as jdumps

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = SECRET_KEY
app.config["MYSQL_HOST"] = HOST_ADRESS
app.config["MYSQL_USER"] = USERNAME
app.config["MYSQL_PASSWORD"] = PASSWORD
app.config["MYSQL_DB"] = DATABASE
mysql = MySQL(app)

app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD

mail = Mail(app)


def sendmail(recipients: str, url: str):
    msg = Message("Смена пароля", recipients=[recipients])
    msg.html = "<H2 align='center'>Смена пароля</H1>\n" \
               f"<H3 align='center'>Для смены пароля нажмите на <a href='{url}'>ссылку.</a></H2>" \
               "<H3 align='center'>Если вы не делали запрос на смену пароля, то обратитесь к <a href='https://vk.com/s.savamura'>автору.</a></H2>"
    mail.send(msg)


def keyGenerator():
    chars = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    key = ""
    for i in range(26):
        key += random.choice(chars)
    return key


def updateKeyInDB(username: str):
    user_key = keyGenerator()
    user_row = users_key_database.getRow("username", username)
    if user_row != "null":
        users_key_database.updateRow("user_key", user_key, "username", username)
    else:
        users_key_database.addSomeRow(("username", "user_key"), (username, user_key))

    return user_key


def checkTime(mysql):
    password_recovery_database = TechDataBase(mysql, "password_recovery")  # INIT Базы с восстановлением юзеров
    expires = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    password_recovery_database.delRowByCond(f"expires < '{expires}'")


@app.before_first_request
def before_first_request():
    pass


@app.before_request  # Выполняется перед запросом
def before_request():
    global users_database, users_key_database
    users_database = TechDataBase(mysql, "user")  # INIT Базы с юзерами
    users_key_database = TechDataBase(mysql, "user_key")  # INIT Базы с ключами узеров
    checkTime(mysql)


@app.after_request  # Выполняется после запроса
def after_request(response):
    mysql.connection.commit()  # Применение изменений в базе
    return response


@app.route("/")  # Глав страница
def index():
    return render_template("index.html")


@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        data = request.json  # Получение значение из принятого json`а
        if data:
            username = data.get("Username")
            password = data.get("Password")
            email = data.get("Email")
            if username and password and email:
                find_user_name = users_database.getRow("username", username)
                if find_user_name == "null":
                    find_user_email = users_database.getRow("email", email)
                    if find_user_email == "null":
                        hash_password = generate_password_hash(password)  # Хеширование пароля
                        users_database.addSomeRow(("username", "password", "email"), (username, hash_password, email))
                        return {"login_status": True, "key": updateKeyInDB(username)}
                    else:
                        return {"error": "This email is already taken"}
                else:
                    return {"error": "This username is already taken"}
            else:
                return {"error": "Username, Password or email is NULL"}
        else:
            return {"error": "Data is NULL"}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.route("/deleteaccount", methods=["GET", "POST"])
def deleteAccount():
    if request.method == "POST":
        data = request.json
        if data:
            username = data.get("Username")
            password = data.get("Password")
            if username and password:
                real_password = users_database.getRow("username", username)[2]  # Получение настоящего пароля из бд
                if check_password_hash(real_password, password):  # Сравнение паролей
                    users_database.delRow("username", username)
                    return {"done": True}
                else:
                    return {"done": False}
            else:
                return {"error": "Username or Password is NULL"}
        else:
            return {"error": "Data is NULL"}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        if data:
            username = data.get("Username")
            password = data.get("Password")
            if username and password:
                real_password = users_database.getRow("username", username)[2]  # Получение настоящего пароля из бд
                if check_password_hash(real_password, password):  # Сравнение паролей
                    return {"login_status": True, "key": updateKeyInDB(username)}
                else:
                    return {"login_status": False}
            else:
                return {"error": "Username or Password is NULL"}
        else:
            return {"error": "Data is NULL"}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        data = request.json
        if data:
            username = data.get("Username")
            if username:
                users_key_database.delRow("username", username)
                return {"login_status": False}
            else:
                return {"error": "Username is NULL"}
        else:
            return {"error": "Data is NULL"}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.route("/emailconfirm", methods=["GET", "POST"])
def emailconfirm():
    password_recovery_database = TechDataBase(mysql, "password_recovery")  # INIT Базы с восстановления
    message = None
    if request.method == "POST":
        email_form = request.form.get("email")
        email = re.search(r"[\w.-]+@[\w.-]+\.?[\w]+?", email_form)
        if email:
            userrow = users_database.getRow("email", email.group())  # Поиск почты в бд
            if userrow != "null":
                access_hash = generate_password_hash(time.ctime())
                expires = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
                password_recovery_database.delRow("user_id", userrow[0])
                password_recovery_database.addSomeRow(("user_id", "access_hash", "expires"),
                                                      (userrow[0], access_hash, expires))
                sendmail(userrow[3], url_for("passwordreset", _external=True, user_id=userrow[0], access_hash=access_hash))
                message = "На вашу почту было отправленно сообшение для смены пароля."
        else:
            message = "Не правильно введены данные!"

    return render_template("form_email_confirm.html", msg=message)


@app.route("/passwordreset", methods=["GET", "POST"])
def passwordreset():
    password_recovery_database = TechDataBase(mysql, "password_recovery")  # INIT Базы с восстановлением юзеров
    message = None
    user_id = request.args.get("user_id", type=int)
    access_hash = request.args.get("access_hash")
    if request.method == "POST":
        new_password = request.form.get("new_password")
        repeat_password = request.form.get("repeat_password")
        if new_password:
            res = (re.search(p, new_password) for p in ('[A-Z]', '\d', '[a-z]'))
            if len(new_password) >= 8 and all(res):
                if new_password == repeat_password:
                    hash_password = generate_password_hash(new_password)
                    users_database.updateRow("password", hash_password, "user_id", user_id)
                    password_recovery_database.delRow("user_id", user_id)
                    return redirect(url_for("index"))
                else:
                    message = "Подтверждение не совпадает с новым паролем."
            else:
                message = "Пароль должен быть длинее 8 символов и содержать символы верхнего и нижнего регистра латинского алфавита."
        else:
            message = "Пароль не может быть пустым."
    if user_id and access_hash:
        result = password_recovery_database.getRow("user_id", user_id)
        if user_id == result[0] and access_hash == result[1]:
            return render_template("new_pass_form.html", msg=message)
    else:
        message = "Ссылка не корректная!"

    return render_template("pass_url_error.html", msg=message)


@app.route("/users/<string:username>", methods=["GET", "POST"])
def user(username):
    if request.method == "POST":
        user_key = users_key_database.getRow("username", username)[1]
        if request.args.get("key") == user_key:  # Сравнение входящего ключа и ключа пользователя.
            user_database = TechDataBase(mysql, username)  # INIT базы пользователя
            data = request.json
            if data:
                name = data.get("Name")
                number = data.get("Number")
            if request.args.get("option") == "add":
                if name and number:
                    contact_row = user_database.getRow("name", name)
                    if contact_row != (name, number):
                        user_database.addSomeRow(('name', 'number'), (name, number))
                        return {"done": True}
                    else:
                        return {"done": False}
                else:
                    return {"error": "Name or Number is NULL"}
            elif request.args.get("option") == "delete":
                if name:
                    user_database.delRow('name', name)
                    return {"done": True}
                else:
                    return {"error": "Name is NULL"}
            elif request.args.get("option") == "show":
                return jdumps(user_database.getAllValue())
            else:
                return {"error": "Option is not specified"}
        else:
            return {"error": "Key is not specified"}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.route("/status", methods=["GET", "POST"])
def status():
    if request.method == "POST":
        return {"status": True, "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S")}
    else:
        return redirect(url_for("index"))  # Перенаправление на главную


@app.errorhandler(404)  # Исключение при 404
def http_404_handler(error):
    return redirect(url_for("index"))  # Перенаправление на главную


@app.errorhandler(500)  # Исключение при 500
def http_500_handler(error):
    return redirect(url_for("index"))  # Перенаправление на главную


if __name__ == "__main__":
    app.run()
