import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройки
BOT_TOKEN = "7572613508:AAErKCDjTYY2E_tLz0U04aA9A8V1PCsH-0w"
DECK_API_URL = "https://deckofcardsapi.com/api/deck"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранение состояния игры
games = {}


async def create_deck() -> str:
    """Создает новую колоду карт"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DECK_API_URL}/new/shuffle/?deck_count=1") as resp:
            data = await resp.json()
            return data["deck_id"]


async def draw_cards(deck_id: str, count: int) -> list:
    """Тянет карты из колоды"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DECK_API_URL}/{deck_id}/draw/?count={count}") as resp:
            data = await resp.json()
            return data["cards"]


def calculate_score(cards: list) -> int:
    """Подсчитывает очки в руке"""
    values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
        "9": 9, "10": 10, "JACK": 10, "QUEEN": 10, "KING": 10, "ACE": 11
    }
    score = sum(values[card["value"]] for card in cards)
    aces = sum(1 for card in cards if card["value"] == "ACE")

    while score > 21 and aces:
        score -= 10
        aces -= 1

    return score


def format_cards(cards: list) -> str:
    """Форматирует карты для вывода"""
    emoji = {
        "HEARTS": "♥️", "DIAMONDS": "♦️",
        "CLUBS": "♣️", "SPADES": "♠️"
    }
    return " ".join(
        f"{emoji[card['suit']]}{card['value']}"
        for card in cards
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🃏 Добро пожаловать в Blackjack!\n\n"
        "Правила:\n"
        "• Цель - набрать 21 очко или ближе к нему, чем дилер\n"
        "• Туз = 1 или 11 очков\n"
        "• Картинки = 10 очков\n\n"
        "Нажми /play чтобы начать игру!"
    )


@dp.message(Command("play"))
async def play(message: types.Message):
    deck_id = await create_deck()
    player_cards = await draw_cards(deck_id, 2)
    dealer_cards = await draw_cards(deck_id, 2)

    games[message.from_user.id] = {
        "deck_id": deck_id,
        "player": player_cards,
        "dealer": dealer_cards,
        "status": "player_turn"
    }

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Взять карту", callback_data="hit")
    builder.button(text="✋ Остановиться", callback_data="stand")

    await message.answer(
        f"💼 Дилер: {dealer_cards[0]['value']} и ❓\n"
        f"👤 Ваши карты: {format_cards(player_cards)} "
        f"(Очков: {calculate_score(player_cards)})\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "hit")
async def hit(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games:
        await callback.answer("Игра не найдена. Начните новую /play")
        return

    game = games[user_id]
    new_card = (await draw_cards(game["deck_id"], 1))[0]
    game["player"].append(new_card)
    score = calculate_score(game["player"])

    if score > 21:
        game["status"] = "game_over"
        await callback.message.edit_text(
            f"💥 Перебор! {format_cards(game['player'])} = {score}\n"
            f"💼 Дилер: {format_cards(game['dealer'])} = {calculate_score(game['dealer'])}\n\n"
            "Вы проиграли! Нажми /play чтобы сыграть снова",
            reply_markup=None
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Взять карту", callback_data="hit")
        builder.button(text="✋ Остановиться", callback_data="stand")

        await callback.message.edit_text(
            f"💼 Дилер: {game['dealer'][0]['value']} и ❓\n"
            f"👤 Ваши карты: {format_cards(game['player'])} "
            f"(Очков: {score})\n\n"
            "Выберите действие:",
            reply_markup=builder.as_markup()
        )

    await callback.answer()


@dp.callback_query(F.data == "stand")
async def stand(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games:
        await callback.answer("Игра не найдена. Начните новую /play")
        return

    game = games[user_id]
    game["status"] = "game_over"
    player_score = calculate_score(game["player"])
    dealer_score = calculate_score(game["dealer"])

    # Дилер добирает карты по правилам
    while dealer_score < 17:
        new_card = (await draw_cards(game["deck_id"], 1))[0]
        game["dealer"].append(new_card)
        dealer_score = calculate_score(game["dealer"])

    # Определяем победителя
    if dealer_score > 21 or player_score > dealer_score:
        result = "Вы выиграли! 🎉"
    elif player_score == dealer_score:
        result = "Ничья! 🤝"
    else:
        result = "Вы проиграли! 😢"

    await callback.message.edit_text(
        f"👤 Ваши карты: {format_cards(game['player'])} = {player_score}\n"
        f"💼 Дилер: {format_cards(game['dealer'])} = {dealer_score}\n\n"
        f"{result}\n\n"
        "Нажми /play чтобы сыграть снова",
        reply_markup=None
    )

    del games[user_id]
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())