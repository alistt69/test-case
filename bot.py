import asyncio
import logging

import aiogram.types
import requests
from dotenv import load_dotenv

from os import environ
from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from pytonconnect.storage import IStorage
from pytonconnect import TonConnect
from pytoniq_core import Address

from utils.captcha import generate_captcha
from database.storage import db
from translations.json import text
from utils.keyboards import menu_kb, sub_kb, get_kb


load_dotenv()

tc_storage = {}
captcha_storage = {}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=environ.get("BOT_TOKEN"))
dp = Dispatcher(bot=bot)


class TcStorage(IStorage):

    def __init__(self, chat_id: int):
        self.chat_id = chat_id

    def _get_key(self, key: str):
        return str(self.chat_id) + key

    async def set_item(self, key: str, value: str):
        tc_storage[self._get_key(key)] = value

    async def get_item(self, key: str, default_value: str = None):
        return tc_storage.get(self._get_key(key), default_value)

    async def remove_item(self, key: str):
        tc_storage.pop(self._get_key(key))


def get_connector(chat_id: int):
    return TonConnect(environ['MANIFEST_URL'], storage=TcStorage(chat_id))


async def get_wallet_balance(address: str) -> float:
    non_bounceable_address = Address(address).to_str(is_bounceable=False)

    # Request to TONCENTER API
    response = requests.get(f'https://toncenter.com/api/v2/getAddressBalance?address={non_bounceable_address}')
    data = response.json()
    balance = int(data['result']) / 1e9

    return balance


class CapState(StatesGroup):
    waiting_for_captcha = State()


class LangState(StatesGroup):
    waiting_for_language = State()


class SubChannel(StatesGroup):
    waiting_for_sub = State()


class ConnectWallet(StatesGroup):
    waiting_for_connect = State()


# Start-up
async def on_startup():
    await db.db_start()


@dp.message(CommandStart(deep_link=True))
async def start(message: Message, command: CommandObject, state: FSMContext):
    user_id = message.from_user.id
    await db.get_or_create_user(user_id, command.args)
    captcha = generate_captcha()
    captcha_storage[f'{user_id}:captcha'] = captcha
    await message.answer(captcha)
    await state.set_state(CapState.waiting_for_captcha)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.get_or_create_user(message.from_user.id)
    captcha = generate_captcha()
    captcha_storage[f'{user_id}:captcha'] = captcha
    await message.answer(captcha)
    await state.set_state(CapState.waiting_for_captcha)


@dp.message(StateFilter(CapState.waiting_for_captcha))
async def cap(message: Message, state: FSMContext):
    captcha_result = eval(captcha_storage[f'{message.from_user.id}:captcha'])

    if message.text == str(captcha_result):

        await message.answer('Choose your language\n\nВыберите язык', reply_markup=menu_kb())
        captcha_storage.pop(f'{message.from_user.id}:captcha', None)
        await state.clear()
        await state.set_state(LangState.waiting_for_language)

    else:
        await message.answer('try again')


@dp.message(StateFilter(LangState.waiting_for_language))
async def language(message: Message, state: FSMContext):
    if message.text == "🇷🇺 Русский":
        lang = 'ru'

    else:
        lang = 'en'

    chat: aiogram.types.Chat = await bot.get_chat(environ['TEST_CHANNEL'])

    await db.update_language(message.from_user.id, lang)
    key_lang, = await db.get_data('locale', message.from_user.id)
    await message.answer(text.get_message(key_lang, 'welcome_text').format(user=message.from_user.full_name, channel=chat.username),
                         reply_markup=sub_kb(key_lang))
    await state.clear()
    await state.set_state(SubChannel.waiting_for_sub)


@dp.message(StateFilter(SubChannel.waiting_for_sub))
async def subcheck(message: Message, state: FSMContext):
    user_id = message.from_user.id
    res = await check_sub(user_id, environ['TEST_CHANNEL'])
    key_lang, = await db.get_data('locale', user_id)

    if res == 0:
        await message.answer(text.get_message(key_lang, 'sub_no'))

    else:
        await db.update_grum_balance(user_id)
        await menu(message)
        await state.clear()
        await wallet_callback(message)


@dp.message()
async def wallet_callback(message: Message):
    key_lang, = await db.get_data('locale', message.from_user.id)

    try:
        chat_id = message.chat.id
        connector = get_connector(chat_id)
        connected = await connector.restore_connection()

        if connected:
            wallet_address = connector.account.address
            await message.answer(
                f"{text.get_message(key_lang, 'connect_text')}\n\n"
                f"{text.get_message(key_lang, 'connect_text_extra').format(wallet=wallet_address)}"
            )

        else:
            wallet = TonConnect.get_wallets()[0]
            generated_url = await connector.connect(wallet)

            mk_b = InlineKeyboardBuilder()
            mk_b.button(text=text.get_message(key_lang, 'connect_wallet_button'), url=generated_url)
            mk_b.adjust(1, )

            await message.answer(
                text.get_message(key_lang, 'connect_text'),
                reply_markup=mk_b.as_markup()
            )

            # Polling for connection status
            for i in range(180):
                await asyncio.sleep(1)
                connected = await connector.restore_connection()
                if connected:
                    wallet_address = connector.account.address
                    await message.answer(text.get_message(key_lang, 'connect_success').format(wallet=wallet_address))
                    await menu(message)
                    return

            await message.answer(text.get_message(key_lang, 'connect_timeout'))

    except Exception as e:
        await message.answer('TON API is unavailable')


async def check_sub(user_id, chat_id):
    member = await bot.get_chat_member(chat_id, user_id)
    if member.status in ['member', 'administrator', 'creator']:
        status = 1
    else:
        status = 0

    return status


async def menu(message: Message):
    id = message.from_user.id
    key_lang, = await db.get_data('locale', id)
    chat_id = message.chat.id
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()
    ton_address, balance = '', ''

    if connected:
        ton_address = connector.wallet.account.address
        balance = await get_wallet_balance(ton_address)

    ref, = await db.get_data('ref_amount', id)
    grum_balance, = await db.get_data('grum_balance', id)

    await message.answer(text.get_message(key_lang, 'sub_yes').format(
        balance=grum_balance
    ), reply_markup=sub_kb(key_lang))

    await message.answer(text.get_message(key_lang, 'more_grum'), reply_markup=get_kb(key_lang))

    await message.answer(text.get_message(key_lang, 'info').format(
        user_id=id, ref=ref,
        wallet_address=ton_address,
        ton_balance=balance)
    )


async def main():
    dp.startup.register(on_startup)
    await db.db_start()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
