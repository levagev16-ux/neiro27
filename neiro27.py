import os
import threading

from dotenv import load_dotenv
from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Используем асинхронный клиент для стабильной версии mistralai==0.4.2
from mistralai.async_client import MistralAsyncClient

# Загружаем переменные окружения из .env (для локальных тестов)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Порт для Render
PORT = int(os.environ.get("PORT", 10000))

# Инициализируем клиент Mistral для старой версии SDK
client = MistralAsyncClient(api_key=MISTRAL_API_KEY)

# Flask-сервер для поддержки активности на Render
web = Flask(name)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Задавай вопросы только через команду:\n"
        "/ask <вопрос>"
    )


# Обработчик команды /ask
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Использование:\n"
            "/ask Твой вопрос"
        )
        return

    question = " ".join(context.args)

    try:
        # Асинхронный вызов в старой версии SDK (mistral-small вместо mistral-small-latest)
        response = await client.chat(
            model="mistral-small",
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = response.choices[0].message.content

        # Отправка ответа с разбивкой по лимиту Telegram (4096 символов)
        if len(answer) <= 4096:
            await update.message.reply_text(answer)
        else:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i + 4096])

    except Exception as e:
        await update.message.reply_text(f"Ошибка:\n{e}")


def main():
    # Запуск веб-сервера Flask в отдельном потоке
    threading.Thread(target=run_web, daemon=True).start()

    # Инициализация и настройка Telegram бота
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))

    print("Бот успешно запущен!")

    # Запуск бесконечного цикла опроса обновлений Telegram
    application.run_polling()


if name == "main":
    main()
