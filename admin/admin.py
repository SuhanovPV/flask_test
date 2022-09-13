from flask import Blueprint, request, redirect, url_for, flash, render_template, session

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')
menu = [{'url': '.index', 'title': 'Панель'},
        {'url': '.logout', 'title': 'Выйти'}]


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
