import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import pyqtSignal
from database import get_user_by_credentials

class LoginWindow(QWidget):
    login_successful = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HoDis - Авторизація")
        self.resize(350, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.username_label = QLabel("Логін:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введіть логін (напр. teacher1)")

        self.password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введіть пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Увійти")
        self.login_button.clicked.connect(self.handle_login)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

        self.username_input.returnPressed.connect(self.login_button.click)
        self.password_input.returnPressed.connect(self.login_button.click)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть всі поля.")
            return

        user = get_user_by_credentials(username, password)

        if user:
            # ПЕРЕВІРКА НА БЛОКУВАННЯ (Вимога UR6)
            if user.get("is_blocked", False):
                QMessageBox.critical(self, "Доступ заборонено", "Ваш акаунт було заблоковано Адміністратором.")
                return

            self.login_successful.emit(user)
            self.close()
        else:
            QMessageBox.critical(self, "Помилка доступу", "Невірний логін або пароль.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())