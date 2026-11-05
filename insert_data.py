from database import get_connection

def insert_user(name, age, relationship):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("INSERT INTO users (name, age, relationship) VALUES (?, ?, ?)", 
                   (name, age, relationship))

    connection.commit()

    connection.close()

    print(f"User '{name}' inserted successfully!")

insert_user("Susila", 26, "Second Owner")
