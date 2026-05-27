import json
import hashlib
import os

DB_FILE = 'db.json'

def init_db():
    if not os.path.exists(DB_FILE):
        data = {"users": [], "courses": [], "tests": [], "results": []}
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Базу даних ініціалізовано.")

def load_db():
    if not os.path.exists(DB_FILE):
        init_db()
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"users": [], "courses": [], "tests": [], "results": []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_user_by_credentials(username, password):
    db = load_db()
    hashed_pw = hash_password(password)
    
    for user in db.get('users', []):
        if user.get('username') == username and user.get('password') == hashed_pw:
            return user
    return None

def migrate_passwords():
    db = load_db()
    changed = False
    
    for user in db.get('users', []):
        if len(user.get('password', '')) < 64:
            user['password'] = hash_password(user['password'])
            changed = True
            
    if changed:
        save_db(db)
        print("Успіх: Всі старі паролі в db.json успішно захешовані!")
    else:
        print("Міграція не потрібна: Паролі вже захешовані.")

if __name__ == "__main__":
    migrate_passwords()