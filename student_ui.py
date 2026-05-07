# student_ui.py
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QListWidget, 
                             QPushButton, QMessageBox, QListWidgetItem)
import database

class StudentDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Студента ({self.user['username']})")
        self.resize(500, 500)
        
        self.layout = QVBoxLayout()
        
        # Список доступних курсів
        self.layout.addWidget(QLabel("<b>Всі доступні курси:</b>"))
        self.available_courses_list = QListWidget()
        self.layout.addWidget(self.available_courses_list)
        
        self.enroll_btn = QPushButton("Приєднатися до обраного курсу")
        self.enroll_btn.clicked.connect(self.join_course)
        self.layout.addWidget(self.enroll_btn)
        
        self.layout.addWidget(QLabel("<hr>"))
        
        # Список курсів студента (на які він уже записаний)
        self.layout.addWidget(QLabel("<b>Мої курси (записані):</b>"))
        self.my_courses_list = QListWidget()
        self.layout.addWidget(self.my_courses_list)
        
        # Кнопка для переходу до тестування (реалізуємо в наступному завданні)
        self.start_test_btn = QPushButton("Відкрити курс та пройти тест")
        self.start_test_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.layout.addWidget(self.start_test_btn)
        
        self.setLayout(self.layout)
        self.refresh_lists()

    def refresh_lists(self):
        """Оновлює списки курсів із бази даних."""
        self.available_courses_list.clear()
        self.my_courses_list.clear()
        
        db = database.load_db()
        
        # Отримуємо ID курсів, на які цей студент уже записаний
        enrolled_ids = [e["course_id"] for e in db["enrollments"] if e["student_id"] == self.user["id"]]
        
        for course in db["courses"]:
            item_text = f"{course['id']}. {course['title']} (Питань: {len(course['questions'])})"
            item = QListWidgetItem(item_text)
            item.setData(32, course['id']) # Зберігаємо ID курсу в об'єкті елемента списку
            
            if course['id'] in enrolled_ids:
                self.my_courses_list.addItem(item)
            else:
                self.available_courses_list.addItem(item)

    def join_course(self):
        """Записує студента на обраний курс."""
        selected_item = self.available_courses_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть курс зі списку доступних!")
            return
            
        course_id = selected_item.data(32)
        db = database.load_db()
        
        # Додаємо запис про реєстрацію
        new_enrollment = {
            "student_id": self.user["id"],
            "course_id": course_id
        }
        
        db["enrollments"].append(new_enrollment)
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", "Ви успішно приєдналися до курсу!")
        self.refresh_lists()