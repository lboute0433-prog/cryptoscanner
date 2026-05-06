import sqlite3

conn = sqlite3.connect('cryptoscanner.db')
cursor = conn.cursor()

# Voir les colonnes de la table users
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("Colonnes de la table users:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
