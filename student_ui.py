from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QListWidget, 
                             QPushButton, QMessageBox, QListWidgetItem,
                             QDialog, QRadioButton, QButtonGroup)
import database
import core

# --- ВІКНО ПРОХОДЖЕННЯ ТЕСТУ ---
class TestExecutionWindow(QDialog):
    def __init__(self, student_id, course_data):
        super().__init__()
        self.student_id = student_id
        self.course = course_data
        self.questions = course_data["questions"]
        self.current_q_index = 0
        self.correct_answers = 0

        self.setWindowTitle(f"Тест: {self.course['title']}")
        self.resize(400, 300)

        self.layout = QVBoxLayout()
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.layout.addWidget(self.question_label)

        # Група радіокнопок для 4 варіантів відповідей
        self.radio_group = QButtonGroup(self)
        self.radios = []
        for i in range(4):
            radio = QRadioButton()
            self.radios.append(radio)
            self.radio_group.addButton(radio, i)
            self.layout.addWidget(radio)

        self.next_btn = QPushButton("Наступне питання")
        self.next_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        self.next_btn.clicked.connect(self.check_answer)
        self.layout.addWidget(self.next_btn)

        self.setLayout(self.layout)
        self.load_question()

    def load_question(self):
        if self.current_q_index < len(self.questions):
            q_data = self.questions[self.current_q_index]
            self.question_label.setText(f"<b>Питання {self.current_q_index + 1}:</b> {q_data['question']}")

            # Заповнюємо варіанти відповідей
            for i, option in enumerate(q_data['options']):
                self.radios[i].setText(option)

            # Скидаємо вибір перед новим питанням
            self.radio_group.setExclusive(False)
            for r in self.radios: 
                r.setChecked(False)
            self.radio_group.setExclusive(True)

            # Якщо це останнє питання, змінюємо текст кнопки
            if self.current_q_index == len(self.questions) - 1:
                self.next_btn.setText("Завершити тест")
        else:
            self.finish_test()

    def check_answer(self):
        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Увага", "Оберіть один із варіантів відповіді!")
            return

        # Перевіряємо, чи правильна відповідь
        correct_id = self.questions[self.current_q_index]["correct_index"]
        if selected_id == correct_id:
            self.correct_answers += 1

        self.current_q_index += 1
        self.load_question()

    def finish_test(self):
        total = len(self.questions)
        
        # ВИКОРИСТОВУЄМО НАШ CORE МОДУЛЬ
        score = core.calculate_score(self.correct_answers, total)
        passed = core.check_pass_status(score)

        # Зберігаємо результат у базу
        db = database.load_db()
        result_record = {
            "student_id": self.student_id,
            "course_id": self.course["id"],
            "score": score,
            "passed": passed
        }
        db["results"].append(result_record)
        database.save_db(db)

        # Показуємо підсумок
        status_text = "Складено успішно!" if passed else "Не складено. Спробуйте ще."
        QMessageBox.information(self, "Результат",
                                f"Тест завершено!\n"
                                f"Правильних відповідей: {self.correct_answers} з {total}\n"
                                f"Ваш бал: {score}%\n"
                                f"Статус: {status_text}")
        self.accept() # Закриваємо вікно тесту


# --- ДАШБОРД СТУДЕНТА (оновлений) ---
class StudentDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Студента ({self.user['username']})")
        self.resize(500, 500)
        
        self.layout = QVBoxLayout()
        
        self.layout.addWidget(QLabel("<b>Всі доступні курси:</b>"))
        self.available_courses_list = QListWidget()
        self.layout.addWidget(self.available_courses_list)
        
        self.enroll_btn = QPushButton("Приєднатися до обраного курсу")
        self.enroll_btn.clicked.connect(self.join_course)
        self.layout.addWidget(self.enroll_btn)
        
        self.layout.addWidget(QLabel("<hr>"))
        
        self.layout.addWidget(QLabel("<b>Мої курси (записані):</b>"))
        self.my_courses_list = QListWidget()
        self.layout.addWidget(self.my_courses_list)
        
        # ПІДКЛЮЧИЛИ КНОПКУ ЗАПУСКУ ТЕСТУ
        self.start_test_btn = QPushButton("Відкрити курс та пройти тест")
        self.start_test_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.start_test_btn.clicked.connect(self.start_test)
        self.layout.addWidget(self.start_test_btn)
        
        self.setLayout(self.layout)
        self.refresh_lists()

    def refresh_lists(self):
        self.available_courses_list.clear()
        self.my_courses_list.clear()
        
        db = database.load_db()
        enrolled_ids = [e["course_id"] for e in db["enrollments"] if e["student_id"] == self.user["id"]]
        
        for course in db["courses"]:
            item_text = f"{course['id']}. {course['title']} (Питань: {len(course['questions'])})"
            item = QListWidgetItem(item_text)
            item.setData(32, course['id'])
            
            if course['id'] in enrolled_ids:
                self.my_courses_list.addItem(item)
            else:
                self.available_courses_list.addItem(item)

    def join_course(self):
        selected_item = self.available_courses_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть курс зі списку доступних!")
            return
            
        course_id = selected_item.data(32)
        db = database.load_db()
        
        db["enrollments"].append({"student_id": self.user["id"], "course_id": course_id})
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", "Ви успішно приєдналися до курсу!")
        self.refresh_lists()

    def start_test(self):
        selected_item = self.my_courses_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Помилка", "Оберіть курс із списку 'Мої курси'!")
            return

        course_id = selected_item.data(32)
        db = database.load_db()
        
        # Шукаємо дані курсу за його ID
        course_data = None
        for course in db["courses"]:
            if course["id"] == course_id:
                course_data = course
                break
                
        if course_data:
            # Відкриваємо модальне вікно проходження тесту
            test_window = TestExecutionWindow(self.user["id"], course_data)
            test_window.exec_()