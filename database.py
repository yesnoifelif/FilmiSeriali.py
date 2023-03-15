import sqlite3 as sq

db = sq.connect('tg.db')
cur = db.cursor()


async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts(a_id TEXT PRIMARY KEY, cart_id TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS items(i_id TEXT PRIMARY KEY, name TEXT, desc TEXT, price TEXT, photo TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS brands(b_id TEXT PRIMARY KEY, name TEXT, b_desc TEXT)")
    db.commit()


async def create_profile(item_id):
    user = cur.execute("SELECT 1 FROM items WHERE i_id == '{key}'".format(key=item_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO items VALUES(?, ?, ?, ?, ?)", (item_id, '', '', '', ''))
        db.commit()


async def edit_profile(state, item_id):
    async with state.proxy() as data:
        cur.execute("UPDATE items SET name = '{}', desc = '{}', price = '{}', photo = '{}' WHERE i_id == '{}'".format(
            data['name'], data['desc'], data['price'], data['photo'], item_id))
        db.commit()