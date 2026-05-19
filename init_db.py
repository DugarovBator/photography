import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = 'portfolio.db'

def init_db():
    # Подключение к базе данных (файл создастся автоматически, если его нет)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Удаление существующих таблиц для чистого старта (полезно при разработке)
    cursor.executescript('''
        DROP TABLE IF EXISTS photos;
        DROP TABLE IF EXISTS lenses;
        DROP TABLE IF EXISTS users;
    ''')

    # Создание таблиц
    cursor.executescript('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE lenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            description TEXT,
            lens_id INTEGER NOT NULL,
            FOREIGN KEY (lens_id) REFERENCES lenses (id)
        );
    ''')

    # Создание пользователя администратора по умолчанию
    # Имя пользователя: admin, Пароль: password
    admin_password = generate_password_hash("password")
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ("admin", admin_password))

    # Добавление объективов по умолчанию
    lenses = [
        ("Canon EOS 550D Kit",),
        ("Helios 44-2",),
        ("Jupiter 37A",)
    ]
    cursor.executemany('INSERT INTO lenses (name) VALUES (?)', lenses)

    conn.commit()
    conn.close()

    print("База данных успешно инициализирована.")
    print("Данные администратора -> Логин: admin | Пароль: password")

if __name__ == '__main__':
    init_db()
