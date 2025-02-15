import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox, QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from Utils.blur import BlurInspector
from Utils.colors_handler import ColorHandler


class BlurInspectorThread(QThread):
    progress = pyqtSignal(int)
    update_label = pyqtSignal(str)  # Sygnał do aktualizacji wyświetlanej nazwy zdjęcia
    finished = pyqtSignal(list)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        inspector = BlurInspector(self.directory)
        image_files = [
            f for f in os.listdir(self.directory)
            if os.path.isfile(os.path.join(self.directory, f)) and
               f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.arw', '.nef', '.cr2', '.dng', '.raw'))
        ]

        total_files = len(image_files)
        for i, file_name in enumerate(image_files):
            file_path = os.path.join(self.directory, file_name)
            self.update_label.emit(file_name)
            is_blurred = inspector.is_blurred(file_path)
            if is_blurred:
                inspector.blurred_images.append(file_name)
            progress_value = int(((i + 1) / total_files) * 100)
            self.progress.emit(progress_value)

        self.finished.emit(inspector.blurred_images)


class BlurInspectorWindow(QDialog):
    def __init__(self, directory, color_handler):
        super().__init__()
        self.setWindowTitle("Blur Inspector")
        self.setGeometry(100, 100, 400, 200)
        self.directory = directory
        self.color_handler = color_handler
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.label = QLabel(f"Analizowanie zdjęć w katalogu: {self.directory}")
        layout.addWidget(self.label)

        self.current_image_label = QLabel("Aktualnie analizowane zdjęcie: ")  # Label dla aktualnego zdjęcia
        layout.addWidget(self.current_image_label)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.thread = BlurInspectorThread(self.directory)
        self.thread.progress.connect(self.update_progress)
        self.thread.update_label.connect(self.update_image_label)  # Połącz sygnał z funkcją aktualizującą nazwę zdjęcia
        self.thread.finished.connect(self.analysis_finished)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_image_label(self, image_name):
        self.current_image_label.setText(f"Aktualnie analizowane zdjęcie: {image_name}")

    def analysis_finished(self, blurred_images):
        self.progress_bar.setValue(100)
        if blurred_images:
            blurred_list = "\n".join(blurred_images)
            msg = f"Znaleziono nieostre zdjęcia:\n{blurred_list}\n\nCzy chcesz je oznaczyć kolorem?"
            choice = QMessageBox.question(self, 'Oznaczenie kolorami', msg, QMessageBox.Yes | QMessageBox.No)

            if choice == QMessageBox.Yes:
                color_choice = self.choose_color()
                if color_choice:
                    for image in blurred_images:
                        self.color_handler.set_color(os.path.join(self.directory, image), color_choice)
        else:
            QMessageBox.information(self, "Wynik", "Nie znaleziono nieostrych zdjęć.")

        self.close()

    def choose_color(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Wybierz kolor")
        dialog.setGeometry(100, 100, 200, 100)

        layout = QVBoxLayout(dialog)
        combo = QComboBox(dialog)
        combo.addItems(["red", "green", "blue", "yellow", "purple"])
        layout.addWidget(combo)

        button = QPushButton("OK", dialog)
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)

        dialog.exec_()
        return combo.currentText()
