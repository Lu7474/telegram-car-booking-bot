from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Регистрация")],
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="")],
        [KeyboardButton(text="")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню...",
)


def get_catalog_keyboard(car_types=None):
    keyboard = [
        [InlineKeyboardButton(text="Все автомобили", callback_data="filter_all")],
        [InlineKeyboardButton(text="Седаны", callback_data="filter_sedan")],
        [InlineKeyboardButton(text="Внедорожники", callback_data="filter_suv")],
        [InlineKeyboardButton(text="Хэтчбеки", callback_data="filter_hatchback")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Обновляем существующую клавиатуру
catalog = get_catalog_keyboard()


get_number = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
    resize_keyboard=True,
)
