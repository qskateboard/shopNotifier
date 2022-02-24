import datetime
import json
import requests
import sqlalchemy

from flask import Blueprint, request, jsonify
from .models import User, Item, Alert, Medium, all_goods
from . import db

api = Blueprint('api', __name__)
t_api = "https://api.telegram.org/bot[token]/sendMessage"
api_url = "https://shopnotifier.pw/api/"


def send_telegram(item, user):
    data = {
        "chat_id": user.telegram_id,
        "parse_mode": "html",
        "text": "💸 <b>Новая {}</b>\n\n".format(item.type.replace("buy", "покупка").replace("sell", "продажа"))
    }
    if "name" in user.alerts:
        data['text'] += "🗒 Предмет: <b>{}</b>".format(item.name)
        if "count" in user.alerts:
            data['text'] += " <b>({})</b>\n".format(item.count)
        else:
            data['text'] += "\n"

    if "price" in user.alerts:
        data['text'] += "💰 Стоимость: <b>{}</b>\n".format(f"${item.price:,}")
    if "player" in user.alerts:
        data['text'] += "👤 Покупатель: <b>{}</b>\n".format(item.player)
    if "balance" in user.alerts:
        data['text'] += "💳 Баланс: <b>{}</b>\n".format(f"${item.balance:,}")
    requests.post(t_api, data=data)


@api.route("/alert/custom/<string:nick>")
def custom_alert(nick):
    action = request.args.get('type')
    if not action:
        return jsonify({"message": "All values dont passed"}), 400

    user_db = User.query.filter_by(nickname=nick).first()
    if not user_db:
        return jsonify({"message": "The specified user does not use this service"}), 401

    if user_db.telegram_id == 0:
        return jsonify({"message": "The specified user does not use telegram alerts"}), 401

    data = {
        "chat_id": user_db.telegram_id,
        "parse_mode": "html",
        "text": "",
    }
    alerts = user_db.alerts
    if action == "rent" and "rent" in alerts:
        data["text"] = "🎰 <b>Вы успешно поймали лавку</b>"
        requests.post(t_api, data=data)
        requests.get("{}add_alert/{}?message={}".format(api_url, user_db.id, "Успешно поймана лавка"))
        return jsonify({"message": "ok"})

    if action == "death" and "death" in alerts:
        data["text"] = "☠️ <b>Ваш персонаж погиб</b>"
        requests.post(t_api, data=data)
        requests.get("{}add_alert/{}?message={}".format(api_url, user_db.id, "Персонаж погиб"))
        return jsonify({"message": "ok"})

    if action == "disconnect" and "disconnect" in alerts:
        data["text"] = "❌ <b>Потерено подключение к серверу</b>"
        requests.post(t_api, data=data)
        requests.get("{}add_alert/{}?message={}".format(api_url, user_db.id, "Потеряно подключение к серверу"))
        return jsonify({"message": "ok"})

    else:
        return jsonify({"message": "selected action does not exist"})


@api.route("/alert/<string:tid>")
def test_alert(tid):
    items = "name,price,balance,count"
    user_db = User.query.filter_by(telegram_id=tid).first()
    if user_db:
        items = user_db.alerts
    send_telegram(Item(type="sell", name="Платиновая рулетка", price=4700000, count="10 шт", player="Alert_Test", seller="Test", balance=22736587, time=datetime.datetime.now()), User(telegram_id=tid, alerts=items))
    return jsonify({"status": "ok"})


@api.route("/status")
def status_code():
    return jsonify({"status": "ok"})


@api.route("/<string:user>/new_item", methods=['POST', 'GET'])
def add_new_item(user):
    item_name = request.args.get('item_name')
    item_count = request.args.get('item_count')
    item_price = request.args.get('item_price')
    order_type = request.args.get('order_type')
    player_name = request.args.get('player_name')
    balance = request.args.get('balance')

    if not item_name or not item_count or not item_price or not order_type or not player_name or not balance:
        return jsonify({"message": "All values dont passed"}), 400

    user_db = User.query.filter_by(nickname=user).first()
    if not user_db:
        return jsonify({"message": "The specified user does not use this service"}), 401

    new_item = Item(type=order_type, name=item_name, price=item_price, count=item_count, player=player_name, seller=user, balance=balance, time=datetime.datetime.now())
    db.session.add(new_item)
    db.session.commit()

    if user_db.telegram_id > 0:
        send_telegram(new_item, user_db)
    return jsonify({"message": "ok"}), 200


@api.route("/<string:user>/get_items/<int:count>")
def get_user_items(user, count):
    if not User.query.filter_by(nickname=user).first():
        return jsonify({"message": "The specified user does not use this service"}), 401

    row_items = Item.query.filter_by(seller=user).all()
    items = []
    for ritem in row_items:
        items.append({"id": ritem.id, "name": ritem.name, "type": ritem.type, "count": ritem.count, "price": ritem.price, "player": ritem.player, "balance": ritem.balance, "time": ritem.time})

    return jsonify(list(reversed(items))[:count])


@api.route("/get_medium/<string:server>")
def get_medium(server):
    row_items = Medium.query.filter_by(server=server).all()
    if not row_items:
        return jsonify({"message": "The specified server does not exist"})

    items = []
    for ritem in row_items:
        items.append(
            {"id": ritem.id, "name": ritem.name, "sell": ritem.sell, "buy": ritem.buy, "server": ritem.server, "time": ritem.time})

    return jsonify(list(reversed(items)))


