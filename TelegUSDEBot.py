import asyncio
import logging
from telegram.ext import Application, CommandHandler
import httpx

BOT_TOKEN = "8461719065:AAGJPOCpt6mWeb8k0rUEQIfdqtuFBAId5SY"
CHAT_ID = 870085433
THRESHOLD = 0.98

logging.basicConfig(level=logging.INFO)

async def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethena-usde&vs_currencies=usd"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            if response.status_code == 429:
                logging.warning("Получен 429 Too Many Requests от CoinGecko. Делаем паузу 60 секунд...")
                await asyncio.sleep(60)
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

async def monitor_price(app):
    while True:
        price = await get_price()
        if price is not None:
            logging.info(f"Текущий курс: {price}")
            if price < THRESHOLD:
                text = f"⚠️ ВНИМАНИЕ! Курс упал ниже {THRESHOLD} USD!\nТекущий курс: {price} USD"
                await app.bot.send_message(chat_id=CHAT_ID, text=text)
            await asyncio.sleep(60)  # пауза 60 сек, чтобы не нагружать API
        else:
            await asyncio.sleep(60)

async def send_price_periodically(n, y, app):
    end_time = asyncio.get_event_loop().time() + y * 60
    while asyncio.get_event_loop().time() < end_time:
        try:
            price = await get_price()
            if price is not None:
                text = f"Текущий курс USDe: {price} USD"
                await app.bot.send_message(chat_id=CHAT_ID, text=text)
            else:
                logging.warning("Не удалось получить курс для отправки.")
        except Exception as e:
            logging.error(f"Ошибка при отправке курса: {e}")
        await asyncio.sleep(max(n * 60, 60))  # минимум 60 секунд

async def price_loop_handler(update, context):
    try:
        n = int(context.args[0])
        y = int(context.args[1])
        if n <= 0 or y <= 0:
            raise ValueError("Параметры должны быть положительными")
        asyncio.create_task(send_price_periodically(n, y, context.application))
        await update.message.reply_text(f"Буду слать курс каждые {n} минут в течение {y} минут.")
    except Exception as e:
        logging.error(f"Ошибка в /price_loop: {e}")
        await update.message.reply_text("Ошибка. Используй команду так: /price_loop n y (n и y — целые положительные числа)")

async def on_startup(app):
    logging.info("Запускаем фоновую задачу мониторинга курса...")
    asyncio.create_task(monitor_price(app))

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("price_loop", price_loop_handler))
    app.post_init = on_startup

    logging.info("Бот запущен и следит за курсом")
    app.run_polling()
