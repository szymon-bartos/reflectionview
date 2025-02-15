from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QStyledItemDelegate
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, color_handler, parent=None):
        super().__init__(parent)
        self.color_handler = color_handler

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        file_path = index.model().filePath(index)
        color = self.color_handler.get_color(file_path)
        if color:
            painter.save()
            painter.setBrush(QColor(color))
            rect = option.rect
            rect.setWidth(10)
            painter.drawRect(rect)
            painter.restore()

class ColorViewer(QWidget):
    def __init__(self, color_handler, image_path):
        super().__init__()
        self.color_handler = color_handler
        self.image_path = image_path
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        colors = {"Red": "red", "Green": "green", "Blue": "blue", "Yellow": "yellow", "Purple": "purple"}
        for color_name, color_code in colors.items():
            button = QPushButton()
            button.setStyleSheet(f"background-color: {color_code}")
            button.setFixedSize(20, 20)
            button.clicked.connect(lambda _, c=color_code: self.set_color(c))
            layout.addWidget(button)
        self.setLayout(layout)

    def set_color(self, color):
        self.color_handler.set_color(self.image_path, color)
