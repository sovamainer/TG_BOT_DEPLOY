import sqlite3
from pathlib import Path

DB_PATH = Path('DB/sampe1.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def create_tables():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Password TEXT NOT NULL,
        Balance INTEGER DEFAULT 0,
        Session_link TEXT,
        Telegram_ID INTEGER UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Items (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Count INTEGER NOT NULL,
        Cost INTEGER NOT NULL,
        Size TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE Basket (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER DEFAULT 1,
        Size TEXT,
        FOREIGN KEY (user_id) REFERENCES Users (Telegram_ID),
        FOREIGN KEY (item_id) REFERENCES Items (ID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE Orders (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER,
        order_id INTEGER,
        Size TEXT,
        FOREIGN KEY (user_id) REFERENCES Users (Telegram_ID),
        FOREIGN KEY (item_id) REFERENCES Items (ID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders_status (
        order_id INTEGER,
        order_status TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS verify_codes (
        order_id INTEGER,
        code TEXT,
        code_usage INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_data_to_send (
        user_id INTEGER,
        region TEXT,
        city TEXT,
        street TEXT,
        home TEXT,
        apartment TEXT,
        fullName TEXT,
        phone TEXT,
        city_index TEXT,
        tg TEXT,
        delivery_adress TEXT
    )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_name_size ON Items(Name, Size)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_basket_user_item_size ON Basket(user_id, item_id, Size)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_order ON Orders(user_id, order_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verify_codes_order_id ON verify_codes(order_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status_order_id ON orders_status(order_id)')

    try:
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uniq_basket_user_item_size ON Basket(user_id, item_id, Size)')
    except sqlite3.OperationalError:
        pass

    conn.commit()


create_tables()
conn.close()
