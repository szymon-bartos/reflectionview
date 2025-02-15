import os
import sys
import traceback
import json
from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, \
    QComboBox, QAction, QDockWidget, QTableWidget, QTableWidgetItem, QApplication
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt, QRectF
from PIL import Image
from Utils.image_handler import rotate_image, resize_image, get_image_with_orientation
from Utils.exif_handler import get_exif_data
from Utils.colors_handler import ColorHandler
from GUI.exif_viewer import create_exif_table


class ImageViewer(QMainWindow):
    def __init__(self, image_path, color_handler):
        super().__init__()
        self.setWindowTitle('Image Viewer')
        self.setGeometry(100, 100, 800, 600)
        self.image_path = image_path
        self.image_folder = os.path.dirname(image_path)
        self.image_files = self.get_image_files()
        self.current_index = self.image_files.index(os.path.basename(image_path))
        self.scale_factor = 1.0
        self.current_image = None
        self.show_exif = False
        self.color_handler = color_handler
        self.color_buttons = {}

        self.initUI()
        self.showMaximized()
        self.load_image()

    def get_image_files(self):
        supported_extensions = (
        '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.arw', '.nef', '.cr2', '.dng', '.raw')
        return [f for f in os.listdir(self.image_folder) if f.lower().endswith(supported_extensions)]

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        button_layout = QHBoxLayout()

        prev_button = QPushButton('<')
        prev_button.clicked.connect(self.show_prev_image)
        button_layout.addWidget(prev_button)

        next_button = QPushButton('>')
        next_button.clicked.connect(self.show_next_image)
        button_layout.addWidget(next_button)

        rotate_button = QPushButton('Rotate')
        rotate_button.clicked.connect(self.rotate_image)
        button_layout.addWidget(rotate_button)

        resize_button = QPushButton('Resize')
        resize_button.clicked.connect(self.resize_image)
        button_layout.addWidget(resize_button)

        exif_button = QPushButton('Show EXIF Data')
        exif_button.clicked.connect(self.toggle_exif_data)
        button_layout.addWidget(exif_button)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "100%", "150%", "200%", "Fit to Screen"])
        self.zoom_combo.currentIndexChanged.connect(self.zoom_image)
        button_layout.addWidget(self.zoom_combo)

        # Dodanie kolorowych przycisków
        colors = ["red", "green", "blue", "yellow", "purple"]
        self.color_buttons = {}
        for color in colors:
            btn = QPushButton()
            btn.setStyleSheet(f"background-color: {color}; width: 30px; height: 30px;")
            btn.clicked.connect(lambda _, c=color: self.tag_color(c))
            button_layout.addWidget(btn)
            self.color_buttons[color] = btn

        layout.addLayout(button_layout)

        fullscreen_action = QAction("Toggle Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_action)

        self.exif_dock = QDockWidget("EXIF Data", self)
        self.exif_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.exif_table = QTableWidget()
        self.exif_dock.setWidget(self.exif_table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.exif_dock)
        self.exif_dock.setMinimumWidth(600)  # Ustawienie minimalnej szerokości okna dokowalnego
        self.exif_dock.hide()

    def load_image(self):
        try:
            self.current_image = get_image_with_orientation(self.image_path)
            if self.current_image:
                if self.current_image.mode != 'RGBA':
                    self.current_image = self.current_image.convert('RGBA')
                data = self.current_image.tobytes("raw", "RGBA")
                q_image = QImage(data, self.current_image.width, self.current_image.height, QImage.Format_RGBA8888)
                self.display_image(q_image)
            else:
                self.scene.clear()
                self.scene.addText("Unable to load image")

            if self.show_exif:
                self.show_exif_data()

            self.update_color_buttons()
        except Exception as e:
            print(f"Error loading image: {e}")
            traceback.print_exc()

    def display_image(self, q_image):
        try:
            pixmap = QPixmap.fromImage(q_image)
            self.scene.clear()
            self.scene.addPixmap(pixmap)

            self.view.resetTransform()
            self.view.setSceneRect(QRectF(pixmap.rect()))

            screen_size = self.view.viewport().size()
            screen_width = screen_size.width()
            screen_height = screen_size.height()
            image_width = q_image.width()
            image_height = q_image.height()

            if image_width > screen_width or image_height > screen_height:
                self.scale_factor = min(screen_width / image_width, screen_height / image_height)
            else:
                self.scale_factor = 1.0

            if self.scale_factor != 1.0:
                self.view.scale(self.scale_factor, self.scale_factor)

            self.view.centerOn(self.scene.itemsBoundingRect().center())
        except Exception as e:
            print(f"Error in display_image: {e}")
            traceback.print.exc()

    def rotate_image(self):
        try:
            if self.current_image:
                self.current_image = rotate_image(self.current_image, 90)
                data = self.current_image.tobytes("raw", "RGBA")
                q_image = QImage(data, self.current_image.width, self.current_image.height, QImage.Format_RGBA8888)
                self.display_image(q_image)
        except Exception as e:
            print(f"Error rotating image: {e}")
            traceback.print.exc()

    def resize_image(self):
        try:
            resize_image(self.image_path, (800, 600))
            self.load_image()
        except Exception as e:
            print(f"Error resizing image: {e}")
            traceback.print.exc()

    def show_exif_data(self):
        try:
            self.exif_table.clear()
            exif_data = get_exif_data(self.image_path)
            if exif_data:
                self.exif_table.setRowCount(len(exif_data))
                self.exif_table.setColumnCount(2)
                self.exif_table.setHorizontalHeaderLabels(['Tag', 'Value'])
                for row, (key, value) in enumerate(exif_data.items()):
                    self.exif_table.setItem(row, 0, QTableWidgetItem(key))
                    self.exif_table.setItem(row, 1, QTableWidgetItem(value))
            else:
                self.exif_table.setRowCount(0)
                self.exif_table.setColumnCount(1)
                self.exif_table.setHorizontalHeaderLabels(['Message'])
                self.exif_table.setItem(0, 0, QTableWidgetItem("No EXIF data found for this image."))
            self.exif_dock.show()
        except Exception as e:
            print(f"Error showing EXIF data: {e}")
            traceback.print.exc()

    def toggle_exif_data(self):
        self.show_exif = not self.show_exif
        if self.show_exif:
            self.show_exif_data()
        else:
            self.exif_dock.hide()

    def show_prev_image(self):
        try:
            if self.current_index > 0:
                self.current_index -= 1
                self.image_path = os.path.join(self.image_folder, self.image_files[self.current_index])
                self.load_image()
        except Exception as e:
            print(f"Error showing previous image: {e}")
            traceback.print_exc()

    def show_next_image(self):
        try:
            if self.current_index < len(self.image_files) - 1:
                self.current_index += 1
                self.image_path = os.path.join(self.image_folder, self.image_files[self.current_index])
                self.load_image()
        except Exception as e:
            print(f"Error showing next image: {e}")
            traceback.print_exc()

    def zoom_image(self, index):
        try:
            zoom_levels = {
                0: 0.5,
                1: 1.0,
                2: 1.5,
                3: 2.0,
                4: "fit"
            }
            zoom = zoom_levels[index]
            self.view.resetTransform()
            if zoom == "fit":
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            else:
                self.view.scale(zoom, zoom)
        except Exception as e:
            print(f"Error in zoom_image: {e}")
            traceback.print.exc()

    def toggle_fullscreen(self):
        try:
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
        except Exception as e:
            print(f"Error toggling fullscreen: {e}")
            traceback.print.exc()

    def tag_color(self, color):
        self.color_handler.set_color(self.image_path, color)
        self.update_color_buttons()

    def update_color_buttons(self):
        # Reset all button styles
        for btn in self.color_buttons.values():
            btn.setStyleSheet(f"background-color: {btn.styleSheet().split(':')[1].strip()}; width: 30px; height: 30px;")

        # Highlight the button of the current image's color
        color = self.color_handler.get_color(self.image_path)
        if color in self.color_buttons:
            self.color_buttons[color].setStyleSheet(
                f"background-color: {color}; border: 3px solid black; width: 30px; height: 30px;")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.show_next_image()
        elif event.key() == Qt.Key_Left:
            self.show_prev_image()
        elif event.key() == Qt.Key_Up:
            self.zoom_image(1)  # 100%
        elif event.key() == Qt.Key_Down:
            self.zoom_image(4)  # Fit to Screen
        elif event.key() == Qt.Key_Z:
            self.tag_color("red")
        elif event.key() == Qt.Key_X:
            self.tag_color("green")
        elif event.key() == Qt.Key_C:
            self.tag_color("blue")
        elif event.key() == Qt.Key_V:
            self.tag_color("yellow")
        elif event.key() == Qt.Key_B:
            self.tag_color("purple")
        elif event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_P:
            self.toggle_exif_data()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        color_handler = ColorHandler('D:/MAGISTERKA - TEST')  # Ustawienie folderu z plikami
        viewer = ImageViewer('D:/MAGISTERKA - TEST/DSC05057.ARW', color_handler)
        viewer.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
