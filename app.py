import sys
from PyQt6.QtWidgets import QApplication
from ui import ExcelDownloader


def main():
    app = QApplication(sys.argv)
    window = ExcelDownloader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
