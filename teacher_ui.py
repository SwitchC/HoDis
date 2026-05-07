from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QListWidget, 
                             QMessageBox, QTabWidget)
import database

class TeacherDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.current_questions = []

        self.setWindowTitle(f"HoDis - Панель Викладача ({self.user['username']})")
        self.resize(600, 650)
        
        main_layout = QVBoxLayout()
        
        # Створюємо 3 вкладки
        self.tabs = QTabWidget()
        self.tab_course = QWidget()
        self.tab_test = QWidget()
        self.tab_stats = QWidget()
        
        self.tabs.addTab(self.tab_course, "1. Створення курсу")
        self.tabs.addTab(self.tab_test, "2. Створення тесту")
        self.tabs.addTab(self.tab_stats, "3. Статистика")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        self.setup_course_tab()
        self.setup_test_tab()
        self.setup_stats_tab()
        
        # Оновлюємо випадаючі списки при перемиканні вкладок
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_combo_boxes()

    # --- Вкладка 1: Створення КУРСУ ---
    def setup_course_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Назва нового курсу:</b>"))
        self.course_title_input = QLineEdit()
        self.course_title_input.setPlaceholderText("Наприклад: Програмування на Python")
        layout.addWidget(self.course_title_input)
        
        self.create_course_btn = QPushButton("СТВОРИТИ КУРС")
        self.create_course_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.create_course_btn.clicked.connect(self.create_course)
        layout.addWidget(self.create_course_btn)
        
        layout.addWidget(QLabel("<hr><b>Ваші курси:</b>"))
        self.my_courses_list = QListWidget()
        layout.addWidget(self.my_courses_list)
        
        self.tab_course.setLayout(layout)

    def create_course(self):
        title = self.course_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Помилка", "Введіть назву курсу!")
            return
            
        db = database.load_db()
        new_course_id = len(db["courses"]) + 1
        course_data = {"id": new_course_id, "teacher_id": self.user["id"], "title": title}
        db["courses"].append(course_data)
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", f"Курс '{title}' створено!")
        self.course_title_input.clear()
        self.refresh_combo_boxes()

    # --- Вкладка 2: Створення ТЕСТУ ---
    def setup_test_tab(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>1. Оберіть курс:</b>"))
        self.test_course_combo = QComboBox()
        layout.addWidget(self.test_course_combo)
        
        layout.addWidget(QLabel("<b>2. Назва тесту:</b>"))
        self.test_title_input = QLineEdit()
        self.test_title_input.setPlaceholderText("Наприклад: Тест №1. Базові типи даних")
        layout.addWidget(self.test_title_input)
        
        layout.addWidget(QLabel("<hr><b>3. Додати питання:</b>"))
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Текст питання...")
        layout.addWidget(self.question_input)
        
        self.options_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"Варіант {i+1}")
            self.options_inputs.append(inp)
            layout.addWidget(inp)
            
        correct_layout = QHBoxLayout()
        correct_layout.addWidget(QLabel("Правильний варіант:"))
        self.correct_combo = QComboBox()
        self.correct_combo.addItems(["Варіант 1", "Варіант 2", "Варіант 3", "Варіант 4"])
        correct_layout.addWidget(self.correct_combo)
        layout.addLayout(correct_layout)
        
        self.add_q_btn = QPushButton("Додати питання до списку")
        self.add_q_btn.clicked.connect(self.add_question)
        layout.addWidget(self.add_q_btn)
        
        self.questions_list = QListWidget()
        layout.addWidget(self.questions_list)
        
        self.save_test_btn = QPushButton("ЗБЕРЕГТИ ТЕСТ")
        self.save_test_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.save_test_btn.clicked.connect(self.save_test)
        layout.addWidget(self.save_test_btn)
        
        self.tab_test.setLayout(layout)

    def add_question(self):
        q_text = self.question_input.text().strip()
        options = [inp.text().strip() for inp in self.options_inputs]
        
        if not q_text or any(not opt for opt in options):
            QMessageBox.warning(self, "Помилка", "Заповніть питання та всі варіанти!")
            return
            
        correct_index = self.correct_combo.currentIndex()
        self.current_questions.append({"question": q_text, "options": options, "correct_index": correct_index})
        self.questions_list.addItem(f"{len(self.current_questions)}. {q_text} (Відповідь: {correct_index + 1})")
        
        self.question_input.clear()
        for inp in self.options_inputs: inp.clear()
        self.correct_combo.setCurrentIndex(0)

    def save_test(self):
        course_id = self.test_course_combo.currentData()
        title = self.test_title_input.text().strip()
        
        if not course_id:
            QMessageBox.warning(self, "Помилка", "Спершу створіть та оберіть курс!")
            return
        if not title or not self.current_questions:
            QMessageBox.warning(self, "Помилка", "Введіть назву тесту та додайте хоча б 1 питання!")
            return
            
        db = database.load_db()
        new_test_id = len(db["tests"]) + 1
        test_data = {
            "id": new_test_id,
            "course_id": course_id,
            "title": title,
            "questions": self.current_questions
        }
        db["tests"].append(test_data)
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", f"Тест '{title}' збережено!")
        self.test_title_input.clear()
        self.questions_list.clear()
        self.current_questions = []

    # --- Вкладка 3: СТАТИСТИКА ---
    def setup_stats_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Оберіть курс:</b>"))
        self.stats_course_combo = QComboBox()
        self.stats_course_combo.currentIndexChanged.connect(self.update_stats_tests_combo)
        layout.addWidget(self.stats_course_combo)
        
        layout.addWidget(QLabel("<b>Оберіть тест:</b>"))
        self.stats_test_combo = QComboBox()
        self.stats_test_combo.currentIndexChanged.connect(self.load_statistics)
        layout.addWidget(self.stats_test_combo)
        
        layout.addWidget(QLabel("<b>Результати студентів:</b>"))
        self.stats_list = QListWidget()
        layout.addWidget(self.stats_list)
        
        self.tab_stats.setLayout(layout)

    def update_stats_tests_combo(self):
        self.stats_test_combo.blockSignals(True)
        self.stats_test_combo.clear()
        course_id = self.stats_course_combo.currentData()
        
        if course_id:
            db = database.load_db()
            for test in db["tests"]:
                if test["course_id"] == course_id:
                    self.stats_test_combo.addItem(test["title"], test["id"])
                    
        self.stats_test_combo.blockSignals(False)
        self.load_statistics()

    def load_statistics(self):
        self.stats_list.clear()
        test_id = self.stats_test_combo.currentData()
        if not test_id: return
            
        db = database.load_db()
        results = [r for r in db["results"] if r["test_id"] == test_id]
        
        if not results:
            self.stats_list.addItem("Ще немає результатів для цього тесту.")
            return
            
        users = {u["id"]: u["username"] for u in db["users"]}
        for r in results:
            student_name = users.get(r["student_id"], "Невідомий")
            status = "✅ Склав" if r["passed"] else "❌ Не склав"
            self.stats_list.addItem(f"Студент: {student_name} | Оцінка: {r['score']}% | {status}")

    # --- Загальні методи ---
    def on_tab_changed(self, index):
        self.refresh_combo_boxes()

    def refresh_combo_boxes(self):
        """Оновлює списки курсів у всіх вкладках"""
        self.test_course_combo.clear()
        self.stats_course_combo.clear()
        self.my_courses_list.clear()
        
        db = database.load_db()
        for course in db["courses"]:
            if course["teacher_id"] == self.user["id"]:
                self.my_courses_list.addItem(f"Курс: {course['title']}")
                self.test_course_combo.addItem(course["title"], course["id"])
                self.stats_course_combo.addItem(course["title"], course["id"])
        
        self.update_stats_tests_combo()