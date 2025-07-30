import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "твой_токен_сюда"
CHAT_ID = "твой_чат_айди_сюда"
USDE_ALERT_THRESHOLD = 1.98
CHECK_INTERVAL = 30

def get_usde_price():
    # Твоя логика получения курса, например requests.get
    return 1.0  # пример

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Бот запущен. Ваш chat_id: {update.effective_chat.id}")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_usde_price()
    await update.message.reply_text(f"Текущий курс USDe: ${price}")

async def monitor_price(app):
    while True:
        price = get_usde_price()
        logger.info(f"Текущий курс USDe: {price}")
        if price < USDE_ALERT_THRESHOLD:
            text = f"⚠️ Курс упал ниже {USDE_ALERT_THRESHOLD}: сейчас {price}"
            await app.bot.send_message(chat_id=CHAT_ID, text=text)
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    # Запускаем мониторинг курса в фоновом таске
    asyncio.create_task(monitor_price(app))

    logger.info("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Если уже есть запущенный event loop (как на Render), запускаем по-другому:
        if "already running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
