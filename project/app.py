from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from flask_cloudflared import run_with_cloudflared
from db_controller import init_db  # Импортируем инициализацию БД

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Задайте свой секретный ключ
DATABASE = "database.db"
run_with_cloudflared(app)

# Инициализируем БД (если ещё не создана)
init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    # Получаем Telegram User ID из query-параметра (например, ?user_id=123456789)
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
            # Преобразуем введённое время (формат datetime-local) в Unix timestamp
            event_time = int(datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M").timestamp())
            reminder_time = int(datetime.strptime(reminder_time_str, "%Y-%m-%dT%H:%M").timestamp())
        except ValueError:
            flash("Неверный формат даты/времени.", "danger")
            return redirect(url_for("index", user_id=user_id))

        # Сохраняем событие в БД
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
    app.run(host='0.0.0.0', port=5000, debug=True)
