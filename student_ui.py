from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class StudentDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Студента ({self.user['username']})")
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Тут буде каталог курсів та проходження тестів."))
        self.setLayout(layout)