import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from config import TOKEN, API_NASA

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)  # Создание экземпляра бота с токеном из config.py
dp = Dispatcher()  # Создание диспетчера для обработки сообщений


async def get_random_apod():
    """Асинхронно получает случайное изображение APOD (Astronomy Picture of the Day) за последний год."""
    end_time = datetime.now()  # Текущая дата и время
    start_time = end_time - timedelta(days=365)  # Дата год назад
    # Генерация случайной даты между start_time и end_time
    random_date = start_time + (end_time - start_time) * random.random()
    date_str = random_date.strftime("%Y-%m-%d")  # Форматирование даты для API

    # Формирование URL для запроса к NASA API
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_NASA}&date={date_str}"

    try:
        async with aiohttp.ClientSession() as session:  # Создание асинхронной сессии
            async with session.get(url) as response:  # GET-запрос к API
                response.raise_for_status()  # Проверка на ошибки HTTP
                apod = await response.json()  # Парсинг JSON-ответа

                # Возвращаем словарь с данными изображения
                return {
                    "title": apod.get("title", "Без названия"),  # Заголовок с дефолтным значением
                    "description": apod.get("explanation", "Описание отсутствует."),  # Описание
                    "url": apod.get("url"),  # URL изображения/видео
                    "is_video": apod.get("media_type") == "video"  # Проверка типа медиа
                }
    except aiohttp.ClientError as e:
        print(f"Ошибка при запросе к NASA API: {e}")
        return None  # В случае ошибки возвращаем None


async def translate_text(text, target_lang="ru"):
    """Переводит текст на русский через Google Translate (без API-ключа)."""
    # Формирование URL для неофициального API Google Translate
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={text}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                translated_data = await response.json()
                # Извлечение переведённого текста из сложной структуры ответа
                translated_text = "".join([part[0] for part in translated_data[0]])
                return translated_text
    except aiohttp.ClientError as e:
        print(f"Ошибка при переводе: {e}")
        return text  # Возвращаем исходный текст в случае ошибки


# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("🚀 Привет! \nОтправь команду /random_apod, чтобы получить случайное изображение NASA!")


# Обработчик команды /random_apod
@dp.message(Command("random_apod"))
async def random_apod(message: Message):
    # Получаем случайное изображение от NASA
    apod = await get_random_apod()

    if not apod:  # Если произошла ошибка
        await message.answer("❌ Ошибка при получении данных от NASA. Попробуйте позже.")
        return

    # Переводим заголовок и описание
    title = await translate_text(apod["title"])
    description = await translate_text(apod["description"])

    # Ограничение описания до 1024 символов (ограничение Telegram для подписей)
    max_length = 1024 - len(title) - 10  # Оставляем запас
    if len(description) > max_length:
        description = description[:max_length] + "..."  # Обрезаем и добавляем многоточие

    # Отправляем результат пользователю
    if apod["is_video"]:
        # Если это видео, отправляем как текст с URL
        await message.answer(f"🎥 {title}\n\n{description}\n\n📺 Видео: {apod['url']}")
    else:
        # Если изображение, отправляем как фото с подписью
        await message.answer_photo(apod["url"], caption=f"📷 {title}\n\n{description}")


async def main():
    """Основная функция для запуска бота."""
    await dp.start_polling(bot)  # Запуск бота в режиме polling


if __name__ == '__main__':
    asyncio.run(main())  # Запуск асинхронной main функции