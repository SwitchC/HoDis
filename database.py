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
            "courses": [],     # Формат: {"id": 1, "teacher_id": 1, "title": "Назва курсу"}
            "tests": [],       # Формат: {"id": 1, "course_id": 1, "title": "Назва тесту", "questions": [...]}
            "enrollments": [], # Формат: {"student_id": 2, "course_id": 1}
            "results": []      # Формат: {"student_id": 2, "test_id": 1, "score": 80, "passed": True}
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