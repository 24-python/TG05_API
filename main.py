import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import TOKEN, API_DOG

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_dog_breeds():
    url = 'https://api.thedogapi.com/v1/breeds'
    headers = {'x-api-key': API_DOG}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении списка пород: {e}")
        return []

def get_dog_breed_image(breed_id):
    url = f'https://api.thedogapi.com/v1/images/search?breed_id={breed_id}'
    headers = {'x-api-key': API_DOG}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and 'url' in data[0]:
            return data[0]['url']
    except (requests.exceptions.RequestException, IndexError, KeyError) as e:
        print(f"Ошибка при получении изображения породы: {e}")
    return None

def get_dog_breed_name(breed_name):
    breeds = get_dog_breeds()
    for breed in breeds:
        if breed['name'].lower() == breed_name.lower():
            return breed
    return None

@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer('Привет!\nЯ бот для поиска собак по породе. Напиши мне породу собаки, и я найду её.')

@dp.message()
async def send_dog_info(message: Message):
    breed_name = message.text.strip()
    breed_info = get_dog_breed_name(breed_name)

    if breed_info:
        dog_image_url = get_dog_breed_image(breed_info['id'])
        if dog_image_url:
            info = (f'🐶 Порода: {breed_info["name"]}\n'
                    f'📅 Возраст: {breed_info["life_span"]} лет\n'
                    f'📖 Описание: {breed_info.get("description", "Нет описания")}')
            await message.answer_photo(dog_image_url, caption=info)
        else:
            await message.answer('Не удалось найти изображение этой породы.')
    else:
        await message.answer('Такой породы нет в базе данных. Попробуйте ещё раз.')

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
