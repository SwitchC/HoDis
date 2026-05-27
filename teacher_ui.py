import os
import shutil
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QListWidget, 
                             QMessageBox, QTabWidget, QFileDialog, QListWidgetItem,
                             QTextEdit, QDialog, QFormLayout, QDialogButtonBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QDesktopServices, QColor
from PyQt5.QtCore import QUrl
import database

# --- НОВЕ ВІКНО ДЛЯ ПЕРЕГЛЯДУ ДЕТАЛЕЙ ТЕСТУ ---
class ResultDetailsDialog(QDialog):
    def __init__(self, parent, result_data, student_name):
        super().__init__(parent)
        self.setWindowTitle(f"Деталізація результату: {student_name}")
        self.resize(700, 450)
        
        layout = QVBoxLayout(self)
        
        status_text = "Склав" if result_data.get('passed') else "Не склав"
        lbl = QLabel(f"<b>Оцінка:</b> {result_data.get('score')}% | <b>Статус:</b> {status_text}")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        details = result_data.get('details', [])
        
        if not details:
            layout.addWidget(QLabel("<i>Детальна інформація відсутня (стара спроба).</i>"))
        else:
            self.table.setColumnCount(4)
            self.table.setRowCount(len(details))
            self.table.setHorizontalHeaderLabels(["Питання", "Відповідь студента", "Правильна відповідь", "Час (с)"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for i, row in enumerate(details):
                q_item = QTableWidgetItem(row.get('question', ''))
                
                s_ans = row.get('student_answer', '')
                c_ans = row.get('correct_answer', '')
                
                s_item = QTableWidgetItem(s_ans)
                if not row.get('is_correct', False):
                    s_item.setForeground(QColor("red"))
                else:
                    s_item.setForeground(QColor("green"))
                    
                c_item = QTableWidgetItem(c_ans)
                t_item = QTableWidgetItem(str(row.get('time_spent_sec', 0)))
                
                self.table.setItem(i, 0, q_item)
                self.table.setItem(i, 1, s_item)
                self.table.setItem(i, 2, c_item)
                self.table.setItem(i, 3, t_item)
                
            layout.addWidget(self.table)
            
        btn = QPushButton("Закрити")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class TaskGradeDialog(QDialog):
    def __init__(self, parent=None, sub_data=None, task_title=""):
        super().__init__(parent)
        self.setWindowTitle(f"Оцінювання: {task_title}")
        self.resize(450, 350)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Відповідь студента:</b>"))
        
        self.answer_view = QTextEdit()
        self.answer_view.setReadOnly(True)
        self.answer_view.setText(sub_data.get("answer_text", ""))
        layout.addWidget(self.answer_view)
        
        form = QFormLayout()
        self.score_input = QLineEdit()
        self.score_input.setPlaceholderText("Бал (напр. 95)")
        if sub_data.get("score") is not None:
            self.score_input.setText(str(sub_data["score"]))
        form.addRow("Оцінка:", self.score_input)
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_score(self):
        return self.score_input.text().strip()

class TeacherDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.current_questions = []

        self.setWindowTitle(f"HoDis - Панель Викладача ({self.user['username']})")
        self.resize(850, 800) 
        
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.tab_course = QWidget()
        self.tab_test = QWidget()
        self.tab_tasks = QWidget()
        self.tab_stats = QWidget()
        
        self.tabs.addTab(self.tab_course, "1. Курси та матеріали")
        self.tabs.addTab(self.tab_test, "2. Управління тестами")
        self.tabs.addTab(self.tab_tasks, "3. Практичні завдання")
        self.tabs.addTab(self.tab_stats, "4. Перевірка та Статистика")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        self.setup_course_tab()
        self.setup_test_tab()
        self.setup_tasks_tab()
        self.setup_stats_tab()
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_combo_boxes()

    # Вкладка 1: КУРСИ ТА МАТЕРІАЛИ
    def setup_course_tab(self):
        main_course_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("<b>1. Назва нового курсу:</b>"))
        self.course_title_input = QLineEdit()
        left_layout.addWidget(self.course_title_input)
        
        self.create_course_btn = QPushButton("СТВОРИТИ КУРС")
        self.create_course_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.create_course_btn.clicked.connect(self.create_course)
        left_layout.addWidget(self.create_course_btn)
        
        left_layout.addWidget(QLabel("<hr><b>2. Завантажити новий матеріал:</b>"))
        self.upload_course_combo = QComboBox()
        left_layout.addWidget(self.upload_course_combo)
        
        self.upload_btn = QPushButton("📎 Обрати та завантажити файл")
        self.upload_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.upload_btn.clicked.connect(self.upload_material)
        left_layout.addWidget(self.upload_btn)
        left_layout.addStretch()
        main_course_layout.addLayout(left_layout, 1)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>3. Управління матеріалами курсу:</b>"))
        self.manage_course_combo = QComboBox()
        self.manage_course_combo.currentIndexChanged.connect(self.load_course_materials)
        right_layout.addWidget(self.manage_course_combo)
        
        self.materials_list = QListWidget()
        right_layout.addWidget(self.materials_list)
        
        mat_btn_layout = QHBoxLayout()
        self.open_mat_btn = QPushButton("👁️ Відкрити файл")
        self.open_mat_btn.clicked.connect(self.open_material)
        mat_btn_layout.addWidget(self.open_mat_btn)
        
        self.delete_mat_btn = QPushButton("🗑️ Видалити файл")
        self.delete_mat_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_mat_btn.clicked.connect(self.delete_material)
        mat_btn_layout.addWidget(self.delete_mat_btn)
        
        right_layout.addLayout(mat_btn_layout)
        main_course_layout.addLayout(right_layout, 1)
        self.tab_course.setLayout(main_course_layout)

    def create_course(self):
        title = self.course_title_input.text().strip()
        if not title: return
        db = database.load_db()
        new_course_id = len(db.get("courses", [])) + 1
        db.setdefault("courses", []).append({"id": new_course_id, "teacher_id": self.user["id"], "title": title, "materials": []})
        database.save_db(db)
        QMessageBox.information(self, "Успіх", f"Курс '{title}' створено!")
        self.course_title_input.clear()
        self.refresh_combo_boxes()

    def upload_material(self):
        course_id = self.upload_course_combo.currentData()
        if not course_id: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Оберіть файл", "", "Матеріали (*.pdf *.docx *.mp4 *.png *.txt)")
        if file_path:
            if not os.path.exists(database.UPLOAD_DIR): os.makedirs(database.UPLOAD_DIR)
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(database.UPLOAD_DIR, file_name)
            try:
                shutil.copy2(file_path, dest_path)
                database.add_material_to_course(course_id, file_name, dest_path)
                self.load_course_materials()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося скопіювати файл:\n{e}")

    def load_course_materials(self):
        self.materials_list.clear()
        course_id = self.manage_course_combo.currentData()
        if not course_id: return
        db = database.load_db()
        for course in db.get("courses", []):
            if course["id"] == course_id:
                for mat in course.get("materials", []):
                    item = QListWidgetItem(mat["name"])
                    item.setData(32, mat["path"]) 
                    self.materials_list.addItem(item)

    def open_material(self):
        selected = self.materials_list.currentItem()
        if not selected: return
        file_path = selected.data(32)
        if os.path.exists(file_path): QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))

    def delete_material(self):
        selected = self.materials_list.currentItem()
        if not selected: return
        course_id = self.manage_course_combo.currentData()
        file_path = selected.data(32)
        database.delete_material_from_course(course_id, file_path)
        self.load_course_materials()

    # Вкладка 2: УПРАВЛІННЯ ТЕСТАМИ
    def setup_test_tab(self):
        main_test_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("<b>1. Оберіть курс:</b>"))
        self.test_course_combo = QComboBox()
        self.test_course_combo.currentIndexChanged.connect(self.load_existing_tests)
        left_layout.addWidget(self.test_course_combo)
        
        left_layout.addWidget(QLabel("<b>2. Назва нового тесту:</b>"))
        self.test_title_input = QLineEdit()
        left_layout.addWidget(self.test_title_input)
        
        left_layout.addWidget(QLabel("<hr><b>3. Додати питання:</b>"))
        self.question_input = QLineEdit()
        left_layout.addWidget(self.question_input)
        
        self.options_inputs = [QLineEdit() for _ in range(4)]
        for i, inp in enumerate(self.options_inputs):
            inp.setPlaceholderText(f"Варіант {i+1}")
            left_layout.addWidget(inp)
            
        correct_layout = QHBoxLayout()
        correct_layout.addWidget(QLabel("Правильний варіант:"))
        self.correct_combo = QComboBox()
        self.correct_combo.addItems(["Варіант 1", "Варіант 2", "Варіант 3", "Варіант 4"])
        correct_layout.addWidget(self.correct_combo)
        left_layout.addLayout(correct_layout)
        
        self.add_q_btn = QPushButton("Додати питання до списку")
        self.add_q_btn.clicked.connect(self.add_question)
        left_layout.addWidget(self.add_q_btn)
        
        self.questions_list = QListWidget()
        left_layout.addWidget(self.questions_list)
        
        self.save_test_btn = QPushButton("ЗБЕРЕГТИ НОВИЙ ТЕСТ")
        self.save_test_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.save_test_btn.clicked.connect(self.save_test)
        left_layout.addWidget(self.save_test_btn)
        
        main_test_layout.addLayout(left_layout, 2)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Існуючі тести в обраному курсі:</b>"))
        self.existing_tests_list = QListWidget()
        right_layout.addWidget(self.existing_tests_list)
        
        self.delete_test_btn = QPushButton("🗑️ Видалити обраний тест")
        self.delete_test_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
        self.delete_test_btn.clicked.connect(self.delete_test)
        right_layout.addWidget(self.delete_test_btn)
        
        main_test_layout.addLayout(right_layout, 1)
        self.tab_test.setLayout(main_test_layout)

    def add_question(self):
        q_text = self.question_input.text().strip()
        options = [inp.text().strip() for inp in self.options_inputs]
        if not q_text or any(not opt for opt in options): return
        correct_index = self.correct_combo.currentIndex()
        self.current_questions.append({"question": q_text, "options": options, "correct_index": correct_index})
        self.questions_list.addItem(f"{q_text} (Відповідь: {correct_index + 1})")
        self.question_input.clear()
        for inp in self.options_inputs: inp.clear()

    def save_test(self):
        course_id = self.test_course_combo.currentData()
        title = self.test_title_input.text().strip()
        if not course_id or not title or not self.current_questions: return
        db = database.load_db()
        new_test_id = len(db.get("tests", [])) + 1
        db.setdefault("tests", []).append({"id": new_test_id, "course_id": course_id, "title": title, "questions": self.current_questions})
        database.save_db(db)
        QMessageBox.information(self, "Успіх", f"Тест збережено!")
        self.test_title_input.clear()
        self.questions_list.clear()
        self.current_questions = []
        self.load_existing_tests() 

    def load_existing_tests(self):
        self.existing_tests_list.clear()
        course_id = self.test_course_combo.currentData()
        if not course_id: return
        db = database.load_db()
        for test in db.get("tests", []):
            if test["course_id"] == course_id:
                item = QListWidgetItem(f"{test['title']} (Питань: {len(test['questions'])})")
                item.setData(32, test["id"])
                self.existing_tests_list.addItem(item)

    def delete_test(self):
        selected = self.existing_tests_list.currentItem()
        if not selected: return
        test_id = selected.data(32)
        confirm = QMessageBox.question(self, "Підтвердження", "Видалити цей тест?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            database.delete_test(test_id)
            self.load_existing_tests()
            self.update_stats_data()

    # Вкладка 3: УПРАВЛІННЯ ПРАКТИЧНИМИ ЗАВДАННЯМИ
    def setup_tasks_tab(self):
        main_task_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("<b>1. Оберіть курс:</b>"))
        self.task_course_combo = QComboBox()
        self.task_course_combo.currentIndexChanged.connect(self.load_existing_tasks)
        left_layout.addWidget(self.task_course_combo)
        
        left_layout.addWidget(QLabel("<b>2. Назва нового завдання:</b>"))
        self.task_title_input = QLineEdit()
        left_layout.addWidget(self.task_title_input)
        
        left_layout.addWidget(QLabel("<b>3. Детальний опис завдання:</b>"))
        self.task_desc_input = QTextEdit()
        left_layout.addWidget(self.task_desc_input)
        
        self.save_task_btn = QPushButton("ЗБЕРЕГТИ НОВЕ ЗАВДАННЯ")
        self.save_task_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.save_task_btn.clicked.connect(self.save_practical_task)
        left_layout.addWidget(self.save_task_btn)
        main_task_layout.addLayout(left_layout, 2)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Існуючі завдання:</b>"))
        self.existing_tasks_list = QListWidget()
        right_layout.addWidget(self.existing_tasks_list)
        
        self.delete_task_btn = QPushButton("🗑️ Видалити обране завдання")
        self.delete_task_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
        self.delete_task_btn.clicked.connect(self.delete_practical_task)
        right_layout.addWidget(self.delete_task_btn)
        main_task_layout.addLayout(right_layout, 1)
        self.tab_tasks.setLayout(main_task_layout)

    def save_practical_task(self):
        course_id = self.task_course_combo.currentData()
        title = self.task_title_input.text().strip()
        desc = self.task_desc_input.toPlainText().strip()
        if not course_id or not title or not desc: return
        database.add_practical_task(course_id, title, desc)
        self.task_title_input.clear()
        self.task_desc_input.clear()
        self.load_existing_tasks()

    def load_existing_tasks(self):
        self.existing_tasks_list.clear()
        course_id = self.task_course_combo.currentData()
        if not course_id: return
        db = database.load_db()
        for task in db.get("practical_tasks", []):
            if task["course_id"] == course_id:
                item = QListWidgetItem(task['title'])
                item.setData(32, task["id"])
                self.existing_tasks_list.addItem(item)

    def delete_practical_task(self):
        selected = self.existing_tasks_list.currentItem()
        if not selected: return
        task_id = selected.data(32)
        confirm = QMessageBox.question(self, "Підтвердження", "Видалити це завдання?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            database.delete_practical_task(task_id)
            self.load_existing_tasks()
            self.update_stats_data()

    # --- ОНОВЛЕНА Вкладка 4: СТАТИСТИКА ТА ПЕРЕВІРКА ---
    def setup_stats_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Оберіть курс для аналізу:</b>"))
        self.stats_course_combo = QComboBox()
        self.stats_course_combo.currentIndexChanged.connect(self.update_stats_data)
        layout.addWidget(self.stats_course_combo)
        
        # Блок тестів з новою кнопкою деталізації
        layout.addWidget(QLabel("<hr><b>Статистика автоматичних тестів:</b>"))
        self.stats_test_combo = QComboBox()
        self.stats_test_combo.currentIndexChanged.connect(self.load_test_statistics)
        layout.addWidget(self.stats_test_combo)
        
        self.stats_list = QListWidget()
        layout.addWidget(self.stats_list)
        
        self.view_details_btn = QPushButton("🔍 Переглянути деталі спроби")
        self.view_details_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.view_details_btn.clicked.connect(self.view_test_details)
        layout.addWidget(self.view_details_btn)
        
        # Блок ручної перевірки завдань
        layout.addWidget(QLabel("<hr><b>Роботи студентів на перевірці:</b>"))
        self.submissions_list = QListWidget()
        layout.addWidget(self.submissions_list)
        
        self.grade_btn = QPushButton("📝 Перевірити та оцінити роботу")
        self.grade_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; font-weight: bold;")
        self.grade_btn.clicked.connect(self.grade_submission)
        layout.addWidget(self.grade_btn)
        
        self.tab_stats.setLayout(layout)

    def update_stats_data(self):
        self.stats_test_combo.blockSignals(True)
        self.stats_test_combo.clear()
        course_id = self.stats_course_combo.currentData()
        
        if course_id:
            db = database.load_db()
            for test in db.get("tests", []):
                if test["course_id"] == course_id:
                    self.stats_test_combo.addItem(test["title"], test["id"])
                    
        self.stats_test_combo.blockSignals(False)
        self.load_test_statistics()
        self.load_submissions()

    def load_test_statistics(self):
        self.stats_list.clear()
        test_id = self.stats_test_combo.currentData()
        if not test_id: return
        db = database.load_db()
        results = [r for r in db.get("results", []) if r["test_id"] == test_id]
        users = {u["id"]: u["username"] for u in db.get("users", [])}
        for r in results:
            student_name = users.get(r['student_id'], 'Невідомий')
            item = QListWidgetItem(f"Студент: {student_name} | Оцінка: {r['score']}%")
            item.setData(32, r) # Зберігаємо весь об'єкт результату (включаючи масив деталей)
            item.setData(33, student_name)
            self.stats_list.addItem(item)

    def view_test_details(self):
        selected = self.stats_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Увага", "Оберіть результат зі списку для деталізації!")
            return
            
        result_data = selected.data(32)
        student_name = selected.data(33)
        dialog = ResultDetailsDialog(self, result_data, student_name)
        dialog.exec_()

    def load_submissions(self):
        self.submissions_list.clear()
        course_id = self.stats_course_combo.currentData()
        if not course_id: return
        
        db = database.load_db()
        course_tasks = {t["id"]: t["title"] for t in db.get("practical_tasks", []) if t["course_id"] == course_id}
        users = {u["id"]: u["username"] for u in db.get("users", [])}
        
        for sub in db.get("task_submissions", []):
            if sub["task_id"] in course_tasks:
                student_name = users.get(sub["student_id"], "Невідомий")
                task_title = course_tasks[sub["task_id"]]
                status = f"✅ Оцінено ({sub['score']} б.)" if sub["status"] == "Оцінено" else "⏳ На перевірці"
                
                item = QListWidgetItem(f"[{status}] Студент: {student_name} | Завдання: {task_title}")
                item.setData(32, sub)
                item.setData(33, task_title)
                self.submissions_list.addItem(item)

    def grade_submission(self):
        selected = self.submissions_list.currentItem()
        if not selected: return
        sub_data = selected.data(32)
        task_title = selected.data(33)
        dialog = TaskGradeDialog(self, sub_data, task_title)
        if dialog.exec_() == QDialog.Accepted:
            score_str = dialog.get_score()
            if not score_str.isdigit(): return
            database.grade_task(sub_data["id"], int(score_str))
            self.load_submissions()

    def on_tab_changed(self, index):
        self.refresh_combo_boxes()

    def refresh_combo_boxes(self):
        self.upload_course_combo.blockSignals(True)
        self.manage_course_combo.blockSignals(True)
        self.test_course_combo.blockSignals(True)
        self.stats_course_combo.blockSignals(True)
        self.task_course_combo.blockSignals(True)
        
        self.upload_course_combo.clear()
        self.manage_course_combo.clear()
        self.test_course_combo.clear()
        self.stats_course_combo.clear()
        self.task_course_combo.clear()
        
        db = database.load_db()
        for course in db.get("courses", []):
            if course["teacher_id"] == self.user["id"]:
                self.upload_course_combo.addItem(course["title"], course["id"])
                self.manage_course_combo.addItem(course["title"], course["id"])
                self.test_course_combo.addItem(course["title"], course["id"])
                self.stats_course_combo.addItem(course["title"], course["id"])
                self.task_course_combo.addItem(course["title"], course["id"])
        
        self.upload_course_combo.blockSignals(False)
        self.manage_course_combo.blockSignals(False)
        self.test_course_combo.blockSignals(False)
        self.stats_course_combo.blockSignals(False)
        self.task_course_combo.blockSignals(False)
        
        self.update_stats_data()
        self.load_existing_tests()
        self.load_existing_tasks()
        self.load_course_materials()