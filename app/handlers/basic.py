from main import bot, dp
from aiogram import types
from app.keyboards import keyboards


@dp.message_handler(commands=['start', 'run'])
async def start_command(message: types.Message):
    await message.answer(f'Добро пожаловать, <b>{message.from_user.first_name}</b>! 🔥\n\n'
                         f'✅ Данный бот поможет Вам найти что можно посмотреть на вечерок.\n',
                         reply_markup=keyboards.main)


@dp.message_handler()
async def answers(message: types.Message):
    if message.text == 'Каталог':
        await message.answer(f'Выберите категорию.', reply_markup=keyboards.catalog)
