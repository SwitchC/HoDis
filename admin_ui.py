from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QMessageBox, QHeaderView,
                             QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox)
import database

class UserDialog(QDialog):
    """Діалогове вікно для створення або редагування користувача."""
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.is_edit_mode = user_data is not None
        self.setWindowTitle("Редагувати користувача" if self.is_edit_mode else "Новий користувач")
        self.resize(300, 150)
        
        self.layout = QFormLayout(self)
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Залиште порожнім, щоб не змінювати" if self.is_edit_mode else "Введіть пароль")
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["student", "teacher", "admin"])
        
        self.layout.addRow("Логін:", self.username_input)
        self.layout.addRow("Пароль:", self.password_input)
        self.layout.addRow("Роль:", self.role_combo)
        
        # Блокуємо зміну ролі, якщо це режим редагування існуючого користувача
        if self.is_edit_mode:
            self.role_combo.setEnabled(False)
            self.role_combo.setToolTip("Зміна ролі існуючого користувача заборонена для збереження цілісності даних.")
        
        # Кнопки ОК та Скасувати
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
        # Якщо режим редагування, заповнюємо поля
        if self.is_edit_mode:
            self.username_input.setText(user_data['username'])
            index = self.role_combo.findText(user_data['role'])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)

    def get_data(self):
        """Повертає введені дані."""
        return {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text().strip(),
            "role": self.role_combo.currentText()
        }


class AdminDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Адміністратора ({self.user['username']})")
        self.resize(700, 450)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Управління користувачами платформи:</b>"))

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Логін", "Роль", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Панель з кнопками управління (CRUD)
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Додати")
        self.add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.add_btn.clicked.connect(self.add_user)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Редагувати")
        self.edit_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.edit_btn.clicked.connect(self.edit_user)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Видалити")
        self.delete_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        self.delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(self.delete_btn)
        
        self.toggle_btn = QPushButton("🔒 Блокувати / Розблокувати")
        self.toggle_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.toggle_btn.clicked.connect(self.toggle_status)
        btn_layout.addWidget(self.toggle_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_users(self):
        db = database.load_db()
        users = db.get("users", [])
        self.table.setRowCount(len(users))

        for row, u in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["role"]))
            
            is_blocked = u.get("is_blocked", False)
            status_text = "❌ Заблокований" if is_blocked else "✅ Активний"
            self.table.setItem(row, 3, QTableWidgetItem(status_text))

    def get_selected_user_id_and_role(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Спершу оберіть користувача в таблиці!")
            return None, None
        user_id = int(self.table.item(current_row, 0).text())
        role = self.table.item(current_row, 2).text()
        return user_id, role

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['username'] or not data['password']:
                QMessageBox.warning(self, "Помилка", "Логін та пароль не можуть бути порожніми!")
                return
                
            success = database.create_user(data['username'], data['password'], data['role'])
            if success:
                QMessageBox.information(self, "Успіх", "Нового користувача створено!")
                self.load_users()
            else:
                QMessageBox.warning(self, "Помилка", "Користувач із таким логіном вже існує!")

    def edit_user(self):
        user_id, current_role = self.get_selected_user_id_and_role()
        if not user_id: return
        
        current_username = self.table.item(self.table.currentRow(), 1).text()
        user_data = {"username": current_username, "role": current_role}
        
        dialog = UserDialog(self, user_data=user_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['username']:
                QMessageBox.warning(self, "Помилка", "Логін не може бути порожнім!")
                return
                
            success = database.update_user(user_id, data['username'], data['password'], data['role'])
            if success:
                QMessageBox.information(self, "Успіх", "Дані користувача оновлено!")
                self.load_users()
            else:
                QMessageBox.warning(self, "Помилка", "Логін вже зайнятий іншим користувачем!")

    def delete_user(self):
        user_id, role = self.get_selected_user_id_and_role()
        if not user_id: return
        
        if user_id == self.user['id']:
            QMessageBox.warning(self, "Помилка", "Ви не можете видалити свій власний акаунт!")
            return
            
        confirm = QMessageBox.question(self, "Підтвердження", 
                                     "Ви впевнені, що хочете видалити цього користувача?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            database.delete_user(user_id)
            QMessageBox.information(self, "Успіх", "Користувача видалено з системи.")
            self.load_users()

    def toggle_status(self):
        user_id, role = self.get_selected_user_id_and_role()
        if not user_id: return
        
        if user_id == self.user['id']:
            QMessageBox.warning(self, "Помилка", "Ви не можете заблокувати самі себе!")
            return
            
        is_blocked = database.toggle_user_block(user_id)
        status_msg = "заблоковано" if is_blocked else "розблоковано"
        QMessageBox.information(self, "Успіх", f"Користувача {status_msg}!")
        self.load_users()