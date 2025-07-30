import asyncio
import logging
from telegram.ext import Application, CommandHandler
import httpx

# Конфигурация
BOT_TOKEN = "8461719065:AAGJPOCpt6mWeb8k0rUEQIfdqtuFBAId5SY"   # сюда вставь свой реальный токен
CHAT_ID = 870085433
THRESHOLD = 0.98

logging.basicConfig(level=logging.INFO)

async def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethena-usde&vs_currencies=usd"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            if response.status_code == 429:
                logging.warning("Получен 429 Too Many Requests от CoinGecko. Делаем паузу...")
                await asyncio.sleep(10)  # пауза подольше при 429
                return None
            response.raise_for_status()
            data = response.json()

            return data["ethena-usde"]["usd"]
    except httpx.RequestError as e:
        logging.error(f"Ошибка запроса к CoinGecko: {e}")
        return None
    except Exception as e:
        logging.error(f"Неожиданная ошибка при получении курса: {e}")
        return None

# 🎯 Фоновая задача: проверка курса
async def monitor_price(app):
    while True:
        price = await get_price()
        if price is not None:
            logging.info(f"Текущий курс: {price}")
            if price < THRESHOLD:
                text = f"⚠️ ВНИМАНИЕ! Курс упал ниже {THRESHOLD} USD!\nТекущий курс: {price} USD"
                await app.bot.send_message(chat_id=CHAT_ID, text=text)
            await asyncio.sleep(5)  # хотя бы 5 секунд между запросами
        else:
            # Если цена не получена, подождать дольше
            await asyncio.sleep(10)

# 🕒 Команда: /price_loop n y
async def price_loop_handler(update, context):
    try:
        n = int(context.args[0])  # каждые n минут
        y = int(context.args[1])  # в течение y минут
        asyncio.create_task(send_price_periodically(n, y, context.application))
        await update.message.reply_text(f"Буду слать курс каждые {n} минут в течение {y} минут.")
    except Exception as e:
        logging.error(f"Ошибка в /price_loop: {e}")
        await update.message.reply_text("Ошибка. Используй команду так: /price_loop n y")

# 📦 Функция для отправки курса каждые n минут в течение y минут
async def send_price_periodically(n, y, app):
    end_time = asyncio.get_event_loop().time() + y * 60
    while asyncio.get_event_loop().time() < end_time:
        try:
            price = await get_price()
            text = f"Текущий курс USDe: {price} USD"
            await app.bot.send_message(chat_id=CHAT_ID, text=text)
        except Exception as e:
            logging.error(f"Ошибка при отправке курса: {e}")
        await asyncio.sleep(n * 60)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("price_loop", price_loop_handler))

    # Запускаем фоновую задачу мониторинга курса, когда бот стартует
    async def on_startup(app):
        asyncio.create_task(monitor_price(app))
    app.post_init = on_startup

    logging.info("Бот запущен и следит за курсом")
    # Запускаем polling **без** asyncio.run()
    app.run_polling()