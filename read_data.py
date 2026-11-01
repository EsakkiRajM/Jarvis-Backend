from database import get_connection

connection = get_connection()

cursor = connection.cursor()

cursor.execute("SELECT * FROM users")

users = cursor.fetchall()

for user in users:

    print(user)

connection.close()