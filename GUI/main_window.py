import sys
import os
import shutil
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QFileSystemModel, QVBoxLayout, QWidget, QLabel, \
    QSplitter, QListView, QHBoxLayout, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import Qt, QDir, QSortFilterProxyModel
from GUI.image_viewer import ImageViewer
from GUI.file_continuity_viewer import FileContinuityCheckerWindow
from GUI.blur_viewer import BlurInspectorWindow
from Utils.colors_handler import ColorHandler, ColorDelegate


class ColorSortProxyModel(QSortFilterProxyModel):
    def __init__(self, color_handler, *args, **kwargs):
        super(ColorSortProxyModel, self).__init__(*args, **kwargs)
        self.color_handler = color_handler
        self.color_filter = None

    def set_color_filter(self, color):
        self.color_filter = color
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.color_filter:
            return True

        index = self.sourceModel().index(source_row, 0, source_parent)
        file_path = self.sourceModel().filePath(index)
        file_color = self.color_handler.get_color(file_path)

        if file_color == self.color_filter:
            return True

        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ReflectionView 1.0.5')
        self.setGeometry(100, 100, 800, 600)

        self.history = []  # Lista przechowująca historię odwiedzanych folderów
        self.current_index = -1  # Indeks bieżącej pozycji w historii

        self.color_handler = ColorHandler()
        self.clipboard = []  # Lista przechowująca pliki do skopiowania lub wycięcia
        self.cut_mode = False  # Tryb oznaczający, czy pliki są wycinane (True) czy kopiowane (False)
        self.initUI()

    def initUI(self):
        # Tworzenie głównego widgetu
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Dodanie przycisków nawigacyjnych
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Cofnij")
        self.back_button.clicked.connect(self.go_back)
        nav_layout.addWidget(self.back_button)

        self.forward_button = QPushButton("Naprzód")
        self.forward_button.clicked.connect(self.go_forward)
        nav_layout.addWidget(self.forward_button)

        # Dodanie przycisku sprawdzającego ciągłość plików
        check_button = QPushButton("Sprawdź ciągłość plików")
        check_button.clicked.connect(self.check_files_continuity)
        nav_layout.addWidget(check_button)

        # Dodanie przycisku uruchamiającego "blur inspector'a"
        blur_button = QPushButton("Blur inspector")
        blur_button.clicked.connect(self.open_blur_inspector)
        nav_layout.addWidget(blur_button)

        # Dodanie przycisków kopiowania, wycinania, wklejania i usuwania
        copy_button = QPushButton("Kopiuj")
        copy_button.clicked.connect(self.copy_files)
        nav_layout.addWidget(copy_button)

        cut_button = QPushButton("Wytnij")
        cut_button.clicked.connect(self.cut_files)
        nav_layout.addWidget(cut_button)

        paste_button = QPushButton("Wklej")
        paste_button.clicked.connect(self.paste_files)
        nav_layout.addWidget(paste_button)

        delete_button = QPushButton("Usuń")
        delete_button.clicked.connect(self.delete_files)
        nav_layout.addWidget(delete_button)

        # Dodanie rozwijanej listy sortowania
        self.sort_combobox = QComboBox()
        self.sort_combobox.addItems([
            "Sortuj według nazwy (A-Z)",
            "Sortuj według nazwy (Z-A)",
            "Sortuj według typu (A-Z)",
            "Sortuj według typu (Z-A)",
            "Sortuj według daty (od najnowszego)",
            "Sortuj według daty (od najstarszego)"
        ])
        self.sort_combobox.currentIndexChanged.connect(self.change_sorting)
        nav_layout.addWidget(self.sort_combobox)

        # Dodanie rozwijanej listy sortowania po kolorze
        self.color_combobox = QComboBox()
        self.color_combobox.addItem("Sortuj według koloru")
        self.color_combobox.setEnabled(False)  # Domyślnie wyłączona
        self.color_combobox.currentIndexChanged.connect(self.sort_by_selected_color)
        nav_layout.addWidget(self.color_combobox)

        main_layout.addLayout(nav_layout)

        # Tworzenie rozdzielacza
        splitter = QSplitter(Qt.Horizontal)

        # Tworzenie drzewa katalogów
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)  # Filtruj tylko katalogi
        self.model.setRootPath("")  # Ustaw root na pustą ścieżkę, aby wyświetlać wszystkie dyski
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))  # Ustaw root index na pustą ścieżkę
        self.tree.clicked.connect(self.on_tree_clicked)

        # Tworzenie listy plików
        self.file_list = QListView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        # Użycie ColorSortProxyModel zamiast QFileSystemModel
        self.proxy_model = ColorSortProxyModel(self.color_handler, self)
        self.proxy_model.setSourceModel(self.file_model)

        self.file_list.setModel(self.proxy_model)
        self.file_list.setItemDelegate(ColorDelegate(self.color_handler, self.file_list))
        self.file_list.setSelectionMode(QListView.ExtendedSelection)  # Pozwala na zaznaczanie wielu plików
        self.file_list.clicked.connect(self.on_file_clicked)
        self.file_list.doubleClicked.connect(self.on_file_double_clicked)

        # Tworzenie obszaru szczegółów
        self.detail_label = QLabel("Wybierz plik, aby zobaczyć szczegóły")
        self.detail_label.setAlignment(Qt.AlignTop)
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self.detail_label)
        detail_widget = QWidget()
        detail_widget.setLayout(detail_layout)

        # Dodanie widżetów do rozdzielacza
        splitter.addWidget(self.tree)
        splitter.addWidget(self.file_list)
        splitter.addWidget(detail_widget)

        main_layout.addWidget(splitter)
        splitter.setSizes([200, 600, 400])

        # Aktualizacja stanu przycisków nawigacyjnych
        self.update_nav_buttons()

    def on_tree_clicked(self, index):
        # Pobierz pełną ścieżkę wybranego katalogu
        path = self.model.filePath(index)
        self.update_history(path)  # Aktualizuj historię nawigacji
        self.update_tree_and_list(path)  # Zaktualizuj drzewo i listę plików
        self.update_sort_by_color_combobox(path)  # Ustaw rozwijaną listę sortowania po kolorze

    def on_file_clicked(self, index):
        # Pobierz pełną ścieżkę wybranego pliku
        source_index = self.proxy_model.mapToSource(index)
        file_info = self.file_model.fileInfo(source_index)
        details = (
            f"Nazwa: {file_info.fileName()}\n"
            f"Typ: {file_info.suffix()}\n"
            f"Rozmiar: {file_info.size()} bajtów\n"
            f"Data utworzenia: {file_info.created().toString(Qt.DefaultLocaleLongDate)}\n"
            f"Data modyfikacji: {file_info.lastModified().toString(Qt.DefaultLocaleLongDate)}"
        )
        self.detail_label.setText(details)

    def on_file_double_clicked(self, index):
        # Pobierz pełną ścieżkę wybranego pliku lub folderu
        source_index = self.proxy_model.mapToSource(index)
        path = self.file_model.filePath(source_index)
        if self.file_model.isDir(source_index):
            # Jeśli to folder, wejdź do niego
            self.update_history(path)  # Aktualizuj historię nawigacji
            self.update_tree_and_list(path)  # Zaktualizuj drzewo i listę plików
            self.update_sort_by_color_combobox(path)  # Ustaw rozwijaną listę sortowania po kolorze
        else:
            # Jeśli to plik graficzny, otwórz go
            supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.raw', '.nef', '.cr2', '.arw', '.dng', '.tiff']
            if any(path.lower().endswith(ext) for ext in supported_extensions):
                try:
                    self.image_viewer = ImageViewer(path, self.color_handler)
                    self.image_viewer.show()
                except Exception as e:
                    self.detail_label.setText(f"Error: {str(e)}")

    def update_tree_and_list(self, path):
        # Aktualizuj root dla listy plików
        self.file_list.setRootIndex(self.proxy_model.mapFromSource(self.file_model.setRootPath(path)))
        # Aktualizuj root dla drzewa katalogów i rozwiń ścieżkę
        index = self.model.index(path)
        self.tree.setCurrentIndex(index)
        self.tree.scrollTo(index, QTreeView.PositionAtCenter)
        self.tree.expand(index)  # Rozwiń bieżący katalog
        while index.parent().isValid():
            index = index.parent()
            self.tree.expand(index)  # Rozwiń wyższe poziomy
            self.tree.setExpanded(index, True)  # Upewnij się, że wszystkie wyższe poziomy są rozwinięte

    def update_history(self, path):
        # Aktualizuj historię nawigacji
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        self.history.append(path)
        self.current_index += 1
        self.update_nav_buttons()

    def go_back(self):
        # Idź wstecz w historii
        if self.current_index > 0:
            self.current_index -= 1
            path = self.history[self.current_index]
            self.update_tree_and_list(path)  # Zaktualizuj drzewo i listę plików
            self.update_nav_buttons()

    def go_forward(self):
        # Idź do przodu w historii
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            path = self.history[self.current_index]
            self.update_tree_and_list(path)  # Zaktualizuj drzewo i listę plików
            self.update_nav_buttons()

    def update_nav_buttons(self):
        # Aktualizuj stan przycisków nawigacyjnych
        self.back_button.setEnabled(self.current_index > 0)
        self.forward_button.setEnabled(self.current_index < len(self.history) - 1)

    def check_files_continuity(self):
        current_directory = self.model.filePath(self.tree.currentIndex())
        continuity_checker_window = FileContinuityCheckerWindow(current_directory)
        continuity_checker_window.exec_()

    def open_blur_inspector(self):
        current_directory = self.model.filePath(self.tree.currentIndex())
        blur_inspector_window = BlurInspectorWindow(current_directory, self.color_handler)
        blur_inspector_window.exec_()

    def update_sort_by_color_combobox(self, directory):
        # Sprawdź, czy plik colors.json istnieje w bieżącym katalogu
        colors_json_path = os.path.join(directory, "colors.json")
        if os.path.exists(colors_json_path):
            with open(colors_json_path, 'r') as f:
                colors = json.load(f)
            unique_colors = set(colors.values())
            self.color_combobox.clear()
            self.color_combobox.addItem("Sortuj według koloru")
            self.color_combobox.addItems(sorted(unique_colors))
            self.color_combobox.setEnabled(True)
        else:
            self.color_combobox.setEnabled(False)

    def change_sorting(self, index):
        # Zmiana sortowania, gdy użytkownik wybierze inną opcję
        if index == 0:  # Sortuj według nazwy (A-Z)
            self.proxy_model.sort(0, Qt.AscendingOrder)
        elif index == 1:  # Sortuj według nazwy (Z-A)
            self.proxy_model.sort(0, Qt.DescendingOrder)
        elif index == 2:  # Sortuj według typu (A-Z)
            self.proxy_model.sort(2, Qt.AscendingOrder)
        elif index == 3:  # Sortuj według typu (Z-A)
            self.proxy_model.sort(2, Qt.DescendingOrder)
        elif index == 4:  # Sortuj według daty (od najnowszego)
            self.proxy_model.sort(3, Qt.DescendingOrder)
        elif index == 5:  # Sortuj według daty (od najstarszego)
            self.proxy_model.sort(3, Qt.AscendingOrder)

    def sort_by_selected_color(self, index):
        if index == 0:
            self.proxy_model.set_color_filter(None)
        else:
            selected_color = self.color_combobox.currentText()
            self.proxy_model.set_color_filter(selected_color)

    def copy_files(self):
        # Skopiuj zaznaczone pliki
        selected_indexes = self.file_list.selectedIndexes()
        self.clipboard = [self.file_model.filePath(self.proxy_model.mapToSource(index)) for index in selected_indexes]
        self.cut_mode = False

    def cut_files(self):
        # Wytnij zaznaczone pliki
        selected_indexes = self.file_list.selectedIndexes()
        self.clipboard = [self.file_model.filePath(self.proxy_model.mapToSource(index)) for index in selected_indexes]
        self.cut_mode = True

    def paste_files(self):
        # Wklej pliki z schowka
        if not self.clipboard:
            return

        target_directory = self.model.filePath(self.tree.currentIndex())
        for file_path in self.clipboard:
            if os.path.exists(file_path):
                target_path = os.path.join(target_directory, os.path.basename(file_path))
                try:
                    if self.cut_mode:
                        shutil.move(file_path, target_path)
                    else:
                        if os.path.isdir(file_path):
                            shutil.copytree(file_path, target_path)
                        else:
                            shutil.copy2(file_path, target_path)
                except Exception as e:
                    QMessageBox.warning(self, "Błąd", f"Nie można wykonać operacji: {str(e)}")

        if self.cut_mode:
            self.clipboard = []  # Wyczyść schowek po wycięciu

        self.update_tree_and_list(target_directory)  # Odśwież widok

    def delete_files(self):
        # Usuń zaznaczone pliki
        selected_indexes = self.file_list.selectedIndexes()
        selected_files = [self.file_model.filePath(self.proxy_model.mapToSource(index)) for index in selected_indexes]

        reply = QMessageBox.question(self, 'Usuń pliki',
                                     f"Czy na pewno chcesz usunąć {len(selected_files)} plik(ów)?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for file_path in selected_files:
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                except Exception as e:
                    QMessageBox.warning(self, "Błąd", f"Nie można usunąć pliku: {str(e)}")

            self.update_tree_and_list(self.model.filePath(self.tree.currentIndex()))  # Odśwież widok


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
