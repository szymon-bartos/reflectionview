from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

class ExifViewer(QDialog):
    def __init__(self, exif_data):
        super().__init__()
        self.setWindowTitle('EXIF Data')
        self.setGeometry(200, 200, 600, 400)
        self.initUI(exif_data)

    def initUI(self, exif_data):
        layout = QVBoxLayout()

        # Tworzenie tabeli
        table = QTableWidget()
        table.setRowCount(len(exif_data))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Tag', 'Value'])
        table.verticalHeader().setDefaultSectionSize(20)  # Ustawienie mniejszych odstępów między wierszami

        # Wypełnianie tabeli danymi EXIF
        for row, (key, value) in enumerate(exif_data.items()):
            table.setItem(row, 0, QTableWidgetItem(key))
            table.setItem(row, 1, QTableWidgetItem(value))

        # Ustawienie minimalnej szerokości kolumny na 15 znaków
        font_metrics = table.fontMetrics()
        min_width = font_metrics.horizontalAdvance('M' * 15)
        table.setColumnWidth(0, min_width)
        table.setColumnWidth(1, min_width)

        layout.addWidget(table)
        self.setLayout(layout)

def create_exif_table(exif_data):
    """
    Tworzy tabelę QTableWidget z danymi EXIF.

    :param exif_data: Słownik z danymi EXIF.
    :return: QTableWidget z danymi EXIF.
    """
    table = QTableWidget()
    table.setRowCount(len(exif_data))
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(['Tag', 'Value'])
    table.verticalHeader().setDefaultSectionSize(20)  # Ustawienie mniejszych odstępów między wierszami

    # Wypełnianie tabeli danymi EXIF
    for row, (key, value) in enumerate(exif_data.items()):
        table.setItem(row, 0, QTableWidgetItem(key))
        table.setItem(row, 1, QTableWidgetItem(value))

    # Ustawienie minimalnej szerokości kolumny na 15 znaków
    font_metrics = table.fontMetrics()
    min_width = font_metrics.horizontalAdvance('M' * 15)
    table.setColumnWidth(0, min_width)
    table.setColumnWidth(1, min_width)

    return table
