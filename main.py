import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import random

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Вот в этом промежутке мы будем работать и писать новый код




async def main():
   await dp.start_polling(bot)

if __name__ == '__main__':
   asyncio.run(main())