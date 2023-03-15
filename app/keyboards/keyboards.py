from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3 as sq

db = sq.connect('tg.db')
cur = db.cursor()

main = ReplyKeyboardMarkup(resize_keyboard=True)
main.add('Каталог 🎣').add('Корзина 🗑').add('Контакты 📲')

admin_main = ReplyKeyboardMarkup(resize_keyboard=True)
admin_main.add('Каталог 🎣').add('Корзина 🗑').add('Контакты 📲').add('Админ-панель')

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.add('Добавить товар').add('Удалить товар').add('Сделать рассылку').add('Отмена')

category = ReplyKeyboardMarkup(resize_keyboard=True)
category.add('Выберите категорию')

catalog = ReplyKeyboardMarkup(resize_keyboard=True)
catalog.add('Выберите товар')

cancel = ReplyKeyboardMarkup(resize_keyboard=True)
cancel.add('Отмена')

#  ------------------------------------------------------------------
"""
Скрипт создания инлайн кнопок в каталоге с помощью перебора всех имён в БД
"""


def catalog_buttons():
    buttons = []
    cur.execute("SELECT name FROM items")
    items = cur.fetchall()
    for item in items:
        button = InlineKeyboardButton(item[0], callback_data=item[0])
        buttons.append(button)

    catalog = InlineKeyboardMarkup(row_width=2)
    return catalog.add(*buttons)


#  ------------------------------------------------------------------

add_to_cart = InlineKeyboardMarkup(row_width=2)
add_to_cart.add(InlineKeyboardButton('Добавить в корзину', callback_data='add_to_cart'))

buy = InlineKeyboardMarkup(row_width=1)
buy.add(InlineKeyboardButton('Купить!', url='https://t.me/timur_py'))