import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import TOKEN, API_NASA

bot = Bot(token=TOKEN)
dp = Dispatcher()







async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
