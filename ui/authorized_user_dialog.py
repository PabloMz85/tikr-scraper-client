from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt


class AuthorizedUserDialog(QDialog):
    def __init__(self, current_value: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar usuario autorizado")
        self.resize(360, 160)

        layout = QVBoxLayout()

        label = QLabel("Ingrese el usuario autorizado por Invertir desde Cero:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Número de usuario autorizado, p. ej. 00001")
        if current_value:
            self.input.setText(current_value)
        layout.addWidget(self.input)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Guardar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)
        self.setLayout(layout)

    def _on_ok(self):
        value = self.input.text().strip()
        if not value:
            QMessageBox.warning(self, "Faltan datos", "Por favor introduce el número de usuario autorizado.")
            return
        if not value.isdigit():
            QMessageBox.warning(self, "Número inválido", "El número de usuario debe ser numérico.")
            return
        self.accept()

    def get_user_number(self) -> str:
        return self.input.text().strip()
