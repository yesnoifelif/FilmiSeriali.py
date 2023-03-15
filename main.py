from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from app.keyboards import keyboards as kb
from database import db_start, create_profile, edit_profile
from aiogram.utils.exceptions import BotBlocked
import dotenv
import os
import sqlite3 as sq

db = sq.connect('tg.db')
cur = db.cursor()

dotenv.load_dotenv()
storage = MemoryStorage()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)


async def on_startup(_):
    print('Бот запущен!!!')
    await db_start()


class AddItems(StatesGroup):
    number = State()
    name = State()
    desc = State()
    photo = State()
    price = State()


class DeleteItems(StatesGroup):
    number = State()


class AddToCart(StatesGroup):
    looking = State()
    adding = State()


class SendToAll(StatesGroup):
    creating = State()
    sending = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(f'Добро пожаловать, {message.from_user.first_name}!', reply_markup=kb.main)
    user = cur.execute("SELECT a_id FROM accounts WHERE a_id == '{key}'".format(key=message.from_user.id)).fetchone()
    if not user:
        cur.execute("INSERT INTO accounts VALUES(?, ?)", (message.from_user.id, ''))
        db.commit()
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы авторизовались как администратор!', reply_markup=kb.admin_main)


@dp.message_handler(text='Отмена', state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(f'Отменено.', reply_markup=kb.main)
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы авторизовались как администратор!', reply_markup=kb.admin_main)


@dp.message_handler(text='Контакты 📲')
async def contacts(message: types.Message):
    await message.answer(f'По всем интересующим вопросам, обращаться по номеру:📲 +998(99)893-65-74')


@dp.message_handler(text='Добавить товар')
async def add_item(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['category'] = message.text
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Выберите категорию', reply_markup=kb.category)
    await AddItems.next()


@dp.message_handler(text='Добавить товар')
async def add_item(message: types.Message) -> None:
    await AddItems.number.set()
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Напишите НОМЕР (ЛОТ) товара (цифры)', reply_markup=kb.cancel)
    else:
        await message.answer(f'Неизвестная команда!')


@dp.message_handler(state=AddItems.number)
async def add_item_id(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['iid'] = message.text
    await message.reply('Теперь отправьте название товара (только текст!)')
    await AddItems.next()


@dp.message_handler(state=AddItems.name)
async def add_item_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply('Теперь отправьте описание товара (только текст!)')
    await AddItems.next()


@dp.message_handler(state=AddItems.desc)
async def add_item_desc(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['desc'] = message.text

    await message.reply('Теперь отправьте фотографию товара (ИМЕННО ФОТО)')
    await AddItems.next()


@dp.message_handler(lambda message: not message.photo, state=AddItems.photo)
async def add_item_check_photo(message: types.Message) -> None:
    await message.reply('Это не фотография!')


@dp.message_handler(content_types=['photo'], state=AddItems.photo)
async def add_item_load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id

    await message.reply('Теперь отправьте цену (только числа! без пробелов!)')
    await AddItems.next()


@dp.message_handler(state=AddItems.price)
async def add_item_price(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:

        data['price'] = message.text
        await bot.send_photo(chat_id=message.from_user.id,
                             photo=data['photo'],
                             caption=f"{data['name']}, {data['desc']}\n{data['price']}")
    await create_profile(item_id=data['iid'])
    await edit_profile(state, item_id=data['iid'])
    db.commit()
    await message.reply('Товар успешно создан!', reply_markup=kb.admin_main)
    await state.finish()


@dp.message_handler(text='Каталог 👟')
async def catalog(message: types.Message) -> None:
    await message.answer(f'Выберите кроссы', reply_markup=kb.catalog_buttons())


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'add_to_cart')
async def add_to_cart(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        cur.execute("UPDATE accounts SET cart_id = {tovar} WHERE a_id == {user}".format(tovar=data['tovar'],
                                                                                        user=message.from_user.id))
        db.commit()
        await message.answer(f'Товар добавлен в корзину!')
        await state.finish()


@dp.callback_query_handler(lambda c: True)
async def process_callback_button(callback_query: types.CallbackQuery, state: FSMContext):
    cur.execute("SELECT * FROM items WHERE name == '{key}'".format(key=callback_query.data))
    item = cur.fetchall()
    await bot.send_photo(callback_query.from_user.id, photo=item[0][4],
                         caption=f"Вы выбрали {item[0][1]}!\n"
                                 f"Цена: {item[0][3]}", reply_markup=kb.add_to_cart)
    async with state.proxy() as data:
        data['tovar'] = item[0][0]


@dp.message_handler(text='Корзина 🗑')
async def catalog(message: types.Message) -> None:
    cur.execute("SELECT cart_id FROM accounts WHERE a_id == {key}".format(key=message.from_user.id))
    item = cur.fetchall()
    if item[0][0] == '':
        await message.answer(f'Корзина пуста!')
    else:
        cur.execute("SELECT * FROM items WHERE i_id == {key}".format(key=item[0][0]))
        tovar = cur.fetchall()
        print(tovar)
        await message.answer(f'Вы выбрали: {tovar[0][1]}\n'
                             f'Цена: {tovar[0][3]}\n', reply_markup=kb.buy)


@dp.message_handler(text='Сделать рассылку')
async def send_for_all(message: types.Message) -> None:
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await SendToAll.creating.set()
        await message.answer('Введите сообщение', reply_markup=kb.cancel)
    else:
        await message.answer('Неизвестная команда!')


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked_handler(update: types.Update, exception: BotBlocked) -> bool:
    print('Юзер заблокировал бот')
    return True


@dp.message_handler(state=SendToAll.creating)
async def sent_for_all(message: types.Message, state: FSMContext):
    await SendToAll.sending.set()
    cur.execute("SELECT a_id FROM accounts")
    accs = cur.fetchall()
    for i in accs:
        try:
            await bot.send_message(i[0], message.text)
        except Exception as error:
            cur.execute("DELETE FROM accounts WHERE a_id == {key}".format(key=i[0]))
            db.commit()
    await state.finish()
    await message.answer('Рассылка завершена', reply_markup=kb.admin_main)


@dp.message_handler(text='Админ-панель')
async def admin_panel(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы вошли в админ-панель.', reply_markup=kb.admin_panel)
    else:
        await message.answer(f'Неизвестная команда!')


@dp.message_handler(text='Удалить товар')
async def delete_item(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await DeleteItems.number.set()
        await message.answer(f'Введите номер (лот) товара.', reply_markup=kb.cancel)
    else:
        await message.answer(f'Неизвестная команда!')


@dp.message_handler(state=DeleteItems.number)
async def delete_item_done(message: types.Message, state: FSMContext):
    cur.execute("DELETE FROM items WHERE i_id == {key}".format(key=message.text))
    db.commit()
    await message.answer(f'Удалено!', reply_markup=kb.admin_panel)
    await state.finish()


@dp.message_handler()
async def none(message: types.Message):
    await message.answer(f'Неизвестная команда!')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)