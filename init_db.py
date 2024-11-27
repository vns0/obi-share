import sqlite3

DATABASE = "notes.db"
SCHEMA_FILE = "schema.sql"

def initialize_database():
    # Подключаемся к базе данных
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Читаем SQL-запросы из файла
    with open(SCHEMA_FILE, "r") as schema_file:
        schema = schema_file.read()

    # Выполняем SQL-запросы
    cursor.executescript(schema)
    conn.commit()

    print("Database initialized successfully!")
    conn.close()

if __name__ == "__main__":
    initialize_database()
