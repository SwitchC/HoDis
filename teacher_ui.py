from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QListWidget, QMessageBox)
import database

class TeacherDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.current_questions = [] # Тимчасове сховище питань для створення курсу

        self.setWindowTitle(f"HoDis - Панель Викладача ({self.user['username']})")
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # Назва курсу
        layout.addWidget(QLabel("<b>Назва нового курсу:</b>"))
        self.course_title_input = QLineEdit()
        self.course_title_input.setPlaceholderText("Наприклад: Основи роботи з Python")
        layout.addWidget(self.course_title_input)
        
        layout.addWidget(QLabel("<hr>")) # Візуальний розділювач
        
        # Додавання питання
        layout.addWidget(QLabel("<b>Додати питання до тесту:</b>"))
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Текст питання...")
        layout.addWidget(self.question_input)
        
        # Варіанти відповідей
        self.options_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"Варіант {i+1}")
            self.options_inputs.append(inp)
            layout.addWidget(inp)
            
        # Вибір правильної відповіді
        correct_layout = QHBoxLayout()
        correct_layout.addWidget(QLabel("Правильний варіант:"))
        self.correct_combo = QComboBox()
        self.correct_combo.addItems(["Варіант 1", "Варіант 2", "Варіант 3", "Варіант 4"])
        correct_layout.addWidget(self.correct_combo)
        layout.addLayout(correct_layout)
        
        # Кнопка додавання питання
        self.add_q_btn = QPushButton("Додати питання у тест")
        self.add_q_btn.clicked.connect(self.add_question)
        layout.addWidget(self.add_q_btn)
        
        # Список доданих питань (для візуалізації)
        layout.addWidget(QLabel("<b>Список питань поточного курсу:</b>"))
        self.questions_list = QListWidget()
        layout.addWidget(self.questions_list)
        
        # Кнопка збереження всього курсу
        self.save_course_btn = QPushButton("ЗБЕРЕГТИ КУРС")
        self.save_course_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.save_course_btn.clicked.connect(self.save_course)
        layout.addWidget(self.save_course_btn)
        
        self.setLayout(layout)

    def add_question(self):
        q_text = self.question_input.text().strip()
        options = [inp.text().strip() for inp in self.options_inputs]
        
        if not q_text or any(not opt for opt in options):
            QMessageBox.warning(self, "Помилка", "Заповніть питання та всі 4 варіанти відповідей!")
            return
            
        correct_index = self.correct_combo.currentIndex()
        
        question_data = {
            "question": q_text,
            "options": options,
            "correct_index": correct_index
        }
        
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