@api.route("/update_medium/<int:server>", methods=['POST'])
def update_medium(server):
    new_items = request.json['array']
    if not new_items:
        return jsonify({"message": "There are no valid array with goods"})

    sql_query = sqlalchemy.text("DELETE FROM medium WHERE server={}".format(server))
    result = db.session.execute(sql_query)

    for item in new_items:
        print(item)
        new_alert = Medium(name=item['name'], sell=int(item['sell']), buy=int(item['buy']), time=datetime.datetime.now(), server=int(server))
        db.session.add(new_alert)
    db.session.commit()

    return jsonify({"status": "ok"})


@api.route("/update_goods", methods=['POST'])
def update_goods():
    new_items = request.json['array']
    print(new_items)
    if not new_items:
        return jsonify({"message": "There are no valid array with goods"})

    sql_query = sqlalchemy.text("DELETE FROM all_goods")
    result = db.session.execute(sql_query)

    for item in new_items:
        print(item)
        new_good = all_goods(name=item['name'])
        db.session.add(new_good)
    db.session.commit()

    return jsonify({"status": "ok"})


@api.route("/get_goods/")
def get_goods():
    row_items = all_goods.query.filter_by().all()
    medium = requests.get(api_url + "get_medium/16").json()
    items = []
    for ritem in row_items:
        resale = list(filter(lambda item: item['name'] == ritem.name, medium))
        buy, sell = 0, 0
        try:
            if resale[0]["buy"]:
                buy = resale[0]["buy"]
        except:
            pass
        try:
            if resale[0]["sell"]:
                sell = resale[0]["sell"]
        except:
            pass
        items.append(
            {"id": ritem.id, "name": ritem.name, "sell": sell, "buy": buy})

    return jsonify(list(reversed(items)))


@api.route("/getalerts/<string:uid>")
def get_alerts(uid):
    if not User.query.filter_by(id=uid).first():
        return jsonify({"message": "The specified user does not use this service"})

    row_items = Alert.query.filter_by(uid=uid, seen=False).all()
    items = []
    for ritem in row_items:
        items.append(
            {"id": ritem.id, "uid": ritem.uid, "message": ritem.message, "seen": ritem.seen, "time": ritem.time})

    return jsonify(list(reversed(items)))


@api.route("/addalert/<string:uid>")
def add_alert(uid):
    if not User.query.filter_by(id=uid).first():
        return jsonify({"message": "The specified user does not use this service"})

    message = request.args.get("message")
    new_alert = Alert(uid=uid, message=message, seen=False, time=datetime.datetime.now())
    db.session.add(new_alert)
    db.session.commit()

    return jsonify({"status": "ok"})


@api.route("/hidealert/<string:id>")
def hide_alert(id):
    alert = Alert.query.filter_by(id=id).first()
    if not alert:
        return jsonify({"message": "The specified alert does not exist"})

    alert.seen = True
    db.session.commit()

    return jsonify({"status": "ok"})


@api.route("/<string:user>/get_items/<int:count>/<string:sort>")
def get_user_items_by_date(user, count, sort):
    if not User.query.filter_by(nickname=user).first():
        return jsonify({"message": "The specified user does not use this service"}), 401

    row_items = Item.query.filter_by(seller=user).all()
    items = []
    date = datetime.datetime.now().timestamp() - 60 * 60 * 24 * 30
    if sort == "today":
        date = datetime.datetime.now().timestamp() - 60 * 60 * 24
    if sort == "weekly":
        date = datetime.datetime.now().timestamp() - 60 * 60 * 24 * 7

    for ritem in row_items:
        if date < ritem.time.timestamp():
            items.append({"id": ritem.id, "name": ritem.name, "type": ritem.type, "count": ritem.count, "price": ritem.price, "player": ritem.player, "balance": ritem.balance, "time": ritem.time})

    return jsonify(list(reversed(items))[:count])



@api.route("/<string:user>/get_items_by_type/<int:count>/<string:sort>")
def get_user_items_by_type(user, count, sort):
    if not User.query.filter_by(nickname=user).first():
        return jsonify({"message": "The specified user does not use this service"}), 401

    row_items = Item.query.filter_by(seller=user).all()
    items = []

    for ritem in row_items:
        if ritem.type == sort:
            items.append({"id": ritem.id, "name": ritem.name, "type": ritem.type, "count": ritem.count, "price": ritem.price, "player": ritem.player, "balance": ritem.balance, "time": ritem.time})

    return jsonify(list(reversed(items))[:count])


@api.route("/<string:user>/get_items_by_type/<int:count>/<string:sort>/<string:sort2>")
def get_user_items_by_type_and_date(user, count, sort, sort2):
    if not User.query.filter_by(nickname=user).first():
        return jsonify({"message": "The specified user does not use this service"}), 401

    row_items = Item.query.filter_by(seller=user).all()
    items = []
    date = datetime.datetime.now().timestamp() - 60 * 60 * 24 * 30
    if sort2 == "today":
        date = datetime.datetime.now().timestamp() - 60 * 60 * 24
    if sort2 == "weekly":
        date = datetime.datetime.now().timestamp() - 60 * 60 * 24 * 7
    for ritem in row_items:
        if ritem.type == sort and date < ritem.time.timestamp():
            items.append({"id": ritem.id, "name": ritem.name, "type": ritem.type, "count": ritem.count, "price": ritem.price, "player": ritem.player, "balance": ritem.balance, "time": ritem.time})

    return jsonify(list(reversed(items))[:count])


@api.route("/updates")
def get_updates():
    return jsonify({
        "url": request.host_url + "static/ShopNotifier.lua",
        "latest": open("./project/static/latest.txt").read(),
    })