import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp  # для асинхронных HTTP-запросов
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен и chat_id (замени на свои)
TOKEN = "ТВОЙ_ТОКЕН"

# Пример API: CoinGecko
API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=usde&vs_currencies=usd"

# Функция для получения курса USDe
async def get_usde_price() -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            data = await response.json()
            # Возвращаем цену (если вдруг в API нет 'usde', будет KeyError)
            return data["usde"]["usd"]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот, который показывает курс USDe.\n"
        "Напиши /price чтобы узнать курс.\n"
        "Или /start_auto <interval_мин> <duration_мин>, чтобы я присылал курс каждые N минут в течение Y минут."
    )

# /price
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        current_price = await get_usde_price()
        await update.message.reply_text(f"Текущий курс USDe: {current_price} USD")
    except Exception as e:
        logger.error(f"Ошибка при получении курса: {e}")
        await update.message.reply_text("Не удалось получить курс. Попробуй позже.")

# /start_auto <interval> <duration>
async def start_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        interval = int(context.args[0])
        duration = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Используй так: /start_auto <interval_мин> <duration_мин>")
        return

    total_messages = duration // interval
    if total_messages == 0:
        await update.message.reply_text("Длительность должна быть больше интервала!")
        return

    await update.message.reply_text(f"Окей! Буду слать курс каждые {interval} мин в течение {duration} мин.")

    for i in range(total_messages):
        try:
            current_price = await get_usde_price()
            text = f"[{i+1}/{total_messages}] Курс USDe: {current_price} USD"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        except Exception as e:
            logger.error(f"Ошибка при отправке курса: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось получить курс.")

        if i < total_messages - 1:
            await asyncio.sleep(interval * 60)  # ждем следующий интервал

    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Рассылка завершена!")

# Запуск бота
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("start_auto", start_auto))

    logger.info("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
