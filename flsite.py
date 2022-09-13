from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
import sqlite3
import os
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from UserLogin import UserLogin
from forms import LoginForm, RegisterForm
from admin.admin import admin

DATABASE = 'tmp/flsite.db'
DEBUG = True
# os.urandom(20).hex()
SECRET_KEY = 'a062128f434c7b1220c4e076b67fc38244ae21eb'
MAX_CONTENT_LENGTH = 1024 * 1024

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Авторизуйтесь для доступа к странице'
login_manager.login_message_category = "success"
dbase = None


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().from_DB(user_id, dbase)


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route("/")
def index():
    if 'vivists' in session:
        session['vivists'] = session.get('vivists') + 1
    else:
        session['vivists'] = 1
    return render_template("index.html", menu=dbase.get_menu(), posts=dbase.get_posts_anounce(),
                           visit=session['vivists'])


@app.route("/add_post", methods=["POST", "GET"])
@login_required
def add_post():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.add_post(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья успешно добавлена', category='success')
        else:
            flash('Ошибка добавления статьи', category='error')
    return render_template('add_post.html', menu=dbase.get_menu(), title='Добавление статьи')


@app.route("/post/<alias>")
@login_required
def show_post(alias):
    title, post = dbase.get_post(alias)
    if not title:
        abort(404)
    return render_template('post.html', menu=dbase.get_menu(), title=title, post=post)


@app.route("/about")
def about():
    content = render_template("about.html", title="О сайте", menu=dbase.get_menu())
    res = make_response(content)
    res.headers['Content-Type'] = 'text/html'
    res.headers['Server'] = 'flasksite'
    return res


@app.route("/picture")
@login_required
def picture():
    img = None
    with app.open_resource(app.root_path + "/static/images/1.gif", mode="rb") as f:
        img = f.read()
    if img is None:
        return "No image"
    res = make_response(img)
    res.headers['Content-type'] = 'image/gif'
    return res


@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', title="О пользователе", menu=dbase.get_menu())


@app.route('/userava')
@login_required
def userava():
    img = current_user.get_avatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = "image/jpeg"
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verify_ext(file.filename):
            try:
                img = file.read()
                res = dbase.update_user_avatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар успешно обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")
    return redirect(url_for('profile'))


@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправления', category='error')
    return render_template('contact.html', title="Обратная связь", menu=dbase.get_menu())


@app.route("/login", methods=['POST', 'GET'])
def login():
    menu = dbase.get_menu()
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.get_user_by_email(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            user_login = UserLogin().create(user)
            rm = form.remember.data
            login_user(user_login, remember=rm)
            if request.args.get("next") is None:
                return redirect(url_for('profile'))
            return redirect(request.args.get("next"))
        flash("Неверный логин, либо пароль", "error")
    return render_template("login.html", menu=menu, title="Авторизация", form=form)


@app.route("/register", methods=["POST", "GET"])
def register():
    menu = dbase.get_menu()
    form = RegisterForm()

    if form.validate_on_submit():
        p_hash = generate_password_hash(form.psw.data)
        res = dbase.add_user(form.name.data, form.email.data, p_hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template('register.html', menu=menu, title="Регистрация", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route("/transfer")
def transfer():
    return redirect(url_for('login'), 301)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html', title='Страница не найдена', menu=dbase.get_menu()), 404, \
           {'Content-type': 'text/html'}


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.after_request
def after_request(response):
    return response


@app.teardown_request
def teardown_request(response):
    return response


if __name__ == '__main__':
    app.run(debug=True)

# with app.test_request_context():
#     print(url_for('index'))
#     print(url_for('about'))
#     print(url_for('profile', username='suxar'))
