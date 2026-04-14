"""
Script de deblocage admin - CryptoScanner Pro V11
Utilisation sur Railway : coller dans le terminal Railway Console
"""
import os
import sqlite3

from config import DATABASE_PATH
from db import get_connection, is_postgres
from security import hash_password

if not is_postgres():
    db_paths = [DATABASE_PATH, "cryptoscanner.db", "/app/cryptoscanner.db", "data/cryptoscanner.db"]
    db_path = next((path for path in db_paths if os.path.exists(path)), None)
    if not db_path:
        print("Base de donnees introuvable")
        print("Chemins testes:", db_paths)
        raise SystemExit(1)
    print(f"DB trouvee: {db_path}")
else:
    print("Mode PostgreSQL détecté")

conn = get_connection()

rows = conn.execute("SELECT id, username, role, created FROM users ORDER BY id").fetchall()
print(f"\nUtilisateurs ({len(rows)}):")
for row in rows:
    created = row[3][:10] if row[3] else "?"
    print(f"  [{row[0]}] {row[1]} - {row[2]} (cree: {created})")

USERNAME = os.environ.get("MAKE_ADMIN", "loyan").strip() or "loyan"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip()

conn.execute("DELETE FROM login_attempts")
print("\nTentatives de connexion effacees")

result = conn.execute("UPDATE users SET role='admin' WHERE username=?", (USERNAME,))
if result.rowcount > 0:
    print(f"{USERNAME} -> admin")
else:
    if not ADMIN_PASSWORD:
        conn.close()
        print("ADMIN_PASSWORD absent: aucun compte admin n'a ete cree.")
        raise SystemExit(1)

    password_hash = hash_password(ADMIN_PASSWORD)
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role, created) VALUES (?,?,?,datetime('now'))",
        (USERNAME, password_hash, "admin"),
    )
    print(f"Compte admin cree: {USERNAME}")

conn.execute("DELETE FROM sessions WHERE expires < datetime('now')")
conn.commit()
conn.close()

print("\nOperation terminee.")
print(f"Connecte-toi avec le compte '{USERNAME}'")
print("Panel admin : https://ton-app.railway.app/admin")
