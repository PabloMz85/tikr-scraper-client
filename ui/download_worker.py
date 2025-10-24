from PyQt6.QtCore import QThread
import requests
from .client_utils import ensure_asset_and_token
from .config import API_URL


class DownloadWorker(QThread):
    def __init__(self, asset: str, token: str, user_number: str):
        super().__init__()
        self.asset = asset
        self.token = token
        self.user_number = user_number
        self.result = None
        self.error = None
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            # Validate asset exists and token is valid
            if self._cancel:
                raise RuntimeError("Operación cancelada por el usuario")
            ensure_asset_and_token(self.asset, self.token)

            # Download with streaming so we can cancel mid-transfer
            response = requests.post(
                API_URL,
                json={"asset": self.asset, "token": self.token, "user_number": self.user_number},
                stream=True,
                timeout=60,
            )

            # If the server returned an error, extract and surface the message
            if response.status_code >= 400:
                # Safely parse error body (JSON preferred, fallback to text)
                msg = ""
                content_type = (response.headers.get("Content-Type") or "").lower()
                try:
                    if "application/json" in content_type:
                        data = response.json()
                        msg = data.get("error") or data.get("message") or ""
                    else:
                        # Access response.text even with stream=True; requests will fetch content if needed
                        msg = (response.text or "").strip()
                except Exception:
                    try:
                        msg = (response.text or "").strip()
                    except Exception:
                        msg = ""

                if not msg:
                    msg = f"{response.status_code} {response.reason}"

                raise RuntimeError(msg)

            suggested_name = f"{self.asset}.xlsx"
            cd = response.headers.get("Content-Disposition", "")
            if cd:
                filename = None
                parts = [p.strip() for p in cd.split(";")]
                for part in parts:
                    lower = part.lower()
                    if lower.startswith("filename*="):
                        value = part.split("=", 1)[1]
                        if value.lower().startswith("utf-8''"):
                            value = value[7:]
                        filename = requests.utils.unquote(value.strip('"'))
                        break
                    elif lower.startswith("filename="):
                        value = part.split("=", 1)[1]
                        filename = requests.utils.unquote(value.strip('"'))
                        break
                if filename:
                    suggested_name = filename

            buf = bytearray()
            for chunk in response.iter_content(chunk_size=65536):
                if self._cancel:
                    raise RuntimeError("Operación cancelada por el usuario")
                if chunk:
                    buf.extend(chunk)

            self.result = {"content": bytes(buf), "suggested_name": suggested_name}
        except Exception as e:
            self.error = e
