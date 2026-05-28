import os
import time
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QListWidget, 
                             QPushButton, QMessageBox, QListWidgetItem,
                             QDialog, QRadioButton, QButtonGroup, QHBoxLayout, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QDesktopServices, QColor
from PyQt5.QtCore import QUrl, QThread, pyqtSignal
import database
import core
import ml_engine

class MLExplainThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, course_id, question, student_answer, correct_answer):
        super().__init__()
        self.course_id = course_id
        self.question = question
        self.student_answer = student_answer
        self.correct_answer = correct_answer

    def run(self):
        explanation = ml_engine.engine.explain_error(
            self.course_id, self.question, self.student_answer, self.correct_answer
        )
        self.finished_signal.emit(explanation)


class StudentResultDetailsDialog(QDialog):
    def __init__(self, parent, result_data, test_title, course_id):
        super().__init__(parent)
        self.result_data = result_data
        self.course_id = course_id
        
        self.setWindowTitle(f"Аналіз помилок: {test_title}")
        self.resize(850, 600)
        
        layout = QVBoxLayout(self)
        
        status_text = "Складено" if result_data.get('passed') else "Не складено"
        lbl = QLabel(f"<b>Ваш бал:</b> {result_data.get('score')}% | <b>Статус:</b> {status_text}")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        details = result_data.get('details', [])
        
        if not details:
            layout.addWidget(QLabel("<i>Детальна інформація відсутня для цієї спроби.</i>"))
        else:
            self.table.setColumnCount(4)
            self.table.setRowCount(len(details))
            self.table.setHorizontalHeaderLabels(["Питання", "Ваша відповідь", "Правильна", "Дія"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for i, row in enumerate(details):
                q_text = row.get('question', '')
                s_ans = row.get('student_answer', '')
                c_ans = row.get('correct_answer', '')
                is_correct = row.get('is_correct', False)
                
                self.table.setItem(i, 0, QTableWidgetItem(q_text))
                
                s_item = QTableWidgetItem(s_ans)
                if not is_correct:
                    s_item.setForeground(QColor("red"))
                    
                    explain_btn = QPushButton("🤖 Пояснити ШІ")
                    explain_btn.setStyleSheet("background-color: #673AB7; color: white;")

                    explain_btn.clicked.connect(lambda ch, q=q_text, sa=s_ans, ca=c_ans: self.ask_ai(q, sa, ca))
                    self.table.setCellWidget(i, 3, explain_btn)
                else:
                    s_item.setForeground(QColor("green"))
                    self.table.setItem(i, 3, QTableWidgetItem("✅ Правильно"))
                    
                self.table.setItem(i, 1, s_item)
                self.table.setItem(i, 2, QTableWidgetItem(c_ans))
                
            layout.addWidget(self.table)
            
        layout.addWidget(QLabel("<b>Відповідь штучного інтелекту:</b>"))
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setStyleSheet("background-color: #f3e5f5; font-size: 14px; padding: 10px;")
        self.ai_output.setPlaceholderText("Натисніть 'Пояснити ШІ' біля вашої помилки, щоб отримати персоналізоване пояснення на основі лекцій...")
        layout.addWidget(self.ai_output)
        
        btn = QPushButton("Закрити")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def ask_ai(self, question, student_answer, correct_answer):
        self.ai_output.setText("⏳ <i>ШІ аналізує матеріали курсу та генерує відповідь. Зачекайте кілька секунд...</i>")
        
        self.ml_thread = MLExplainThread(self.course_id, question, student_answer, correct_answer)
        self.ml_thread.finished_signal.connect(self.on_ai_finished)
        self.ml_thread.start()

    def on_ai_finished(self, explanation):
        self.ai_output.setText(f"🤖 <b>ШІ Асистент:</b>\n{explanation}")


class TaskSubmissionDialog(QDialog):
    def __init__(self, parent, student_id, task_data, existing_submission):
        super().__init__(parent)
        self.student_id = student_id
        self.task = task_data
        self.setWindowTitle(f"Завдання: {self.task['title']}")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Опис завдання:</b>"))
        
        desc_label = QLabel(self.task["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(desc_label)
        
        layout.addWidget(QLabel("<b>Ваша відповідь:</b>"))
        self.answer_input = QTextEdit()
        layout.addWidget(self.answer_input)
        
        self.submit_btn = QPushButton("Відправити на перевірку")
        self.submit_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.submit_btn.clicked.connect(self.submit_task)
        layout.addWidget(self.submit_btn)
        
        if existing_submission:
            self.answer_input.setText(existing_submission["answer_text"])
            if existing_submission["status"] == "Оцінено":
                self.answer_input.setReadOnly(True)
                self.submit_btn.hide()
                score_lbl = QLabel(f"<b><font color='green'>Роботу оцінено! Ваш бал: {existing_submission['score']}</font></b>")
                layout.addWidget(score_lbl)
            else:
                self.submit_btn.setText("Оновити відповідь")

    def submit_task(self):
        answer = self.answer_input.toPlainText().strip()
        if not answer:
            QMessageBox.warning(self, "Помилка", "Відповідь не може бути порожньою!")
            return
        database.submit_task(self.student_id, self.task["id"], answer)
        QMessageBox.information(self, "Успіх", "Вашу відповідь надіслано викладачу на перевірку!")
        self.accept()

class TestExecutionWindow(QDialog):
    def __init__(self, student_id, test_data):
        super().__init__()
        self.student_id = student_id
        self.test = test_data
        self.questions = test_data["questions"]
        self.current_q_index = 0
        self.correct_answers = 0
        self.detailed_results = []
        self.q_start_time = 0 

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
            for r in self.radios: r.setChecked(False)
            self.radio_group.setExclusive(True)

            if self.current_q_index == len(self.questions) - 1:
                self.next_btn.setText("Завершити тест")
                
            self.q_start_time = time.time()
        else:
            self.finish_test()

    def check_answer(self):
        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Увага", "Оберіть один із варіантів відповіді!")
            return

        time_spent = round(time.time() - self.q_start_time, 1)
        q_data = self.questions[self.current_q_index]
        correct_id = q_data["correct_index"]
        
        is_correct = (selected_id == correct_id)
        if is_correct:
            self.correct_answers += 1

        self.detailed_results.append({
            "question": q_data["question"],
            "correct_answer": q_data["options"][correct_id],
            "student_answer": q_data["options"][selected_id],
            "is_correct": is_correct,
            "time_spent_sec": time_spent
        })

        self.current_q_index += 1
        self.load_question()

    def finish_test(self):
        total = len(self.questions)
        score = core.calculate_score(self.correct_answers, total)
        passed = core.check_pass_status(score)

        database.save_detailed_test_result(self.student_id, self.test["id"], score, passed, self.detailed_results)

        status_text = "Складено успішно!" if passed else "Не складено. Спробуйте ще."
        QMessageBox.information(self, "Результат", f"Тест завершено!\nПравильних відповідей: {self.correct_answers} з {total}\nВаш бал: {score}%\nСтатус: {status_text}")
        self.accept()


class StudentDashboard(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle(f"HoDis - Панель Студента ({self.user['username']})")
        self.resize(850, 750)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<b>Каталог усіх курсів:</b>"))
        self.available_courses_list = QListWidget()
        self.layout.addWidget(self.available_courses_list)
        
        self.enroll_btn = QPushButton("Приєднатися до курсу")
        self.enroll_btn.clicked.connect(self.join_course)
        self.layout.addWidget(self.enroll_btn)
        
        self.layout.addWidget(QLabel("<hr>"))
        h_layout = QHBoxLayout()
        
        v_left = QVBoxLayout()
        v_left.addWidget(QLabel("<b>Мої курси:</b>"))
        self.my_courses_list = QListWidget()
        self.my_courses_list.itemSelectionChanged.connect(self.load_course_content) 
        v_left.addWidget(self.my_courses_list)
        h_layout.addLayout(v_left, 1)
        
        v_right = QVBoxLayout()
        v_right.addWidget(QLabel("<b>Навчальні матеріали:</b>"))
        self.materials_list = QListWidget()
        v_right.addWidget(self.materials_list)
        
        self.open_mat_btn = QPushButton("👁️ Відкрити матеріал")
        self.open_mat_btn.clicked.connect(self.open_material)
        v_right.addWidget(self.open_mat_btn)
        
        v_right.addWidget(QLabel("<hr><b>Автоматичні тести:</b>"))
        self.tests_list = QListWidget()
        v_right.addWidget(self.tests_list)
        
        self.start_test_btn = QPushButton("Пройти обраний тест")
        self.start_test_btn.clicked.connect(self.start_test)
        v_right.addWidget(self.start_test_btn)
        
        v_right.addWidget(QLabel("<hr><b>Відкриті практичні завдання:</b>"))
        self.tasks_list = QListWidget()
        v_right.addWidget(self.tasks_list)
        
        self.open_task_btn = QPushButton("Відкрити завдання")
        self.open_task_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px; font-weight: bold;")
        self.open_task_btn.clicked.connect(self.open_practical_task)
        v_right.addWidget(self.open_task_btn)
        
        v_right.addWidget(QLabel("<hr><b>Мої результати тестів:</b>"))
        self.results_list = QListWidget()
        v_right.addWidget(self.results_list)
        
        self.analyze_btn = QPushButton("🔍 Аналіз помилок (ШІ)")
        self.analyze_btn.setStyleSheet("background-color: #673AB7; color: white; padding: 8px; font-weight: bold;")
        self.analyze_btn.clicked.connect(self.open_ai_analysis)
        v_right.addWidget(self.analyze_btn)
        
        h_layout.addLayout(v_right, 2)
        self.layout.addLayout(h_layout)
        
        self.setLayout(self.layout)
        self.refresh_lists()

    def refresh_lists(self):
        self.available_courses_list.clear()
        self.my_courses_list.clear()
        self.tests_list.clear()
        self.materials_list.clear()
        self.tasks_list.clear()
        self.results_list.clear()
        
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
        selected = self.available_courses_list.currentItem()
        if not selected: return
        course_id = selected.data(32)
        db = database.load_db()
        db.setdefault("enrollments", []).append({"student_id": self.user["id"], "course_id": course_id})
        database.save_db(db)
        QMessageBox.information(self, "Успіх", "Ви приєдналися до курсу!")
        self.refresh_lists()

    def load_course_content(self):
        self.tests_list.clear()
        self.materials_list.clear()
        self.tasks_list.clear()
        self.results_list.clear()
        
        selected = self.my_courses_list.currentItem()
        if not selected: return
        course_id = selected.data(32)
        db = database.load_db()
        
        for course in db.get("courses", []):
            if course["id"] == course_id:
                for mat in course.get("materials", []):
                    item = QListWidgetItem(mat["name"])
                    item.setData(32, mat["path"]) 
                    self.materials_list.addItem(item)
                break
                
        test_dict = {}
        for test in db.get("tests", []):
            if test["course_id"] == course_id:
                test_dict[test["id"]] = test["title"]
                item = QListWidgetItem(f"{test['title']} (Питань: {len(test['questions'])})")
                item.setData(32, test['id'])
                self.tests_list.addItem(item)
                
        student_submissions = {s["task_id"]: s for s in db.get("task_submissions", []) if s["student_id"] == self.user["id"]}
        for task in db.get("practical_tasks", []):
            if task["course_id"] == course_id:
                status_text = "Не виконано"
                if task["id"] in student_submissions:
                    sub = student_submissions[task["id"]]
                    status_text = f"Оцінено: {sub['score']}" if sub["status"] == "Оцінено" else "На перевірці"
                    
                item = QListWidgetItem(f"[{status_text}] {task['title']}")
                item.setData(32, task)
                item.setData(33, student_submissions.get(task["id"]))
                self.tasks_list.addItem(item)
                
        for r in db.get("results", []):
            if r["student_id"] == self.user["id"] and r["test_id"] in test_dict:
                test_title = test_dict[r["test_id"]]
                status = "✅" if r["passed"] else "❌"
                item = QListWidgetItem(f"{status} {test_title} | Оцінка: {r['score']}%")
                item.setData(32, r)
                item.setData(33, test_title)
                item.setData(34, course_id)
                self.results_list.addItem(item)

    def open_material(self):
        selected = self.materials_list.currentItem()
        if not selected: return
        file_path = selected.data(32)
        if os.path.exists(file_path): QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))

    def start_test(self):
        selected = self.tests_list.currentItem()
        if not selected: return
        test_id = selected.data(32)
        db = database.load_db()
        test_data = next((t for t in db.get("tests", []) if t["id"] == test_id), None)
        if test_data:
            dialog = TestExecutionWindow(self.user["id"], test_data)
            dialog.exec_()
            self.load_course_content()

    def open_practical_task(self):
        selected = self.tasks_list.currentItem()
        if not selected: return
        task_data = selected.data(32)
        submission_data = selected.data(33)
        dialog = TaskSubmissionDialog(self, self.user["id"], task_data, submission_data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_course_content()

    def open_ai_analysis(self):
        selected = self.results_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Увага", "Оберіть результат тесту для аналізу!")
            return
            
        result_data = selected.data(32)
        test_title = selected.data(33)
        course_id = selected.data(34)
        
        dialog = StudentResultDetailsDialog(self, result_data, test_title, course_id)
        dialog.exec_()