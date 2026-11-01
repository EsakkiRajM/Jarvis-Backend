import sqlite3

def get_connection():

    connection = sqlite3.connect("jarvis.db")

    print("Connected to the database successfully!")

    return connection


def create_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            age INTEGER,

            relationship TEXT

        )
    """)

    connection.commit()

    connection.close()

print("Table created successfully!")

if __name__ == "__main__":
    create_table()