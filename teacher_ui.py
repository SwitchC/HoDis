from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class TeacherDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Викладача ({self.user['username']})")
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Тут буде функціонал створення курсів та перегляду статистики."))
        self.setLayout(layout)