from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def menu_kb() -> ReplyKeyboardMarkup:
    items1 = ["🇷🇺 Русский", "🇺🇸 English"]
    row1 = [KeyboardButton(text=item1) for item1 in items1]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[row1],
        resize_keyboard=True
    )

    return keyboard


def sub_kb(key_lang) -> ReplyKeyboardMarkup:
    from translations.json import text
    items1 = [text.get_message(key_lang, 'button1')]
    row1 = [KeyboardButton(text=item1) for item1 in items1]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[row1],
        resize_keyboard=True
    )

    return keyboard


def get_kb(key_lang) -> ReplyKeyboardMarkup:
    from translations.json import text
    items1 = [text.get_message(key_lang, 'button2')]
    items2 = [text.get_message(key_lang, 'button3')]
    items3 = [text.get_message(key_lang, 'button4')]
    row1 = [KeyboardButton(text=item1) for item1 in items1]
    row2 = [KeyboardButton(text=item1) for item1 in items2]
    row3 = [KeyboardButton(text=item1) for item1 in items3]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[row1, row2, row3],
        resize_keyboard=True
    )

    return keyboard
