from aiogram import Bot
from aiogram.types import LabeledPrice
from config import TELEGRAM_BOT_TOKEN

bot = Bot(token=TELEGRAM_BOT_TOKEN)
PRICE = LabeledPrice(label="Подписка на 1 месяц", amount=500 * 100)
