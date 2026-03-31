import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

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
    print("Запуск платформи HoDis (GUI режим)")
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_application()