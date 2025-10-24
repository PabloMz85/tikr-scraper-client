# Cliente de Exportación TIKR (tikr-scraper-client)

Aplicación de escritorio en PyQt6 para:
- Iniciar sesión en TIKR y generar un token de acceso de forma automática
- Validar el token contra la API pública de TIKR
- Configurar el número de usuario autorizado
- Solicitar al servidor local la descarga de un Excel con datos del activo seleccionado

Este cliente se integra con el servidor de `tikr-scraper` expuesto en `http://127.0.0.1:5050/v0.1/getAssetExcel`.

## Tabla de contenido
- Requisitos previos
- Instalación
- Ejecutar el servidor backend (tikr-scraper)
- Ejecutar el cliente de escritorio
- Uso
- Seguridad y almacenamiento de credenciales
- Empaquetado como ejecutable (PyInstaller)
- Arquitectura del proyecto
- Configuración
- Solución de problemas

---

## Requisitos previos

- Python 3.10+ recomendado
- Google Chrome (o Chromium)
  - El cliente usa Selenium y `webdriver-manager` para gestionar ChromeDriver automáticamente.
  - En Linux/Docker se puede definir `CHROME_BIN=/usr/bin/chromium` para usar Chromium.
- Acceso a una cuenta en TIKR para poder generar el token de acceso.
- Servidor local `tikr-scraper` ejecutándose en `http://127.0.0.1:5050` (ver sección Backend).

## Instalación

1) Crear y activar un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows (PowerShell/CMD)
```

2) Instalar dependencias:
```bash
pip install -r requirements.txt
```

Dependencias clave:
- PyQt6: UI escritorio
- selenium, selenium-wire, webdriver-manager: automatización Chrome y captura de petición para extraer el token
- requests: peticiones HTTP
- keyring: almacenamiento seguro de credenciales en llavero del sistema
- pyinstaller: empaquetado opcional

## Ejecutar el servidor backend (tikr-scraper)

Este cliente se comunica con un servidor local que expone el endpoint:
```
POST http://127.0.0.1:5050/v0.1/getAssetExcel
Body JSON: { "asset": "<ticker|nombre>", "token": "<tokenTikr>", "user_number": "<numero>" }
```

Para iniciarlo desde el proyecto `tikr-scraper`:
```bash
# En el repo tikr-scraper
python server.py
# Por defecto escucha en http://127.0.0.1:5050
```

Asegúrate de que el endpoint anterior responda correctamente antes de usar el cliente.

## Ejecutar el cliente de escritorio

Desde este proyecto `tikr-scraper-client`:
```bash
python app.py
```

Se abrirá la ventana “Cliente de Exportación TIKR”.

## Uso

1) Cuenta:
   - Introduce tu correo y contraseña de TIKR.
   - Opcional: marca “Recordar credenciales” para guardarlas de forma segura en el llavero del sistema.
   - Pulsa “Generar token de acceso”.
     - El cliente abrirá un Chrome headless, iniciará sesión en TIKR, navegará al Screener y capturará el token (campo `auth`) de la petición a `api.tikr.com/fs`.
     - El token se guarda en `token.json` en el directorio del cliente.

2) Usuario autorizado:
   - Pulsa “Configurar usuario autorizado” e introduce tu número de usuario autorizado.
   - Este número es requerido por el backend para habilitar la descarga.

3) Descargar Excel:
   - En “Exportar”, introduce el activo (ticker o nombre de empresa), por ejemplo `AAPL`.
   - Pulsa “Descargar Excel”.
   - Si todo es correcto, se solicitará al servidor el archivo y podrás elegir dónde guardarlo. El nombre sugerido se toma del `Content-Disposition` de la respuesta.

4) Validación automática:
   - Si existe `token.json` al abrir la app, se valida automáticamente con `AAPL`.
   - Si el token está expirado y existen credenciales almacenadas, el cliente intentará regenerarlo automáticamente.

## Seguridad y almacenamiento de credenciales

- Las credenciales se guardan (si lo decides) usando `keyring` en el llavero del sistema.
- El archivo `token.json` contiene el token y la marca temporal de creación.
- Las credenciales nunca se envían al servidor local; solo se usan para obtener un token directamente desde `app.tikr.com`.

## Empaquetado como ejecutable (PyInstaller)

Opcionalmente, puedes generar un ejecutable del cliente:
```bash
pyinstaller --noconfirm --onefile --windowed --name tikr-scraper-client app.py
```

Notas:
- En proyectos PyQt, a veces es necesario incluir recursos adicionales. Si el ejecutable no inicia, prueba sin `--onefile` o añade datos con `--add-data`.
- En macOS, `--windowed` evita abrir una terminal junto con la app.

## Arquitectura del proyecto

Estructura principal:
- `app.py`: punto de entrada (crea `QApplication`, muestra `ExcelDownloader`).
- `ui/excel_downloader.py`: ventana principal, estados UI y coordinación de acciones.
- `ui/token_worker.py`: hilo en segundo plano para generar token (usa Selenium).
- `ui/validate_token_worker.py`: hilo para validar token con una consulta básica.
- `ui/download_worker.py`: hilo que llama al backend `getAssetExcel` y gestiona la descarga en streaming.
- `ui/client_utils.py`:
  - `create_driver()`: configura Chrome headless con Selenium Wire.
  - `get_access_token(...)`: login y extracción de token `auth`.
  - `ensure_asset_and_token(...)`: valida que el activo existe y que el token es válido.
- `ui/config.py`: `API_URL` del backend (`http://127.0.0.1:5050/v0.1/getAssetExcel`).
- `ui/authorized_user_dialog.py`: diálogo para configurar el número de usuario.
- `ui/busy_dialog.py`: diálogo modal para mostrar progreso y permitir cancelar.

## Configuración

- `API_URL`: definida en `ui/config.py`. Por defecto: `http://127.0.0.1:5050/v0.1/getAssetExcel`.
- `CHROME_BIN` (opcional, Linux/Docker): ruta a binario de Chromium. Si existe, el cliente lo usará.
- `.gitignore`: ignora `token.json`, `.env`, datos temporales y archivos de entorno.

## Solución de problemas

- Token inválido o expirado:
  - Usa “Generar token de acceso” nuevamente.
  - Si habilitaste “Recordar credenciales”, la regeneración puede ocurrir automáticamente al iniciar.
- No se abre Chrome headless / error de WebDriver:
  - Asegúrate de tener Google Chrome/Chromium instalado.
  - En Linux/Docker, define `CHROME_BIN=/usr/bin/chromium` si corresponde.
  - El driver se gestiona por `webdriver-manager` y se descarga automáticamente.
- Error al descargar Excel:
  - Verifica que el servidor backend está activo en `http://127.0.0.1:5050`.
  - Comprueba el número de usuario autorizado y el ticker.
  - Revisa el mensaje específico devuelto por el servidor en la alerta.
- Operación cancelada:
  - Algunas tareas se pueden cancelar desde el diálogo de progreso; el mensaje “Operación cancelada por el usuario” es esperado si se aborta.

---
