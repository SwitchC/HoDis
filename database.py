import json
import hashlib
import os

DB_FILE = 'db.json'
UPLOAD_DIR = 'uploads'

def init_db():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        
    if not os.path.exists(DB_FILE):
        data = {
            "users": [], "courses": [], "tests": [], "results": [],
            "practical_tasks": [], "task_submissions": []
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Базу даних ініціалізовано.")

def load_db():
    if not os.path.exists(DB_FILE):
        init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            db = json.load(f)
            if "practical_tasks" not in db: db["practical_tasks"] = []
            if "task_submissions" not in db: db["task_submissions"] = []
            return db
        except json.JSONDecodeError:
            return {
                "users": [], "courses": [], "tests": [], "results": [],
                "practical_tasks": [], "task_submissions": []
            }

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
    db = load_db()
    if any(u.get('username') == username for u in db.get('users', [])): return False
    users = db.get('users', [])
    new_id = 1 if not users else max(u['id'] for u in users) + 1
    db['users'].append({
        "id": new_id, "username": username, "password": hash_password(password),
        "role": role, "is_blocked": False
    })
    save_db(db)
    return True

def update_user(user_id, new_username, new_password, new_role):
    db = load_db()
    if any(u.get('username') == new_username and u['id'] != user_id for u in db.get('users', [])): return False
    for user in db.get('users', []):
        if user['id'] == user_id:
            user['username'] = new_username
            user['role'] = new_role
            if new_password: user['password'] = hash_password(new_password)
            break
    save_db(db)
    return True

def delete_user(user_id):
    db = load_db()
    db['users'] = [u for u in db.get('users', []) if u['id'] != user_id]
    save_db(db)
    return True

def add_material_to_course(course_id: int, file_name: str, file_path: str):
    db = load_db()
    for course in db.get('courses', []):
        if course['id'] == course_id:
            if 'materials' not in course: course['materials'] = []
            course['materials'].append({"name": file_name, "path": file_path})
            break
    save_db(db)
    return True

def delete_material_from_course(course_id: int, file_path: str):
    db = load_db()
    for course in db.get('courses', []):
        if course['id'] == course_id:
            materials = course.get('materials', [])
            course['materials'] = [m for m in materials if m['path'] != file_path]
            break
    save_db(db)
    if os.path.exists(file_path):
        try: os.remove(file_path)
        except Exception: pass
    return True

def add_practical_task(course_id: int, title: str, description: str):
    db = load_db()
    tasks = db.get("practical_tasks", [])
    new_id = 1 if not tasks else max(t["id"] for t in tasks) + 1
    db.setdefault("practical_tasks", []).append({
        "id": new_id, "course_id": course_id, "title": title, "description": description
    })
    save_db(db)
    return True

def submit_task(student_id: int, task_id: int, answer_text: str):
    db = load_db()
    subs = db.setdefault("task_submissions", [])
    for s in subs:
        if s["student_id"] == student_id and s["task_id"] == task_id:
            s["answer_text"] = answer_text
            s["status"] = "На перевірці"
            save_db(db)
            return True
    new_id = 1 if not subs else max(sub["id"] for sub in subs) + 1
    subs.append({
        "id": new_id, "student_id": student_id, "task_id": task_id,
        "answer_text": answer_text, "status": "На перевірці", "score": None
    })
    save_db(db)
    return True

def grade_task(submission_id: int, score: int):
    db = load_db()
    for s in db.get("task_submissions", []):
        if s["id"] == submission_id:
            s["score"] = score
            s["status"] = "Оцінено"
            save_db(db)
            return True
    return False

def delete_test(test_id: int):
    db = load_db()
    db['tests'] = [t for t in db.get('tests', []) if t['id'] != test_id]
    db['results'] = [r for r in db.get('results', []) if r.get('test_id') != test_id]
    save_db(db)
    return True

def delete_practical_task(task_id: int):
    db = load_db()
    db['practical_tasks'] = [t for t in db.get('practical_tasks', []) if t['id'] != task_id]
    db['task_submissions'] = [s for s in db.get('task_submissions', []) if s.get('task_id') != task_id]
    save_db(db)
    return True

# --- НОВА ФУНКЦІЯ ДЛЯ ЗБЕРЕЖЕННЯ ДЕТАЛЬНИХ РЕЗУЛЬТАТІВ ТЕСТУ ---
def save_detailed_test_result(student_id: int, test_id: int, score: float, passed: bool, details: list):
    """Зберігає не лише бал, а й масив відповідей з витраченим часом (FR5)."""
    db = load_db()
    result_record = {
        "id": len(db.get("results", [])) + 1,
        "student_id": student_id,
        "test_id": test_id,
        "score": score,
        "passed": passed,
        "details": details  # Тут зберігається весь масив
    }
    db.setdefault("results", []).append(result_record)
    save_db(db)
    return True