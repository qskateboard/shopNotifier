import datetime

from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    nickname = db.Column(db.String(1000))
    password = db.Column(db.String(100))
    telegram_id = db.Column(db.Integer)
    alerts = db.Column(db.String(1000))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    count = db.Column(db.Integer)
    price = db.Column(db.Integer)
    player = db.Column(db.String(1000))
    seller = db.Column(db.String(1000))
    balance = db.Column(db.Integer)
    time = db.Column(db.DateTime)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer)
    message = db.Column(db.Text)
    seen = db.Column(db.Boolean)
    time = db.Column(db.DateTime)


class Medium(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    sell = db.Column(db.Integer)
    buy = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    server = db.Column(db.Integer)


class all_goods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)