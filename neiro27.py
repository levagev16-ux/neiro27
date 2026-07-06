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

from mistralai.async_client import MistralAsyncClient

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Порт Render
PORT = int(os.environ.get("PORT", 10000))

# Mistral клиент
client = Mistral(api_key=MISTRAL_API_KEY)

# Flask для Render
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Задавай вопросы только через команду:\n"
        "/ask <вопрос>"
    )


# Команда /ask
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Использование:\n"
            "/ask Твой вопрос"
        )
        return

    question = " ".join(context.args)

    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = response.choices[0].message.content

        if len(answer) <= 4096:
            await update.message.reply_text(answer)
        else:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i + 4096])

    except Exception as e:
        await update.message.reply_text(f"Ошибка:\n{e}")


def main():
    # Запускаем Flask
    threading.Thread(target=run_web, daemon=True).start()

    # Telegram бот
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))

    print("Бот запущен!")

    application.run_polling()


if __name__ == "__main__":
    main()
