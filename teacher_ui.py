import os
import shutil
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QListWidget, 
                             QMessageBox, QTabWidget, QFileDialog, QListWidgetItem)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import database

class TeacherDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.current_questions = []

        self.setWindowTitle(f"HoDis - Панель Викладача ({self.user['username']})")
        self.resize(700, 750)
        
        main_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tab_course = QWidget()
        self.tab_test = QWidget()
        self.tab_stats = QWidget()
        
        self.tabs.addTab(self.tab_course, "1. Управління курсами та файлами")
        self.tabs.addTab(self.tab_test, "2. Створення тесту")
        self.tabs.addTab(self.tab_stats, "3. Статистика")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        self.setup_course_tab()
        self.setup_test_tab()
        self.setup_stats_tab()
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_combo_boxes()

    # --- Вкладка 1: Управління курсами ---
    def setup_course_tab(self):
        layout = QVBoxLayout()
        
        # Блок створення курсу
        layout.addWidget(QLabel("<b>Назва нового курсу:</b>"))
        self.course_title_input = QLineEdit()
        self.course_title_input.setPlaceholderText("Наприклад: Програмування на Python")
        layout.addWidget(self.course_title_input)
        
        self.create_course_btn = QPushButton("СТВОРИТИ КУРС")
        self.create_course_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.create_course_btn.clicked.connect(self.create_course)
        layout.addWidget(self.create_course_btn)
        
        layout.addWidget(QLabel("<hr>"))
        
        # Блок управління матеріалами (UR4, FR2 розширено)
        layout.addWidget(QLabel("<b>Управління матеріалами курсу:</b>"))
        self.material_course_combo = QComboBox()
        self.material_course_combo.currentIndexChanged.connect(self.load_course_materials)
        layout.addWidget(self.material_course_combo)
        
        self.materials_list = QListWidget()
        layout.addWidget(self.materials_list)
        
        mat_btn_layout = QHBoxLayout()
        self.open_mat_btn = QPushButton("👁️ Відкрити файл")
        self.open_mat_btn.clicked.connect(self.open_material)
        mat_btn_layout.addWidget(self.open_mat_btn)
        
        self.delete_mat_btn = QPushButton("🗑️ Видалити файл")
        self.delete_mat_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_mat_btn.clicked.connect(self.delete_material)
        mat_btn_layout.addWidget(self.delete_mat_btn)
        
        self.upload_btn = QPushButton("📎 Завантажити новий")
        self.upload_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.upload_btn.clicked.connect(self.upload_material)
        mat_btn_layout.addWidget(self.upload_btn)
        
        layout.addLayout(mat_btn_layout)
        self.tab_course.setLayout(layout)

    def create_course(self):
        title = self.course_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Помилка", "Введіть назву курсу!")
            return
            
        db = database.load_db()
        new_course_id = len(db.get("courses", [])) + 1
        course_data = {"id": new_course_id, "teacher_id": self.user["id"], "title": title, "materials": []}
        db["courses"].append(course_data)
        database.save_db(db)
        
        QMessageBox.information(self, "Успіх", f"Курс '{title}' створено!")
        self.course_title_input.clear()
        self.refresh_combo_boxes()

    def load_course_materials(self):
        self.materials_list.clear()
        course_id = self.material_course_combo.currentData()
        if not course_id: return
        
        db = database.load_db()
        for course in db.get("courses", []):
            if course["id"] == course_id:
                for mat in course.get("materials", []):
                    item = QListWidgetItem(mat["name"])
                    item.setData(32, mat["path"]) # Зберігаємо шлях до файлу приховано
                    self.materials_list.addItem(item)
                break

    def upload_material(self):
        course_id = self.material_course_combo.currentData()
        if not course_id:
            QMessageBox.warning(self, "Помилка", "Спершу оберіть курс!")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Оберіть файл для курсу", "", "Навчальні матеріали (*.pdf *.docx *.mp4 *.png *.txt)"
        )
        
        if file_path:
            if not os.path.exists(database.UPLOAD_DIR):
                os.makedirs(database.UPLOAD_DIR)
                
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(database.UPLOAD_DIR, file_name)
            
            try:
                shutil.copy2(file_path, dest_path)
                database.add_material_to_course(course_id, file_name, dest_path)
                QMessageBox.information(self, "Успіх", f"Файл '{file_name}' успішно завантажено!")
                self.load_course_materials() # Оновлюємо список
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося скопіювати файл:\n{str(e)}")

    def open_material(self):
        selected = self.materials_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Увага", "Оберіть файл зі списку!")
            return
        file_path = selected.data(32)
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        else:
            QMessageBox.critical(self, "Помилка", "Файл не знайдено на диску!")

    def delete_material(self):
        selected = self.materials_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Увага", "Оберіть файл для видалення!")
            return
            
        course_id = self.material_course_combo.currentData()
        file_path = selected.data(32)
        
        confirm = QMessageBox.question(self, "Підтвердження", "Видалити цей файл назавжди?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            database.delete_material_from_course(course_id, file_path)
            QMessageBox.information(self, "Успіх", "Файл видалено.")
            self.load_course_materials()

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
        new_test_id = len(db.get("tests", [])) + 1
        test_data = {
            "id": new_test_id,
            "course_id": course_id,
            "title": title,
            "questions": self.current_questions
        }
        db.setdefault("tests", []).append(test_data)
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
            for test in db.get("tests", []):
                if test["course_id"] == course_id:
                    self.stats_test_combo.addItem(test["title"], test["id"])
                    
        self.stats_test_combo.blockSignals(False)
        self.load_statistics()

    def load_statistics(self):
        self.stats_list.clear()
        test_id = self.stats_test_combo.currentData()
        if not test_id: return
            
        db = database.load_db()
        results = [r for r in db.get("results", []) if r["test_id"] == test_id]
        
        if not results:
            self.stats_list.addItem("Ще немає результатів для цього тесту.")
            return
            
        users = {u["id"]: u["username"] for u in db.get("users", [])}
        for r in results:
            student_name = users.get(r["student_id"], "Невідомий")
            status = "✅ Склав" if r["passed"] else "❌ Не склав"
            self.stats_list.addItem(f"Студент: {student_name} | Оцінка: {r['score']}% | {status}")

    # --- Загальні методи ---
    def on_tab_changed(self, index):
        self.refresh_combo_boxes()

    def refresh_combo_boxes(self):
        self.test_course_combo.blockSignals(True)
        self.stats_course_combo.blockSignals(True)
        self.material_course_combo.blockSignals(True)
        
        self.test_course_combo.clear()
        self.stats_course_combo.clear()
        self.material_course_combo.clear()
        
        db = database.load_db()
        for course in db.get("courses", []):
            if course["teacher_id"] == self.user["id"]:
                self.test_course_combo.addItem(course["title"], course["id"])
                self.stats_course_combo.addItem(course["title"], course["id"])
                self.material_course_combo.addItem(course["title"], course["id"])
        
        self.test_course_combo.blockSignals(False)
        self.stats_course_combo.blockSignals(False)
        self.material_course_combo.blockSignals(False)
        
        self.update_stats_tests_combo()
        self.load_course_materials()