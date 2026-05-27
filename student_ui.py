import os
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QListWidget, 
                             QPushButton, QMessageBox, QListWidgetItem,
                             QDialog, QRadioButton, QButtonGroup, QHBoxLayout)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import database
import core

# --- ВІКНО ПРОХОДЖЕННЯ ТЕСТУ ---
class TestExecutionWindow(QDialog):
    def __init__(self, student_id, test_data):
        super().__init__()
        self.student_id = student_id
        self.test = test_data
        self.questions = test_data["questions"]
        self.current_q_index = 0
        self.correct_answers = 0

        self.setWindowTitle(f"Тест: {self.test['title']}")
        self.resize(500, 350)

        self.layout = QVBoxLayout()
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.layout.addWidget(self.question_label)

        self.radio_group = QButtonGroup(self)
        self.radios = []
        for i in range(4):
            radio = QRadioButton()
            self.radios.append(radio)
            self.radio_group.addButton(radio, i)
            self.layout.addWidget(radio)

        self.next_btn = QPushButton("Наступне питання")
        self.next_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.next_btn.clicked.connect(self.check_answer)
        self.layout.addWidget(self.next_btn)

        self.setLayout(self.layout)
        self.load_question()

    def load_question(self):
        if self.current_q_index < len(self.questions):
            q_data = self.questions[self.current_q_index]
            self.question_label.setText(f"<b>Питання {self.current_q_index + 1}:</b> {q_data['question']}")

            for i, option in enumerate(q_data['options']):
                self.radios[i].setText(option)

            self.radio_group.setExclusive(False)
            for r in self.radios: 
                r.setChecked(False)
            self.radio_group.setExclusive(True)

            if self.current_q_index == len(self.questions) - 1:
                self.next_btn.setText("Завершити тест")
        else:
            self.finish_test()

    def check_answer(self):
        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Увага", "Оберіть один із варіантів відповіді!")
            return

        correct_id = self.questions[self.current_q_index]["correct_index"]
        if selected_id == correct_id:
            self.correct_answers += 1

        self.current_q_index += 1
        self.load_question()

    def finish_test(self):
        total = len(self.questions)
        score = core.calculate_score(self.correct_answers, total)
        passed = core.check_pass_status(score)

        db = database.load_db()
        result_record = {
            "student_id": self.student_id,
            "test_id": self.test["id"], 
            "score": score,
            "passed": passed
        }
        db.setdefault("results", []).append(result_record)
        database.save_db(db)

        status_text = "Складено успішно!" if passed else "Не складено. Спробуйте ще."
        QMessageBox.information(self, "Результат",
                                f"Тест завершено!\n"
                                f"Правильних відповідей: {self.correct_answers} з {total}\n"
                                f"Ваш бал: {score}%\n"
                                f"Статус: {status_text}")
        self.accept()


# --- ДАШБОРД СТУДЕНТА ---
class StudentDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Студента ({self.user['username']})")
        self.resize(750, 600)
        
        self.layout = QVBoxLayout()
        
        # 1. Каталог доступних курсів
        self.layout.addWidget(QLabel("<b>Каталог усіх курсів:</b>"))
        self.available_courses_list = QListWidget()
        self.layout.addWidget(self.available_courses_list)
        
        self.enroll_btn = QPushButton("Приєднатися до курсу")
        self.enroll_btn.clicked.connect(self.join_course)
        self.layout.addWidget(self.enroll_btn)
        
        self.layout.addWidget(QLabel("<hr>"))
        
        # 2. Мої курси та контент (горизонтальний блок)
        h_layout = QHBoxLayout()
        
        # Ліва колонка: Мої курси
        v_left = QVBoxLayout()
        v_left.addWidget(QLabel("<b>Мої курси:</b>"))
        self.my_courses_list = QListWidget()
        self.my_courses_list.itemSelectionChanged.connect(self.load_course_content) 
        v_left.addWidget(self.my_courses_list)
        h_layout.addLayout(v_left)
        
        # Права колонка: Матеріали та Тести
        v_right = QVBoxLayout()
        
        # Блок Матеріалів
        v_right.addWidget(QLabel("<b>Навчальні матеріали:</b>"))
        self.materials_list = QListWidget()
        v_right.addWidget(self.materials_list)
        
        self.open_mat_btn = QPushButton("👁️ Відкрити матеріал")
        self.open_mat_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px;")
        self.open_mat_btn.clicked.connect(self.open_material)
        v_right.addWidget(self.open_mat_btn)
        
        v_right.addWidget(QLabel("<hr><b>Доступні тести:</b>"))
        self.tests_list = QListWidget()
        v_right.addWidget(self.tests_list)
        
        self.start_test_btn = QPushButton("Пройти обраний тест")
        self.start_test_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.start_test_btn.clicked.connect(self.start_test)
        v_right.addWidget(self.start_test_btn)
        
        h_layout.addLayout(v_right)
        self.layout.addLayout(h_layout)
        
        self.setLayout(self.layout)
        self.refresh_lists()

    def refresh_lists(self):
        self.available_courses_list.clear()
        self.my_courses_list.clear()
        self.tests_list.clear()
        self.materials_list.clear()
        
        db = database.load_db()
        enrolled_ids = [e["course_id"] for e in db.get("enrollments", []) if e["student_id"] == self.user["id"]]
        
        for course in db.get("courses", []):
            item = QListWidgetItem(course['title'])
            item.setData(32, course['id'])
            
            if course['id'] in enrolled_ids:
                self.my_courses_list.addItem(item)
            else:
                self.available_courses_list.addItem(item)

    def join_course(self):
        selected_item = self.available_courses_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Помилка", "Оберіть курс із каталогу!")
            return
            
        course_id = selected_item.data(32)
        db = database.load_db()
        
        db.setdefault("enrollments", []).append({"student_id": self.user["id"], "course_id": course_id})
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", "Ви приєдналися до курсу!")
        self.refresh_lists()

    def load_course_content(self):
        """Завантажує матеріали та тести для курсу, який студент обрав."""
        self.tests_list.clear()
        self.materials_list.clear()
        
        selected_item = self.my_courses_list.currentItem()
        if not selected_item: return
            
        course_id = selected_item.data(32)
        db = database.load_db()
        
        for course in db.get("courses", []):
            if course["id"] == course_id:
                for mat in course.get("materials", []):
                    item = QListWidgetItem(mat["name"])
                    item.setData(32, mat["path"]) 
                    self.materials_list.addItem(item)
                break
                
        for test in db.get("tests", []):
            if test["course_id"] == course_id:
                item = QListWidgetItem(f"{test['title']} (Питань: {len(test['questions'])})")
                item.setData(32, test['id'])
                self.tests_list.addItem(item)

    def open_material(self):
        selected = self.materials_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Увага", "Оберіть матеріал зі списку!")
            return
        file_path = selected.data(32)
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        else:
            QMessageBox.critical(self, "Помилка", "Файл не знайдено на сервері!")

    def start_test(self):
        selected_item = self.tests_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Помилка", "Оберіть тест зі списку тестів!")
            return

        test_id = selected_item.data(32)
        db = database.load_db()
        
        test_data = None
        for test in db.get("tests", []):
            if test["id"] == test_id:
                test_data = test
                break
                
        if test_data:
            test_window = TestExecutionWindow(self.user["id"], test_data)
            test_window.exec_()