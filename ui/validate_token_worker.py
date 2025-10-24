from PyQt6.QtCore import QThread
from .client_utils import ensure_asset_and_token


class ValidateTokenWorker(QThread):
    def __init__(self, asset: str, token: str):
        super().__init__()
        self.asset = asset
        self.token = token
        self.result = None
        self.error = None

    def run(self):
        try:
            ensure_asset_and_token(self.asset, self.token)
            self.result = True
        except Exception as e:
            self.error = e
            self.result = False
