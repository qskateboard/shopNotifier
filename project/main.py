from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from colorhash import ColorHash
import requests
import datetime
from . import db

main = Blueprint('main', __name__)
api_url = "https://shopnotifier.pw/api/"


def round_price(price):
    if  -1000000 < price < 1000000:
        return str(price / 1000) + "K"
    elif 1000000 < price < 10000000 or -1000000 < price < -10000000 :
        return "{}M".format(round(price / 1000000, 2))
    else:
        return str(round(price / 1000000)) + "M"


def str2time(row):
    return datetime.datetime.strptime(row, "%a, %d %b %Y %H:%M:%S %Z")


def calc_perc(x, y):
    if y == 0:
        return 100
    if x == 0:
        return -100
    z = x / y * 100

    if z == 0 or z == 100:
        return 0
    if z > 100:
        return round(z) - 100
    return round(z - 100)


@main.route("/")
def index_page():
    return redirect(url_for('auth.login'))


@main.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "daily": {
            "earned": 0,
            "operations": 0,
            "difference_earned": {},
            "difference_operations": {},
            "sold": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "brought": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        },
        "2days": {
            "earned": 0,
            "operations": 0,
        },
        "weekly": {
            "earned": 0,
            "chart": {"earned": [0, 0, 0, 0, 0, 0, 0], "sell": [0, 0, 0, 0, 0, 0, 0], "buy": [0, 0, 0, 0, 0, 0, 0]},
            "operations": 0,
            "difference_earned": {},
            "difference_operations": {},
        },
        "2weekly": {
            "earned": 0,
            "operations": 0,
        },
    }
    all_operation = requests.get(api_url + current_user.nickname + "/get_items/1000000/monthly").json()
    last_moves = all_operation[:5]
    chart_days = [
        {"value": 0, "name": "Mon"},
        {"value": 1, "name": "Tue"},
        {"value": 2, "name": "Wed"},
        {"value": 3, "name": "Thu"},
        {"value": 4, "name": "Fri"},
        {"value": 5, "name": "Sat"},
        {"value": 6, "name": "Sun"},
    ]

    for operation in all_operation:
        time = str2time(operation['time'])
        curr_time = datetime.datetime.now().timestamp()
        if curr_time - 60 * 60 * 24 * 2 < time.timestamp() < curr_time - 60 * 60 * 24:
            stats['2days']['operations'] += 1
            if operation['type'] == "sell":
                stats['2days']['earned'] += operation['price']
            else:
                stats['2days']['earned'] -= operation['price']

        if time.timestamp() > curr_time - 60 * 60 * 24:
            stats['daily']['operations'] += 1
            if operation['type'] == "sell":
                stats['daily']['earned'] += operation['price']
                stats['daily']['sold'][time.hour] += operation['price']
            else:
                stats['daily']['earned'] -= operation['price']
                stats['daily']['brought'][time.hour] += operation['price']

        if time.timestamp() > curr_time - 60 * 60 * 24 * 7:
            stats['weekly']['operations'] += 1

            for day in chart_days:
                if day['name'] in operation['time']:
                    if operation['type'] == "sell":
                        stats['weekly']['chart']['earned'][day['value']] += operation['price']
                        stats['weekly']['chart']['sell'][day['value']] += operation['price']
                    else:
                        stats['weekly']['chart']['earned'][day['value']] -= operation['price']
                        stats['weekly']['chart']['buy'][day['value']] += operation['price']

            if operation['type'] == "sell":
                stats['weekly']['earned'] += operation['price']
            else:
                stats['weekly']['earned'] -= operation['price']

        if curr_time - 60 * 60 * 24 * 14 < time.timestamp() < curr_time - 60 * 60 * 24 * 7:
            stats['2weekly']['operations'] += 1
            if operation['type'] == "sell":
                stats['2weekly']['earned'] += operation['price']
            else:
                stats['2weekly']['earned'] -= operation['price']

    calc_arr = [["daily", "earned", "operations"], ["weekly", "earned", "operations"]]
    for item in calc_arr:
        for i in range(2):
            diff = calc_perc(stats[item[0]][item[i + 1]], stats["2" + item[0]][item[i + 1]])
            if diff > 0:
                stats[item[0]]['difference_' + item[i + 1]] = {'percent': "+{}%".format(diff), "arrow": "trending_up",
                                                               "style": "success"}
            else:
                stats[item[0]]['difference_' + item[i + 1]] = {'percent': "{}%".format(diff), "arrow": "trending_down",
                                                               "style": "danger"}

    # -- TODAY CHART VALUES --

    today_chart = {"sold": stats['daily']['sold'], "brought": stats['daily']['brought']}

    # -- TODAY CHART VALUES --
    alerts = requests.get(api_url + "getalerts/" + str(current_user.id)).json()
    aarr = {"count": len(alerts), "array": alerts}

    return render_template("dashboard.html",
                           username=current_user.nickname,
                           last_moves=last_moves,
                           total_money=round_price(stats['weekly']['earned']),
                           operations_all=stats['weekly']['operations'],
                           operations_today=stats['daily']['operations'],
                           earned_today=round_price(stats['daily']['earned']),
                           daily_difference=stats['daily']['difference_earned'],
                           daily_difference_operations=stats['daily']['difference_operations'],
                           weekly_difference = stats['weekly']['difference_earned'],
                           weekly_difference_operations = stats['weekly']['difference_operations'],
                           chart=stats['weekly']['chart'],
                           today_chart=today_chart,
                           alerts=aarr, title="Dashboard"
                           )


