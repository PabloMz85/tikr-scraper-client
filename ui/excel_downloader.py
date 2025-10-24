import os
import json
import keyring

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QSizePolicy,
)

from .busy_dialog import BusyDialog
from .token_worker import TokenWorker
from .validate_token_worker import ValidateTokenWorker
from .download_worker import DownloadWorker
from .authorized_user_dialog import AuthorizedUserDialog


class ExcelDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.token = ""
        self.token_file = os.path.join(os.path.dirname(__file__), "..", "token.json")
        self.token_file = os.path.normpath(self.token_file)
        self.cancel_requested = False
        self.busy_dialog = None
        self.worker = None
        self.stored_email = ""
        self.stored_password = ""
        self.authorized_user_number = ""
        self.init_ui()
        self.load_existing_token()

    def init_ui(self):
        self.setWindowTitle("Cliente de Exportación TIKR")
        self.resize(480, 380)

        # Basic styling
        self.setStyleSheet("""
            QWidget {
                font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                font-size: 13px;
                color: #222;
            }
            QLabel.title {
                font-size: 18px;
                font-weight: 600;
                padding: 8px 0 2px 0;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #DDD;
                border-radius: 8px;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                background-color: #F7F7F7;
                border-radius: 4px;
            }
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #CCC;
                border-radius: 6px;
            }
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #1f6feb;
                background-color: #2f81f7;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1f6feb;
            }
            QPushButton:disabled {
                background-color: #A9A9A9;
                border-color: #A9A9A9;
            }
            QLabel.status-ok {
                color: #2E7D32;
                font-weight: 600;
            }
            QLabel.status-error {
                color: #C62828;
                font-weight: 600;
            }
        """)

        root = QVBoxLayout()
        root.setSpacing(12)

        # Header
        header = QLabel("Cliente de Exportación TIKR")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setProperty("class", "title")
        header.setObjectName("title")
        header.setStyleSheet("QLabel#title { font-size: 22px; font-weight: 700; }")
        root.addWidget(header)

        # Account group
        account_group = QGroupBox("Cuenta")
        account_layout = QVBoxLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("tu@ejemplo.com")
        self.input_email.setClearButtonEnabled(True)
        self.input_email.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Introduce tu contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setClearButtonEnabled(True)
        self.input_password.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form.addRow("Correo electrónico", self.input_email)
        form.addRow("Contraseña", self.input_password)

        account_layout.addLayout(form)
        self.chk_remember = QCheckBox("Recordar credenciales")
        self.chk_remember.setToolTip("Almacena tus credenciales de forma segura en el llavero del sistema para futuros inicios de sesión.")
        account_layout.addWidget(self.chk_remember)

        # add credentials hint
        hint = QLabel(f"🔐 Las credenciales solo se utilizan para loguearse en TIKR y obtener el token,\nlas credenciales nunca serán enviadas al servidor y solo serán almacenadas de forma local.")
        hint.setAlignment(Qt.AlignmentFlag.AlignLeft)
        hint.setStyleSheet("color: #555;")
        account_layout.addWidget(hint)

        actions_row = QHBoxLayout()
        self.btn_generate_token = QPushButton("Generar token de acceso")
        self.btn_generate_token.clicked.connect(self.handle_generate_token)

        self.lbl_token_status = QLabel("Sin token generado")
        self.lbl_token_status.setAlignment(Qt.AlignmentFlag.AlignLeft)

        actions_row.addWidget(self.btn_generate_token)
        actions_row.addWidget(self.lbl_token_status, stretch=1)

        account_layout.addLayout(actions_row)

        # add authorized user number configuration
        user_row = QHBoxLayout()
        self.btn_configure_user = QPushButton("Configurar usuario autorizado")
        self.btn_configure_user.clicked.connect(self.open_authorized_user_dialog)

        self.user_label = QLabel("Usuario autorizado: no configurado")
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        user_row.addWidget(self.btn_configure_user)
        user_row.addWidget(self.user_label, stretch=1)

        account_layout.addLayout(user_row)

        account_group.setLayout(account_layout)
        root.addWidget(account_group)

        # Export group
        export_group = QGroupBox("Exportar")
        export_layout = QVBoxLayout()

        self.label = QLabel("Usa tu token para descargar el archivo Excel:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        export_layout.addWidget(self.label)

        self.input_asset = QLineEdit()
        self.input_asset.setPlaceholderText("Activo (ticker o nombre de la empresa), p. ej. AAPL")
        self.input_asset.setClearButtonEnabled(True)
        self.input_asset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        export_layout.addWidget(self.input_asset)

        self.button = QPushButton("Descargar Excel")
        self.button.clicked.connect(self.download_excel)
        export_layout.addWidget(self.button)
        # Separate status label to show download result without overwriting hints
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        export_layout.addWidget(self.status_label)

        export_group.setLayout(export_layout)
        root.addWidget(export_group)

        self.setLayout(root)

    def open_authorized_user_dialog(self):
        # Open dialog to configure authorized user number
        current_value = (self.authorized_user_number or "").strip()
        dlg = AuthorizedUserDialog(current_value=current_value, parent=self)
        if dlg.exec():
            new_value = dlg.get_user_number()
            self.authorized_user_number = new_value
            # Update label
            self.user_label.setText(f"Usuario autorizado: {new_value}")
            # Persist like user/password using system keychain
            try:
                if self.chk_remember.isChecked():
                    keyring.set_password("tikr-scraper-client", "__authorized_user_number__", new_value)
                else:
                    try:
                        keyring.delete_password("tikr-scraper-client", "__authorized_user_number__")
                    except Exception:
                        pass
            except Exception:
                pass

    def load_existing_token(self):
        # Attempt to load stored credentials from keychain
        try:
            last_email = keyring.get_password("tikr-scraper-client", "__last_tikr_client_email__")
            if last_email:
                self.input_email.setText(last_email)
                stored_password = keyring.get_password("tikr-scraper-client", last_email)
                if stored_password:
                    self.input_password.setText(stored_password)
                    self.chk_remember.setChecked(True)
                self.stored_email = last_email
                self.stored_password = stored_password or ""
        except Exception:
            pass

        # Load stored authorized user number
        try:
            authorized_user = keyring.get_password("tikr-scraper-client", "__authorized_user_number__")
            if authorized_user:
                self.authorized_user_number = authorized_user
                self.user_label.setText(f"Usuario autorizado: {authorized_user}")
        except Exception:
            pass

        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                token = data.get("token", "")
                if token:
                    self.token = token
                    self.lbl_token_status.setText("Token cargado ✅")
                    self.lbl_token_status.setProperty("class", "status-ok")
                    # Validar token automáticamente con AAPL
                    try:
                        self.set_busy(True, "Validando token...")
                        self.worker = ValidateTokenWorker("AAPL", self.token)
                        self.worker.finished.connect(self._on_validate_done)
                        self.worker.start()
                    except Exception:
                        # Si falla la validación inmediata, mantener la UI operativa
                        self.set_busy(False)
                else:
                    self.lbl_token_status.setText("Archivo de token encontrado pero vacío ❌")
                    self.lbl_token_status.setProperty("class", "status-error")
        except Exception:
            self.lbl_token_status.setText("Error al leer el archivo de token ❌")
            self.lbl_token_status.setProperty("class", "status-error")

    def set_busy(self, busy: bool, message: str | None = None):
        if busy:
            # Show a modal blocking dialog with status and cancel option
            self.cancel_requested = False
            if self.busy_dialog is None:
                self.busy_dialog = BusyDialog(message or "Procesando...", on_cancel=self._cancel_operation, parent=self)
            else:
                if message:
                    self.busy_dialog.update_message(message)
            self.busy_dialog.show()
            self.busy_dialog.raise_()
            QApplication.processEvents()
        else:
            # Close modal and reset cancellation state
            try:
                if self.busy_dialog is not None:
                    self.busy_dialog.close()
            except Exception:
                pass
            self.busy_dialog = None
            self.cancel_requested = False
            QApplication.processEvents()

    def handle_generate_token(self):
        email = self.input_email.text().strip()
        password = self.input_password.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Faltan datos", "Por favor introduce el correo y la contraseña.")
            return

        self.btn_generate_token.setEnabled(False)
        self.lbl_token_status.setText("Generando token...")
        self.set_busy(True, "Generando token...")

        # Run token generation in a background thread to keep UI responsive and support cancel
        self.worker = TokenWorker(email, password, self.token_file)
        self.worker.finished.connect(self._on_token_done)
        self.worker.start()

    def _cancel_operation(self):
        # User clicked cancel in the busy dialog
        self.cancel_requested = True
        try:
            if self.worker is not None:
                # All workers implement cancel()
                self.worker.cancel()
        except Exception:
            pass

    def _on_token_done(self):
        # Called when the TokenWorker thread finishes
        self.set_busy(False)
        try:
            if self.worker and self.worker.error:
                self.lbl_token_status.setText("Error al generar el token ❌")
                self.lbl_token_status.setProperty("class", "status-error")
                QMessageBox.critical(self, "Error", f"No se pudo generar el token de acceso:\n{self.worker.error}")
                try:
                    self.btn_generate_token.setEnabled(True)
                except Exception:
                    pass
            elif self.worker and self.worker.result:
                token = self.worker.result
                self.token = token
                self.lbl_token_status.setText("Token generado y guardado ✅")
                self.lbl_token_status.setProperty("class", "status-ok")
                try:
                    self.btn_generate_token.setEnabled(False)
                except Exception:
                    pass
                QMessageBox.information(self, "Éxito", "Token de acceso generado y guardado correctamente.")
                # Optionally store credentials in the system keychain
                email = self.input_email.text().strip()
                password = self.input_password.text().strip()
                if self.chk_remember.isChecked():
                    try:
                        keyring.set_password("tikr-scraper-client", "__last_tikr_client_email__", email)
                        keyring.set_password("tikr-scraper-client", email, password)
                    except Exception:
                        pass
                else:
                    # Remove any previously stored credentials
                    try:
                        keyring.delete_password("tikr-scraper-client", "__last_tikr_client_email__")
                    except Exception:
                        pass
                    try:
                        keyring.delete_password("tikr-scraper-client", email)
                    except Exception:
                        pass
        finally:
            self.worker = None
            # Mantener bloqueado si ya hay un token cargado
            try:
                if not self.token:
                    self.btn_generate_token.setEnabled(True)
            except Exception:
                pass

    def _on_validate_done(self):
        # Validación del token tras abrir la app
        self.set_busy(False)
        try:
            if self.worker and getattr(self.worker, "result", False):
                # Token válido: mantener el estado y bloquear generación manual
                self.lbl_token_status.setText("Token cargado ✅")
                self.lbl_token_status.setProperty("class", "status-ok")
                try:
                    self.btn_generate_token.setEnabled(False)
                except Exception:
                    pass
            else:
                # Token inválido o expirado
                if self.stored_email and self.stored_password:
                    # Informar al usuario y regenerar token automáticamente
                    QMessageBox.information(self, "Información", "El token está inválido o expirado.\nSe generará un nuevo token usando las credenciales almacenadas.")
                    self.lbl_token_status.setText("Generando nuevo token...")
                    self.lbl_token_status.setProperty("class", "status-ok")
                    self.set_busy(True, "Generando nuevo token...")
                    try:
                        self.btn_generate_token.setEnabled(False)
                    except Exception:
                        pass
                    # Iniciar generación de token con credenciales almacenadas
                    self.worker = TokenWorker(self.stored_email, self.stored_password, self.token_file)
                    self.worker.finished.connect(self._on_token_done)
                    self.worker.start()
                else:
                    # No hay credenciales almacenadas: actualizar etiqueta acorde
                    self.lbl_token_status.setText("Token inválido o expirado ❌")
                    self.lbl_token_status.setProperty("class", "status-error")
                    try:
                        self.btn_generate_token.setEnabled(True)
                    except Exception:
                        pass
        finally:
            # Si no iniciamos la regeneración, limpiar worker
            if not isinstance(self.worker, TokenWorker):
                self.worker = None

    def download_excel(self):
        if not self.token:
            QMessageBox.warning(self, "Sin token", "Por favor genera o carga un token primero.")
            return

        asset = self.input_asset.text().strip()
        if not asset:
            QMessageBox.warning(self, "Activo faltante", "Por favor introduce el activo (ticker o nombre de la empresa).")
            return

        # Validate user number
        user_number = (self.authorized_user_number or "").strip()
        if not user_number:
            QMessageBox.warning(self, "Número de usuario faltante", "Por favor configura tu número de usuario autorizado.")
            return
        if not user_number.isdigit():
            QMessageBox.warning(self, "Número de usuario inválido", "El número de usuario debe ser numérico.")
            return

        # Run download in a background thread with a modal busy dialog and cancel support
        self.set_busy(True, f"Obteniendo archivo Excel de {asset}...")
        self.button.setEnabled(False)
        self.worker = DownloadWorker(asset, self.token, user_number)
        self.worker.finished.connect(self._on_download_done)
        self.worker.start()

    def _on_download_done(self):
        try:
            if self.worker and self.worker.error:
                QMessageBox.critical(self, "Error", f"No se pudo descargar el archivo:\n\n{self.worker.error}")
                self.status_label.setText("Error al descargar ❌")
                self.status_label.setProperty("class", "status-error")
            elif self.worker and self.worker.result:
                suggested_name = self.worker.result["suggested_name"]
                content = self.worker.result["content"]
                # Ask where to save the file with suggested name
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Guardar archivo Excel", suggested_name, "Archivos de Excel (*.xlsx)"
                )
                if file_path:
                    with open(file_path, "wb") as f:
                        f.write(content)
                    QMessageBox.information(self, "Éxito", "¡Archivo Excel descargado correctamente!")
                    self.status_label.setText("Descarga completada ✅")
                    self.status_label.setProperty("class", "status-ok")
        finally:
            # Ensure UI is always unblocked even if other unexpected errors occur
            self.set_busy(False)
            self.button.setEnabled(True)
            self.worker = None
