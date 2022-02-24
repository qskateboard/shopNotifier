from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Проверьте введенные данные, логин или пароль неверны')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('main.dashboard'))


@auth.route('/signup')
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('register.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    mark = request.form.get('mark')

    if email == "" or name == "" or password == "" or password2 == "":
        flash('Некоторые поля не заполнены')
        return redirect(url_for('auth.signup'))

    if password != password2:
        flash('Введенные пароли не совпадают')
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Пользователь с такой почтой уже зарегистрирован')
        return redirect(url_for('auth.signup'))

    new_user = User(email=email, nickname=name, password=generate_password_hash(password, method='sha256'))
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index_page'))