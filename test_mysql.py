import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="capstonewebgym"
)

print("MYSQL CONNECTED")

cursor = conn.cursor()
cursor.execute("SHOW TABLES")
print(cursor.fetchall())

conn.close()
