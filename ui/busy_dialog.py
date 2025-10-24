from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class BusyDialog(QDialog):
    def __init__(self, message: str = "Procesando...", on_cancel=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Por favor, espera")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(380, 150)
        layout = QVBoxLayout()
        self.msg_label = QLabel(message)
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.msg_label)
        self.cancel_btn = QPushButton("Cancelar")
        if on_cancel:
            self.cancel_btn.clicked.connect(on_cancel)
        self.cancel_btn.clicked.connect(self.reject)  # close the dialog
        layout.addWidget(self.cancel_btn)
        self.setLayout(layout)

    def update_message(self, message: str):
        self.msg_label.setText(message)
