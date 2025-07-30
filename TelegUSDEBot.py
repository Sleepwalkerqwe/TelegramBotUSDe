# в начале
import datetime

def now_time():
    return datetime.datetime.now().strftime("%H:%M:%S %d.%m.%Y")

from aiohttp import web

# функция для обработки GET /
async def handle(request):
    return web.Response(text="I'm alive!")

# функция старта сервера
async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ Web server started on port 8080")

import asyncio
import logging
from telegram.ext import Application, CommandHandler
import httpx

BOT_TOKEN = "8461719065:AAGJPOCpt6mWeb8k0rUEQIfdqtuFBAId5SY"
CHAT_ID = 870085433
THRESHOLD = 0.98

logging.basicConfig(level=logging.INFO)

last_price = None
last_price_time = None

async def get_price():
    global last_price, last_price_time
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethena-usde&vs_currencies=usd"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            if response.status_code == 429:
                logging.warning("Получен 429 Too Many Requests от CoinGecko. Делаем паузу 60 секунд...")
                await asyncio.sleep(120)
                # возвращаем None, чтобы наверху знали, что это 429
                return None
            response.raise_for_status()
            data = response.json()
            price = data["ethena-usde"]["usd"]
            # сохраняем в кэш
            last_price = price
            last_price_time = now_time()
            return price
    except httpx.RequestError as e:
        logging.error(f"ошибка запроса к CoinGecko: {e}")
        return None
    except Exception as e:
        logging.error(f"неожиданная ошибка при получении курса: {e}")
        return None

async def monitor_price(app):
    while True:
        price = await get_price()
        if price is not None:
            logging.info(f"текущий курс: {price} {now_time()}")
            if price < THRESHOLD:
                text = f"⚠️ ВНИМАНИЕ! курс упал ниже {THRESHOLD} USDe!\nтекущий курс: {price} USD {now_time()}"
                await app.bot.send_message(chat_id=CHAT_ID, text=text)
            await asyncio.sleep(120)  # пауза 60 сек, чтобы не нагружать API
        else:
            await asyncio.sleep(120)

async def send_price_periodically(n, y, app):
    end_time = asyncio.get_event_loop().time() + y * 60
    while asyncio.get_event_loop().time() < end_time:
        try:
            price = await get_price()
            if price is not None:
                text = f"текущий курс USDe: {price} USD {now_time()}"
            elif last_price is not None:
                text = f"⚠️ Не удалось получить свежий курс, показываю последний сохранённый: {last_price} USD (на {last_price_time})"
            else:
                text = "Не удалось получить курс. Попробую позже."
            await app.bot.send_message(chat_id=CHAT_ID, text=text)
        except Exception as e:
            logging.error(f"ошибка при отправке курса: {e} {now_time()}")
        await asyncio.sleep(max(n * 60, 60))  # минимум 60 секунд

async def price_loop_handler(update, context):
    try:
        n = int(context.args[0])
        y = int(context.args[1])
        if n <= 0 or y <= 0:
            raise ValueError("параметры должны быть положительными")
        asyncio.create_task(send_price_periodically(n, y, context.application))
        await update.message.reply_text(f"буду слать курс каждые {n} минут в течение {y} минут.")
    except Exception as e:
        logging.error(f"ошибка в /price_loop: {e}")
        await update.message.reply_text("ошибка. используй команду так: /price_loop n y (n и y — целые положительные числа)")

# Команда /price — сразу показать текущий курс
async def price_handler(update, context):
    price = await get_price()
    if price is not None:
        text = f"текущий курс USDe: {price} USD   {now_time()}"
    else:
        text = "Не удалось получить текущий курс. Попробуйте позже."
    await update.message.reply_text(text)

# В основном блоке добавь этот хэндлер:


async def on_startup(app):
    logging.info("Запускаем фоновую задачу мониторинга курса...")
    asyncio.create_task(monitor_price(app))

    asyncio.create_task(monitor_price(app))
    asyncio.create_task(start_webserver())


if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("price_loop", price_loop_handler))
    app.add_handler(CommandHandler("price", price_handler))
    app.post_init = on_startup

    logging.info("бот запущен и следит за курсом")
    app.run_polling()

from aiohttp import web

# Функция-обработчик запроса
async def handle(request):
    return web.Response(text="I'm alive!")

# Функция запуска веб-сервера
async def start_keep_alive():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)  # Порт 8080
    await site.start()
    logging.info("Keep-alive сервер запущен на порту 8080")

async def on_startup(app):
    asyncio.create_task(monitor_price(app))
    asyncio.create_task(start_keep_alive())
