import json

def calculate_score(correct, total):
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

def check_pass_status(score):
    threshold = 60 
    return score >= threshold 

def load_test_from_json(filepath):
    print(f"Завантаження тесту з файлу: {filepath}")
    return {"question": "Що таке Git?", "answer": "Система контролю версій"}

def run_application():
    print("Запуск платформи HoDis (Консольний режим)")
    test_data = load_test_from_json("test.json")
    print("Тест успішно завантажено.")

if __name__ == "__main__":
    run_application()