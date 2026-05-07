from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
import database

class LoginWindow(QWidget):
    # Створюємо сигнал, який буде передавати словник з даними користувача
    login_successful = pyqtSignal(dict) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HoDis - Авторизація")
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логін (наприклад: teacher1)")
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль (наприклад: 123)")
        self.password_input.setEchoMode(QLineEdit.Password) 
        layout.addWidget(self.password_input)
        
        self.login_btn = QPushButton("Увійти")
        self.login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)

    def check_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        db = database.load_db()
        for user in db["users"]:
            if user["username"] == username and user["password"] == password:
                self.login_successful.emit(user)
                self.close()
                return
        
        QMessageBox.warning(self, "Помилка", "Невірний логін або пароль!")