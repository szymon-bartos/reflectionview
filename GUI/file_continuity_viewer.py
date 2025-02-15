import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication, QTextEdit, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QScreen
from Utils.file_continuity_handler import FileContinuityChecker

class FileContinuityCheckerThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    result = pyqtSignal(str)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        def progress_callback(value):
            self.progress.emit(value)

        def status_callback(message):
            self.status.emit(message)

        checker = FileContinuityChecker(self.directory, progress_callback, status_callback)
        result = checker.check_continuity()
        self.result.emit(result)

class FileContinuityCheckerWindow(QDialog):
    def __init__(self, directory):
        super().__init__()
        self.setWindowTitle("Sprawdzanie ciągłości plików")
        self.setGeometry(100, 100, 600, 400)
        self.directory = directory

        self.initUI()
        self.start_checking()
        self.ensure_within_screen()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel(f"Sprawdzanie plików w katalogu: {self.directory}")
        layout.addWidget(self.info_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Rozpoczynanie sprawdzania ciągłości plików...")
        layout.addWidget(self.status_label)

        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.result_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.result_text)

    def start_checking(self):
        self.checker_thread = FileContinuityCheckerThread(self.directory)
        self.checker_thread.progress.connect(self.update_progress)
        self.checker_thread.status.connect(self.update_status)
        self.checker_thread.result.connect(self.display_result)
        self.checker_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def display_result(self, result):
        self.result_text.setPlainText(result)
        self.status_label.setText("Sprawdzanie zakończone")
        self.progress_bar.setValue(100)

    def ensure_within_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.geometry()

        if not screen_geometry.contains(window_geometry):
            if window_geometry.right() > screen_geometry.right():
                window_geometry.moveRight(screen_geometry.right())
            if window_geometry.bottom() > screen_geometry.bottom():
                window_geometry.moveBottom(screen_geometry.bottom())
            if window_geometry.left() < screen_geometry.left():
                window_geometry.moveLeft(screen_geometry.left())
            if window_geometry.top() < screen_geometry.top():
                window_geometry.moveTop(screen_geometry.top())

            self.setGeometry(window_geometry)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileContinuityCheckerWindow("D:/MAGISTERKA - TEST")
    window.show()
    sys.exit(app.exec_())
