from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import datetime
import requests

app = Flask(__name__)
app.secret_key = "luckypass"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///luckybox.db'
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    balance = db.Column(db.Float, default=0.0)
    prizes = db.Column(db.String(500), default="")

# Модель пополнений
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))
    amount = db.Column(db.Float)
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

db.create_all()

# Интерфейс (упрощённый)
template = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>LuckyBox</title>
  <style>
    body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; }
    input, button { padding: 10px; margin: 5px; border-radius: 8px; border: none; }
    .case { margin: 30px auto; padding: 20px; background: #1e293b; border-radius: 20px; width: 300px; }
    .spin { animation: spin 1s linear; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>
  {% if session.get('email') %}
    <h2>Привет, {{session.email}} | Баланс: ${{user.balance}}</h2>
    <form method="post" action="/logout"><button>Выйти</button></form>
    <form method="post" action="/pay"><input name="amount" type="number" placeholder="Сумма $"><button>Пополнить</button></form>
    <div class="case">
      <h3>💎 Premium Кейс</h3>
      <form method="post" action="/open_case"><button>Открыть за 5$</button></form>
    </div>
    <h3>Ваши призы:</h3>
    <p>{{user.prizes}}</p>
    <form method="post" action="/withdraw"><button>Запросить выплату</button></form>
  {% else %}
    <h2>Вход / Регистрация</h2>
    <form method="post" action="/login">
      <input name="email" placeholder="Email">
      <input name="password" type="password" placeholder="Пароль">
      <button>Войти / Зарегистрироваться</button>
    </form>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'logout' in request.form:
            session.clear()
            return redirect("/")
        if 'email' in request.form:
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user:
                if user.password == password:
                    session['email'] = user.email
            else:
                new_user = User(email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                session['email'] = email
            return redirect("/")
    user = None
    if session.get('email'):
        user = User.query.filter_by(email=session['email']).first()
    return render_template_string(template, user=user)

@app.route("/open_case", methods=["POST"])
def open_case():
    user = User.query.filter_by(email=session['email']).first()
    if user.balance < 5:
        return "Недостаточно средств"
    user.balance -= 5
    prize = get_random_prize()
    user.prizes += prize + ", "
    db.session.commit()
    return f"<h2>Выпал приз: {prize}</h2><a href='/'>Назад</a>"

def get_random_prize():
    roll = random.randint(1, 1000)
    if roll <= 400:
        return "💵 1$"
    elif roll <= 600:
        return "💵 10$"
    elif roll <= 610:
        return "📱 iPhone 15"
    elif roll <= 620:
        return "🎮 PS5"
    elif roll <= 630:
        return "💵 100$"
    else:
        return "❌ Ничего"

@app.route("/pay", methods=["POST"])
def pay():
    user = User.query.filter_by(email=session['email']).first()
    amount = float(request.form['amount'])
    payment = Payment(user_email=user.email, amount=amount)
    db.session.add(payment)
    user.balance += amount
    db.session.commit()
    return redirect("/")

@app.route("/withdraw", methods=["POST"])
def withdraw():
    user = User.query.filter_by(email=session['email']).first()
    return f"<h3>Заявка на вывод отправлена. Мы переведём средства на карту 4149 6090 4170 7177</h3><a href='/'>Назад</a>"

if __name__ == "__main__":
    app.run(debug=True)
