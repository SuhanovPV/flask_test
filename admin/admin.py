import sqlite3

from flask import Blueprint, request, redirect, url_for, flash, render_template, session, g

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')
menu = [{'url': '.index', 'title': 'Панель'},
        {'url': '.list_pubs', 'title': 'Статьи'},
        {'url': '.list_users', 'title': 'Пользователи'},
        {'url': '.logout', 'title': 'Выйти'}]

db = None


@admin.before_request
def before_request():
    global db
    db = g.get('link_db')


@admin.teardown_request
def teardown_request(req):
    global db
    db = None
    return req


@admin.route('/')
def index():
    if not is_logged():
        return redirect(url_for('.login'))
    return render_template('admin/index.html', menu=menu, title='Админ-панель')


def login_admin():
    session['admin_logged'] = 1


def is_logged():
    if session.get('admin_logged'):
        return True
    return False


def logout_admin():
    session.pop('admin_logged', None)


@admin.route('/login', methods=["POST", "GET"])
def login():
    if is_logged():
        return redirect(url_for('.index'))

    if request.method == 'POST':
        if request.form['user'] == "admin" and request.form['psw'] == "12345":
            login_admin()
            return redirect(url_for('.index'))
        else:
            flash("Невернаый логин или пароль", "error")
    return render_template('admin/login.html', title="Admin-панель")


@admin.route('/logout', methods=["POST", "GET"])
def logout():
    if not is_logged():
        return redirect(url_for('.login'))
    logout_admin()
    return redirect(url_for('.login'))


@admin.route('/list_pubs')
def list_pubs():
    if not is_logged():
        return redirect(url_for('.login'))

    list = []
    if db:
        try:
            cur = db.cursor()
            cur.execute(f"SELECT title, text, url FROM posts")
            list = cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения статей из БД " + str(e))
    return render_template("admin/listpubs.html", title="Список статуей", menu=menu, list=list)


@admin.route('/list_users')
def list_users():
    if not is_logged():
        return redirect(url_for('.login'))

    list = []
    if db:
        try:
            cur = db.cursor()
            cur.execute(f"SELECT name, email FROM users ORDER BY time DESC")
            list = cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения пользователей из БД " + str(e))
    return render_template("admin/listusers.html", title="Список пользователей", menu=menu, list=list)
