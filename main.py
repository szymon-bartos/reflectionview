import sys
from PyQt5.QtWidgets import QApplication
from GUI.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()