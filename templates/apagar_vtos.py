import sqlite3

DB = "urna.db"

conn = sqlite3.connect(DB)
conn.execute("DELETE FROM votos;")
conn.commit()
conn.close()

print("Todos os votos foram apagados!")
input("Pressione ENTER para sair...")