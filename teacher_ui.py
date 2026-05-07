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
        self.resize(550, 600)
        
        main_layout = QVBoxLayout()
        
        # Створюємо систему вкладок
        self.tabs = QTabWidget()
        self.tab_create = QWidget()
        self.tab_stats = QWidget()
        
        self.tabs.addTab(self.tab_create, "Створення курсу")
        self.tabs.addTab(self.tab_stats, "Статистика курсу")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        self.setup_create_tab()
        self.setup_stats_tab()
        
        # Підключаємо подію перемикання вкладок
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def setup_create_tab(self):
        """Побудова інтерфейсу для вкладки створення курсу"""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Назва нового курсу:</b>"))
        self.course_title_input = QLineEdit()
        self.course_title_input.setPlaceholderText("Наприклад: Основи роботи з Python")
        layout.addWidget(self.course_title_input)
        
        layout.addWidget(QLabel("<hr>"))
        
        layout.addWidget(QLabel("<b>Додати питання до тесту:</b>"))
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
        
        self.add_q_btn = QPushButton("Додати питання у тест")
        self.add_q_btn.clicked.connect(self.add_question)
        layout.addWidget(self.add_q_btn)
        
        layout.addWidget(QLabel("<b>Список питань поточного курсу:</b>"))
        self.questions_list = QListWidget()
        layout.addWidget(self.questions_list)
        
        self.save_course_btn = QPushButton("ЗБЕРЕГТИ КУРС")
        self.save_course_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.save_course_btn.clicked.connect(self.save_course)
        layout.addWidget(self.save_course_btn)
        
        self.tab_create.setLayout(layout)

    def setup_stats_tab(self):
        """Побудова інтерфейсу для вкладки статистики"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Оберіть ваш курс:</b>"))
        
        self.stats_course_combo = QComboBox()
        self.stats_course_combo.currentIndexChanged.connect(self.load_statistics)
        layout.addWidget(self.stats_course_combo)
        
        layout.addWidget(QLabel("<b>Результати студентів:</b>"))
        self.stats_list = QListWidget()
        layout.addWidget(self.stats_list)
        
        self.tab_stats.setLayout(layout)

    # --- ЛОГІКА СТВОРЕННЯ КУРСУ ---
    def add_question(self):
        q_text = self.question_input.text().strip()
        options = [inp.text().strip() for inp in self.options_inputs]
        
        if not q_text or any(not opt for opt in options):
            QMessageBox.warning(self, "Помилка", "Заповніть питання та всі 4 варіанти відповідей!")
            return
            
        correct_index = self.correct_combo.currentIndex()
        question_data = {"question": q_text, "options": options, "correct_index": correct_index}
        
        self.current_questions.append(question_data)
        self.questions_list.addItem(f"{len(self.current_questions)}. {q_text} (Прав. відп: {correct_index + 1})")
        
        self.question_input.clear()
        for inp in self.options_inputs:
            inp.clear()
        self.correct_combo.setCurrentIndex(0)

    def save_course(self):
        title = self.course_title_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Помилка", "Введіть назву курсу!")
            return
        if not self.current_questions:
            QMessageBox.warning(self, "Помилка", "Додайте хоча б одне питання до тесту!")
            return
            
        db = database.load_db()
        new_course_id = len(db["courses"]) + 1
        
        course_data = {
            "id": new_course_id,
            "teacher_id": self.user["id"],
            "title": title,
            "questions": self.current_questions
        }
        
        db["courses"].append(course_data)
        database.save_db(db)
        QMessageBox.information(self, "Успіх", f"Курс '{title}' успішно збережено!")
        
        self.course_title_input.clear()
        self.questions_list.clear()
        self.current_questions = []

    # --- ЛОГІКА СТАТИСТИКИ ---
    def on_tab_changed(self, index):
        if index == 1: # Перехід на вкладку "Статистика"
            self.load_teacher_courses()

    def load_teacher_courses(self):
        self.stats_course_combo.blockSignals(True) # Тимчасово блокуємо сигнал, щоб не викликати load_statistics завчасно
        self.stats_course_combo.clear()
        
        db = database.load_db()
        for course in db["courses"]:
            if course["teacher_id"] == self.user["id"]:
                self.stats_course_combo.addItem(course["title"], course["id"])
                
        self.stats_course_combo.blockSignals(False)
        self.load_statistics()

    def load_statistics(self):
        self.stats_list.clear()
        course_id = self.stats_course_combo.currentData()
        if not course_id:
            return
            
        db = database.load_db()
        # Шукаємо всі результати саме для обраного курсу
        results = [r for r in db["results"] if r["course_id"] == course_id]
        
        if not results:
            self.stats_list.addItem("Ще немає результатів для цього курсу.")
            return
            
        # Створюємо словник для швидкого пошуку логіна студента за його ID
        users = {u["id"]: u["username"] for u in db["users"]}
        
        for r in results:
            student_name = users.get(r["student_id"], "Невідомий")
            status = "✅ Склав" if r["passed"] else "❌ Не склав"
            self.stats_list.addItem(f"Студент: {student_name} | Оцінка: {r['score']}% | {status}")