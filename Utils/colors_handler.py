import os
import json
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import QRect, Qt, QSortFilterProxyModel

class ColorHandler:
    def __init__(self):
        self.colors = {}

    def load_colors(self, directory):
        json_path = os.path.join(directory, "colors.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                self.colors = json.load(f)
        else:
            self.colors = {}

    def save_colors(self, directory):
        json_path = os.path.join(directory, "colors.json")
        with open(json_path, 'w') as f:
            json.dump(self.colors, f)

    def set_color(self, image_path, color):
        directory = os.path.dirname(image_path)
        file_name = os.path.basename(image_path)
        self.load_colors(directory)
        self.colors[file_name] = color
        self.save_colors(directory)

    def get_color(self, image_path):
        directory = os.path.dirname(image_path)
        file_name = os.path.basename(image_path)
        self.load_colors(directory)
        return self.colors.get(file_name, None)

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, color_handler, parent=None):
        super().__init__(parent)
        self.color_handler = color_handler

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if not index.isValid():
            return

        model = index.model()
        if isinstance(model, QSortFilterProxyModel):
            source_index = model.mapToSource(index)
            file_path = model.sourceModel().filePath(source_index)
        else:
            file_path = model.filePath(index)

        color = self.color_handler.get_color(file_path)
        if color:
            rect = QRect(option.rect.left() + 20, option.rect.top() + 2, 20, 20)
            painter.save()
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
            painter.restore()

class ColorSortProxyModel(QSortFilterProxyModel):
    def __init__(self, color_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color_handler = color_handler
        self.selected_color = None

    def set_color_filter(self, color):
        self.selected_color = color
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.selected_color:
            return True

        index = self.sourceModel().index(source_row, 0, source_parent)
        file_path = self.sourceModel().filePath(index)
        file_color = self.color_handler.get_color(file_path)

        # Wyświetl tylko pliki z wybranym kolorem
        return file_color == self.selected_color

    def lessThan(self, left, right):
        if not self.selected_color:
            return super().lessThan(left, right)

        left_path = self.sourceModel().filePath(left)
        right_path = self.sourceModel().filePath(right)

        left_color = self.color_handler.get_color(left_path)
        right_color = self.color_handler.get_color(right_path)

        # Pliki z wybranym kolorem idą na górę
        if left_color == self.selected_color and right_color != self.selected_color:
            return True
        if left_color != self.selected_color and right_color == self.selected_color:
            return False

        # W przeciwnym razie sortowanie alfabetyczne
        return super().lessThan(left, right)
