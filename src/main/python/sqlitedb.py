import sqlite3

def create_db():
	connection = sqlite3.connect("sqlite_db.db")
	connection.close()
	print("Banco de dados criado")