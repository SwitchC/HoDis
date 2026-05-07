# database.py
import json
import os

DB_FILE = "db.json"

def init_db():
    if not os.path.exists(DB_FILE):
        initial_data = {
            "users": [
                {"id": 1, "username": "teacher1", "password": "123", "role": "teacher"},
                {"id": 2, "username": "student1", "password": "123", "role": "student"}
            ],
            "courses": [],     # Тут будуть зберігатися курси та тести
            "enrollments": [], # Записи: який студент на який курс підписався
            "results": []      # Оцінки: хто, який курс, скільки балів
        }
        save_db(initial_data)

def load_db():
    if not os.path.exists(DB_FILE):
        init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)