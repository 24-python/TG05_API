import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from config import TOKEN, API_NASA

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def get_random_apod():
    """Асинхронно получает случайное изображение APOD за последний год."""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=365)
    random_date = start_time + (end_time - start_time) * random.random()
    date_str = random_date.strftime("%Y-%m-%d")

    url = f"https://api.nasa.gov/planetary/apod?api_key={API_NASA}&date={date_str}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                apod = await response.json()

                return {
                    "title": apod.get("title", "Без названия"),
                    "description": apod.get("explanation", "Описание отсутствует."),
                    "url": apod.get("url"),
                    "is_video": apod.get("media_type") == "video"
                }
    except aiohttp.ClientError as e:
        print(f"Ошибка при запросе к NASA API: {e}")
        return None


async def translate_text(text, target_lang="ru"):
    """Переводит текст на русский через Google Translate (без API-ключа)."""
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={text}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                translated_data = await response.json()
                translated_text = "".join([part[0] for part in translated_data[0]])  # Извлекаем переведённый текст
                return translated_text
    except aiohttp.ClientError as e:
        print(f"Ошибка при переводе: {e}")
        return text  # Если ошибка, возвращаем оригинальный текст


@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("🚀 Привет! \nОтправь команду /random_apod, чтобы получить случайное изображение NASA!")


@dp.message(Command("random_apod"))
async def random_apod(message: Message):
    apod = await get_random_apod()

    if not apod:
        await message.answer("❌ Ошибка при получении данных от NASA. Попробуйте позже.")
        return

    title = await translate_text(apod["title"])
    description = await translate_text(apod["description"])

    # 📌 Ограничение описания до 1024 символов
    max_length = 1024 - len(title) - 10  # Вычитаем длину заголовка и запаса
    if len(description) > max_length:
        description = description[:max_length] + "..."  # Добавляем многоточие в конце

    if apod["is_video"]:
        await message.answer(f"🎥 {title}\n\n{description}\n\n📺 Видео: {apod['url']}")
    else:
        await message.answer_photo(apod["url"], caption=f"📷 {title}\n\n{description}")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
