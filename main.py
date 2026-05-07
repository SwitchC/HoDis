import sys
from PyQt5.QtWidgets import QApplication
import database
from auth_ui import LoginWindow
from teacher_ui import TeacherDashboard
from student_ui import StudentDashboard

class HoDisApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        database.init_db()
        
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.show_dashboard)
        
        self.current_window = self.login_window 

    def show_dashboard(self, user_data):
        print(f"Успішний вхід: {user_data['username']}, Роль: {user_data['role']}")
        
        if user_data["role"] == "teacher":
            self.current_window = TeacherDashboard(user_data)
        elif user_data["role"] == "student":
            self.current_window = StudentDashboard(user_data)
            
        self.current_window.show()

    def run(self):
        self.current_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = HoDisApp()
    app.run()