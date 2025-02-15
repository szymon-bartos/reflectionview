import os
from PyQt5.QtWidgets import QListView, QFileSystemModel
from PyQt5.QtCore import QDir, QSortFilterProxyModel, Qt
from Utils.colors_handler import ColorHandler
from Utils.exif_handler import extract_camera_model, extract_lens_model

class BrowseWindow(QListView):
    def __init__(self, color_handler):
        super().__init__()
        self.color_handler = color_handler
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.setFilterCaseSensitivity(False)
        self.proxy_model.setSortCaseSensitivity(False)
        self.setModel(self.proxy_model)
        self.current_filter_color = None
        self.current_filter_exif = None
        self.current_exif_value = None
        self.current_sort_criteria = "name"

    def setRootPath(self, path):
        self.file_model.setRootPath(path)
        self.setRootIndex(self.proxy_model.mapFromSource(self.file_model.index(path)))

    def set_filter_color(self, color):
        self.current_filter_color = color
        self.invalidate_filter()

    def set_filter_exif(self, exif_type, value):
        self.current_filter_exif = exif_type
        self.current_exif_value = value
        self.invalidate_filter()

    def set_sort_criteria(self, criteria):
        self.current_sort_criteria = criteria
        self.sort_files()

    def sort_files(self):
        if self.current_sort_criteria == "name":
            self.proxy_model.sort(0, Qt.AscendingOrder)
        elif self.current_sort_criteria == "date":
            self.proxy_model.sort(3, Qt.AscendingOrder)
        elif self.current_sort_criteria == "type":
            self.proxy_model.sort(2, Qt.AscendingOrder)

    def invalidate_filter(self):
        self.proxy_model.setFilterKeyColumn(-1)  # Ustawia filtrowanie na wszystkie kolumny
        self.proxy_model.setFilterFixedString("")
        self.proxy_model.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.file_model.index(source_row, 0, source_parent)
        file_path = self.file_model.filePath(index)

        # Filtrowanie według koloru
        if self.current_filter_color:
            color = self.color_handler.get_color(file_path)
            if color != self.current_filter_color:
                return False

        # Filtrowanie według danych EXIF
        if self.current_filter_exif:
            exif_data = self.get_exif_data(file_path)
            if self.current_filter_exif == "camera" and exif_data.get('CameraModel') != self.current_exif_value:
                return False
            if self.current_filter_exif == "lens" and exif_data.get('LensModel') != self.current_exif_value:
                return False

        return True

    def get_exif_data(self, file_path):
        # Pseudo-funkcja, która zwraca dane EXIF (do zastąpienia przez prawdziwą analizę EXIF)
        camera_model = extract_camera_model(file_path)
        lens_model = extract_lens_model(file_path)
        return {"CameraModel": camera_model, "LensModel": lens_model}
