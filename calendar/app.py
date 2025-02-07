from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Замени на свой секретный ключ
DATABASE = "database.db"


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_text TEXT NOT NULL,
                event_time INTEGER NOT NULL,
                reminder_time INTEGER NOT NULL,
                notified INTEGER DEFAULT 0
            )
        ''')
        conn.commit()


# Инициализация базы данных при запуске приложения
init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    # Если пользователь зашёл по ссылке с ?user_id=..., подставляем его ID
    user_id = request.args.get("user_id")
    if request.method == "POST":
        user_id = request.form.get("user_id")
        event_text = request.form.get("event_text")
        event_time_str = request.form.get("event_time")
        reminder_time_str = request.form.get("reminder_time")

        if not (user_id and event_text and event_time_str and reminder_time_str):
            flash("Пожалуйста, заполните все поля.", "danger")
            return redirect(url_for("index", user_id=user_id))

        try:
            # Преобразуем введённое время в Unix timestamp
            event_time = int(datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M").timestamp())
            reminder_time = int(datetime.strptime(reminder_time_str, "%Y-%m-%dT%H:%M").timestamp())
        except ValueError:
            flash("Неверный формат даты/времени.", "danger")
            return redirect(url_for("index", user_id=user_id))

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (user_id, event_text, event_time, reminder_time) VALUES (?, ?, ?, ?)",
                (user_id, event_text, event_time, reminder_time)
            )
            conn.commit()
        flash("Событие успешно добавлено!", "success")
        return redirect(url_for("index", user_id=user_id))

    return render_template("index.html", user_id=user_id)


if __name__ == "__main__":
    app.run(debug=True)
