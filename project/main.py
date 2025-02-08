import subprocess
import re
import time
import sys


def launch_app():
    """
    Запускаем app.py и ищем в выводе первую строку с HTTPS-доменом.
    """
    proc = subprocess.Popen(
        [sys.executable, "-u", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    domain = None
    start_time = time.time()
    timeout = 30  # ждём до 30 секунд

    while True:
        # Если истёк таймаут, прекращаем ожидание
        if time.time() - start_time > timeout:
            break

        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue

        print(line, end="")  # выводим строку на консоль

        # Ищем строку вида: Running on https://...
        match = re.search(r"Running on (https://\S+)", line)
        if match:
            domain = match.group(1)
            # Если домен содержит trycloudflare, скорее всего, это нужная строка
            if "trycloudflare" in domain:
                break

    return proc, domain


def update_keys(domain, keys_file="keys.py"):
    """
    Обновляем в файле keys.py значение переменной domen.
    Если строка уже есть, заменяем её, иначе добавляем.
    """
    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    if "domen" in content:
        new_content = re.sub(r"^domen\s*=\s*['\"].*?['\"]", f"domen = '{domain}'", content, flags=re.M)
    else:
        new_content = content + f"\ndomen = '{domain}'\n"

    with open(keys_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[INFO] keys.py обновлён: domen = '{domain}'")


def launch_bot():
    """Запускаем bot.py в отдельном процессе."""
    bot_proc = subprocess.Popen([sys.executable, "bot.py"])
    return bot_proc


def main():
    print("[INFO] Запускаем web-сервер (app.py)...")
    app_proc, domain = launch_app()

    if domain is None:
        print("[ERROR] Не удалось получить домен из app.py. Проверьте вывод и настройки cloudflared.")
        app_proc.terminate()
        sys.exit(1)

    update_keys(domain)

    print("[INFO] Запускаем Telegram-бота (bot.py)...")
    bot_proc = launch_bot()

    try:
        # Поддерживаем работу мастер-скрипта, пока работают дочерние процессы
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Остановка процессов...")
        app_proc.terminate()
        bot_proc.terminate()


if __name__ == "__main__":
    main()
