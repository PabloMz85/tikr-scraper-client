from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import datetime
import json
import os
import time
import requests


def create_driver():
    """
    Create a headless Chrome driver with Selenium Wire enabled to intercept requests.
    Mirrors the behavior from tikr-scraper utils, with small robustness tweaks.
    """
    chrome_options = Options()
    # Use new headless mode when available
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Optional user agent
    user_agent = ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) "
                  "Chrome/22.0.1216.0 Safari/537.2")
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Detect Chromium if present (useful in Docker); macOS users typically have Chrome
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_access_token(username: str, password: str, token_file: str | None = None, should_cancel=None) -> str:
    """
    Log in to TIKR using provided credentials, navigate to Screener, trigger a request,
    and capture the 'auth' token from the intercepted POST payload. If token_file is provided,
    persist the token as JSON. Returns the token string.

    This function is adapted from tikr-scraper's utils.get_access_token to accept username/password
    directly instead of reading environment variables, and to optionally persist the token.
    """
    # Optional cancellation hook support
    def is_cancelled():
        try:
            return bool(should_cancel and callable(should_cancel) and should_cancel())
        except Exception:
            return False

    if is_cancelled():
        raise RuntimeError("Operación cancelada por el usuario")

    browser = create_driver()
    if is_cancelled():
        try:
            browser.quit()
        except Exception:
            pass
        raise RuntimeError("Operación cancelada por el usuario")
    try:
        browser.get("https://app.tikr.com/login")

        # Fill login form and submit
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="email"]'))
        ).send_keys(username)
        browser.find_element(By.XPATH, '//input[@type="password"]').send_keys(password)
        browser.find_element(By.XPATH, "//button/span").click()

        # Wait until authenticated (landing text or redirect)
        WebDriverWait(browser, 60).until(
            lambda drv: ("Welcome to TIKR" in drv.page_source) or ("screener" in drv.current_url)
        )

        # Navigate to Screener and trigger fetch to produce a POST to api.tikr.com/fs
        browser.get("https://app.tikr.com/screener?sid=1")
        fetch_button = WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button/span[contains(text(), "Fetch Screen")]/..'))
        )
        browser.execute_script("arguments[0].scrollIntoView({block: \"center\"});", fetch_button)
        time.sleep(1)
        browser.execute_script("arguments[0].click();", fetch_button)

        # Give network a moment to settle with periodic cancellation checks
        for _ in range(50):  # ~5 seconds total
            if is_cancelled():
                try:
                    browser.quit()
                except Exception:
                    pass
                raise RuntimeError("Operación cancelada por el usuario")
            time.sleep(0.1)

        # Inspect captured requests to extract the 'auth' token from the POST body
        access_token = ""
        for request in browser.requests:
            if is_cancelled():
                try:
                    browser.quit()
                except Exception:
                    pass
                raise RuntimeError("Operación cancelada por el usuario")
            try:
                if ("api.tikr.com/fs" in request.url) and (request.method == "POST"):
                    body = request.body
                    if isinstance(body, bytes):
                        body = body.decode("utf-8", errors="ignore")
                    payload = json.loads(body)
                    access_token = payload.get("auth", "")
                    if access_token:
                        break
            except Exception:
                # Continue scanning other requests in case of parsing hiccups
                continue

        if not access_token:
            raise RuntimeError("No se pudo obtener el token de acceso de TIKR")

        # Optionally persist the token
        if token_file:
            try:
                data = {
                    "token": access_token,
                    "created": datetime.datetime.utcnow().isoformat() + "Z",
                }
                with open(token_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                # If persisting fails, still return the token for immediate use
                pass

        return access_token
    finally:
        try:
            browser.quit()
        except Exception:
            pass

def default_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Origin': 'https://app.tikr.com',
        'Connection': 'keep-alive',
        'Referer': 'https://app.tikr.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'trailers'
    }

def find_company_info(ticker):
    headers = default_headers().copy()
    headers['content-type'] = 'application/x-www-form-urlencoded'
    data = '{"params":"query=' + ticker + '&distinct=2"}'
    url = ('https://tjpay1dyt8-3.algolianet.com/1/indexes/tikr-feb/query?'
           'x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser%20'
           '(lite)&x-algolia-application-id=TJPAY1DYT8&'
           'x-algolia-api-key=d88ea2aa3c22293c96736f5ceb5bab4e')
    response = requests.post(url, headers=headers, data=data)
    try:
        hits = response.json().get('hits', [])
        if hits:
            tid = hits[0].get('tradingitemid')
            cid = hits[0].get('companyid')
            return tid, cid
        return None, None
    except Exception:
        return None, None

def get_tibobj_data(access_token: str, headers: dict, tid: int, cid: int) -> any:
    url = 'https://api.tikr.com/tidobj'
    payload = json.dumps({
        "auth": access_token,
        "tid": tid,
        "cid": cid,
        "v": "v0"
    })
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

def ensure_asset_and_token(asset: str, access_token: str):
    tid, cid = find_company_info(asset)
    if not tid or not cid:
        raise ValueError("Activo no encontrado. Por favor verifica el ticker o el nombre.")
    headers = default_headers()
    resp = get_tibobj_data(access_token, headers, tid, cid)
    if not isinstance(resp, dict) or ('data' not in resp and 'cTblDataObj' not in resp) or resp.get('error'):
        raise RuntimeError("Token inválido o expirado. Por favor inicia sesión nuevamente para refrescar tu token.")
    return tid, cid
