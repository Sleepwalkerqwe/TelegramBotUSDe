import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx

# 🔧 Конфигурация
BOT_TOKEN = "твой_токен_сюда"
CHAT_ID = 870085433

# Настроим логирование
logging.basicConfig(level=logging.INFO)

# 📊 Функция для получения курса из API
async def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=usde&vs_currencies=usd"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data["usde"]["usd"]

# 🚀 Команда /startalert n y
async def startalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(context.args[0])  # каждые n минут
        y = int(context.args[1])  # в течение y минут
    except (IndexError, ValueError):
        await update.message.reply_text("Используй: /startalert <каждые_сколько_минут> <в_течение_скольки_минут>")
        return

    await update.message.reply_text(f"Ок! Буду слать курс каждые {n} минут в течение {y} минут.")

    # Запустим фоновую задачу
    asyncio.create_task(send_price_periodically(n, y))

# 📦 Фоновая задача
async def send_price_periodically(n, y):
    total_runs = y * 60 // (n * 60)  # сколько раз нужно отправить (но проще считать по времени)
    end_time = asyncio.get_event_loop().time() + y * 60

    while asyncio.get_event_loop().time() < end_time:
        price = await get_price()
        text = f"Текущий курс USDe: {price} USD"
        await app.bot.send_message(chat_id=CHAT_ID, text=text)
        await asyncio.sleep(n * 60)

# 🏁 main
async def main():
    global app
    app = Application.builder().token(BOT_TOKEN).build()

    # Добавим обработчик команды
    app.add_handler(CommandHandler("startalert", startalert))

    logging.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
