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

def toggle_user_block(user_id: int) -> bool:
    db = load_db()
    new_status = False
    for user in db.get('users', []):
        if user['id'] == user_id:
            current_status = user.get('is_blocked', False)
            user['is_blocked'] = not current_status
            new_status = user['is_blocked']
            break
    save_db(db)
    return new_status

def create_user(username, password, role):
    """Створює нового користувача. Повертає True, якщо успішно, False - якщо логін зайнятий."""
    db = load_db()
    if any(u.get('username') == username for u in db.get('users', [])):
        return False
    
    users = db.get('users', [])
    new_id = 1 if not users else max(u['id'] for u in users) + 1
    
    db['users'].append({
        "id": new_id,
        "username": username,
        "password": hash_password(password),
        "role": role,
        "is_blocked": False
    })
    save_db(db)
    return True

def update_user(user_id, new_username, new_password, new_role):
    """Оновлює дані користувача. Якщо new_password порожній, пароль не змінюється."""
    db = load_db()
    
    # Перевірка, чи не зайнятий новий логін іншим користувачем
    if any(u.get('username') == new_username and u['id'] != user_id for u in db.get('users', [])):
        return False
        
    for user in db.get('users', []):
        if user['id'] == user_id:
            user['username'] = new_username
            user['role'] = new_role
            if new_password:  # Оновлюємо пароль тільки якщо введено новий
                user['password'] = hash_password(new_password)
            break
            
    save_db(db)
    return True

def delete_user(user_id):
    """Видаляє користувача з бази."""
    db = load_db()
    db['users'] = [u for u in db.get('users', []) if u['id'] != user_id]
    save_db(db)
    return True

def create_default_admin():
    db = load_db()
    if not any(u.get('role') == 'admin' for u in db.get('users', [])):
        users = db.get('users', [])
        admin_id = 1 if not users else max(u['id'] for u in users) + 1
        db['users'].append({
            "id": admin_id,
            "username": "admin1",
            "password": hash_password("123"),
            "role": "admin",
            "is_blocked": False
        })
        save_db(db)
        print("Успіх: Створено адміністратора (Логін: admin1, Пароль: 123)")

if __name__ == "__main__":
    create_default_admin()