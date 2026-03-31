import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
import json

def calculate_score(correct, total):
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

def check_pass_status(score):
    threshold = 60 
    return score >= threshold 

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HoDis - Проходження тесту")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Тут буде візуалізація тесту..."))
        self.setLayout(layout)

def run_application():
    print("Запуск платформи HoDis (Гібридний режим)")
    test_data = load_test_from_json("test.json")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
    
def load_test_from_json(filepath):
    print(f"Завантаження тесту з файлу: {filepath}")
    return {"question": "Що таке Git?", "answer": "Система контролю версій"}

if __name__ == "__main__":
    run_application()