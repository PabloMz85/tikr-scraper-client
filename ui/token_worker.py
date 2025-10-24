from PyQt6.QtCore import QThread
from .client_utils import get_access_token


class TokenWorker(QThread):
    def __init__(self, email: str, password: str, token_file: str | None):
        super().__init__()
        self.email = email
        self.password = password
        self.token_file = token_file
        self.result = None
        self.error = None
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            # Pass a cancellable hook into client_utils.get_access_token
            self.result = get_access_token(
                self.email,
                self.password,
                token_file=self.token_file,
                should_cancel=lambda: self._cancel,
            )
        except Exception as e:
            self.error = e

