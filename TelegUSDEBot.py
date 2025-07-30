import logging
import asyncio
import requests
import os
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID', '870085433')
USDE_ALERT_THRESHOLD = 1.98
CHECK_INTERVAL = 30  # секунд

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Получение курса USDe ---
def get_usde_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethena-usde&vs_currencies=usd'
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['ethena-usde']['usd']
    except Exception as e:
        logger.error(f"Ошибка при получении курса: {e}")
        return None

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f'✅ Бот запущен и следит за курсом USDe! Ваш chat_id: {chat_id}')

# --- Команда /price ---
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_price = get_usde_price()
    if current_price:
        await update.message.reply_text(f'Текущий курс USDe: ${current_price}')
    else:
        await update.message.reply_text('Не удалось получить курс.')

# --- Фоновый мониторинг курса ---
async def monitor_price(bot: Bot):
    while True:
        price = get_usde_price()
        if price:
            logger.info(f"Текущий курс USDe: ${price}")
            if price < USDE_ALERT_THRESHOLD:
                text = f"⚠️ Внимание! Курс USDe упал ниже ${USDE_ALERT_THRESHOLD}: сейчас ${price}"
                await bot.send_message(chat_id=CHAT_ID, text=text)
        await asyncio.sleep(CHECK_INTERVAL)

# --- Keep alive сервер ---
async def handle(request):
    return web.Response(text="I'm alive!")

async def start_keep_alive():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()
    logger.info("Keep alive сервер запущен на порту 8080")

# --- Запуск бота ---
async def run():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    # Запускаем мониторинг и keep alive параллельно
    asyncio.create_task(monitor_price(app.bot))
    asyncio.create_task(start_keep_alive())

    logger.info("Бот запущен.")
    await app.run_polling()

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()