@main.route("/settings/telegram", methods=['GET', 'POST'])
@login_required
def telegram_settings():
    if request.method == 'POST':
        if request.args.get('tid'):
            current_user.telegram_id = request.args.get('tid')
            db.session.commit()
            return jsonify({'status': 'ok'})
        elif len(request.args) > 0:
            current_user.alerts = ','.join(request.args.to_dict(flat=False))
            db.session.commit()
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error'})
    else:
        keys = {"name": 0, "price": 1, "count": 2, "player": 3, "balance": 4, "rent": 5, "death": 6, "disconnect": 7}
        checkboxes = ["", "", "", "", "", "", "", ""]
        try:
            if len(current_user.alerts) > 0:
                for k in current_user.alerts.split(","):
                    if k in keys:
                        checkboxes[keys[k]] = "checked"
        except:
            pass

        alerts = requests.get(api_url + "getalerts/" + str(current_user.id)).json()
        aarr = {"count": len(alerts), "array": alerts}

        return render_template("telegram_settings.html",
                               telegram_id=current_user.telegram_id,
                               checkboxes=checkboxes,
                               alerts=aarr,
                               username=current_user.nickname, title="Telegram уведомления")


@main.route("/stats/sales")
def sales_page():
    r = requests.get(api_url + current_user.nickname + "/get_items/1000000/monthly").json()
    data = [item for item in r if item['type'] == "sell"]
    done, passed, result = [], [], []
    for item in data:
        if not item['name'] in passed:
            prices = [el['price'] for el in data if el['name'] == item['name']]
            counting = [int(str(el['count']).replace(" шт", "")) for el in data if el['name'] == item['name']]
            tmp = {"name": item['name'], "earned": sum(prices), "count": sum(counting)}
            done.append(tmp)
            passed.append(item['name'])

    charts = {
        "earned": [el['earned'] for el in done],
        "count": [el['count'] for el in done],
        "colors": ["rgb({0[0]}, {0[1]}, {0[2]})".format(ColorHash(el['name']).rgb) for el in done],
        "labels": [el['name'] for el in done ],
    }

    alerts = requests.get(api_url + "getalerts/" + str(current_user.id)).json()
    aarr = {"count": len(alerts), "array": alerts}

    return render_template('sales.html', charts=charts, data=r, alerts=aarr, username=current_user.nickname, title="Статиктика продаж")


@main.route("/stats/medium")
def medium_page():
    data = requests.get(api_url + "get_medium/16").json()

    alerts = requests.get(api_url + "getalerts/" + str(current_user.id)).json()
    aarr = {"count": len(alerts), "array": alerts}

    return render_template('medium.html', data=data, alerts=aarr, username=current_user.nickname, title="Средние цены")


@main.route("/buyout")
def buyout_page():
    goods = requests.get(api_url + "get_goods").json()

    alerts = requests.get(api_url + "getalerts/" + str(current_user.id)).json()
    aarr = {"count": len(alerts), "array": alerts}

    return render_template('buyout.html', goods=goods, alerts=aarr, username=current_user.nickname, title="Настройки скупки товара")


@main.route("/stats/")

@main.errorhandler(404)
def not_found_page(e):
    return render_template('404.html')


@main.errorhandler(500)
def server_error_page(e):
    return render_template('500.html')