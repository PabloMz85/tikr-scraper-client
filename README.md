# Cliente de Exportación TIKR (tikr-client)

Aplicación de escritorio en PyQt6 para:
- Iniciar sesión en TIKR y generar un token de acceso de forma automática
- Validar el token contra la API pública de TIKR
- Configurar el número de usuario autorizado
- Solicitar la descarga de un Excel con datos del activo seleccionado


## Tabla de contenido
- Requisitos previos
- Instalación
- Ejecutar el cliente de escritorio
- Uso
- Seguridad y almacenamiento de credenciales
- Empaquetado y reconstrucción (PyInstaller y CI)
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


## Ejecutar el cliente de escritorio

Desde este proyecto `tikr-client`:
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
   - Este número es requerido para habilitar la descarga.

3) Descargar Excel:
   - En “Exportar”, introduce el activo (ticker o nombre de empresa), por ejemplo `AAPL`.
   - Pulsa “Descargar Excel”.
   - Si todo es correcto, se descargará el archivo y podrás elegir dónde guardarlo. El nombre sugerido se toma del `Content-Disposition` de la respuesta.

4) Validación automática:
   - Si existe `token.json` al abrir la app, se valida automáticamente con `AAPL`.
   - Si el token está expirado y existen credenciales almacenadas, el cliente intentará regenerarlo automáticamente.

## Seguridad y almacenamiento de credenciales

- Las credenciales se guardan (si lo decides) usando `keyring` en el llavero del sistema.
- El archivo `token.json` contiene el token y la marca temporal de creación.
- Las credenciales nunca se envían al servidor local; solo se usan para obtener un token directamente desde `app.tikr.com`.

## Empaquetado y reconstrucción (PyInstaller y CI)

A continuación se detallan las opciones para generar y reconstruir el ejecutable del cliente en macOS y Windows, así como la construcción automatizada en GitHub Actions.

Requisitos previos
- Python 3.10+ (se recomienda usar un entorno virtual)
- Google Chrome (o Chromium). Si usas Chromium, define CHROME_BIN con la ruta al binario.
- Conexión a internet (para inicio de sesión en TIKR y descarga de ChromeDriver por webdriver-manager en el primer uso).

Opción A) Reconstruir localmente en macOS (Apple Silicon)
1) Abrir una terminal y posicionarse en el proyecto:
```bash
cd /ruta/al/proyecto/tikr-client
```
2) Activar el entorno virtual (o crearlo si no existe):
```bash
python -m venv .venv
source .venv/bin/activate
```
3) Instalar/actualizar dependencias:
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```
4) (Opcional) Limpiar artefactos de builds previas:
```bash
rm -rf build dist TIKR-Client.spec
```
5) Construir:
```bash
python -m PyInstaller --noconfirm --windowed --onedir --name "TIKR-Client" app.py
```
6) Resultado:
- La app quedará en: `dist/TIKR-Client/TIKR-Client.app`
- Esta build es para Apple Silicon (arm64). Para soporte Intel, construir en una máquina Intel o usar un runner macOS Intel en CI.

Opción B) Reconstruir localmente en Windows
1) Abrir PowerShell o CMD y posicionarse en el proyecto:
```powershell
cd \ruta\al\proyecto\tikr-client
```
2) Crear/activar entorno virtual:
```powershell
py -m venv .venv
.\.venv\Scripts\activate
```
3) Instalar/actualizar dependencias:
```powershell
py -m pip install --upgrade pip setuptools wheel
py -m pip install -r requirements.txt
```
4) (Opcional) Limpiar artefactos:
```powershell
rmdir /s /q build dist
del TIKR-Client.spec
```
5) Construir:
```powershell
py -m PyInstaller --noconfirm --windowed --onedir --name "TIKR-Client" app.py
```
6) Resultado:
- Ejecutable y archivos de soporte en: `dist\TIKR-Client\TIKR-Client.exe`

Opción C) Reconstruir vía GitHub Actions (Windows y macOS)
- Ya existe un workflow en: `.github/workflows/build.yml`
- Cómo dispararlo:
  - Hacer push a `main`/`master`
  - Hacer push de un tag con formato `v*.*.*` (por ejemplo, `v1.2.3`)
  - Ejecutarlo manualmente desde la pestaña “Actions” → “Build TIKR Client” → “Run workflow”
- Artefactos generados:
  - macOS: `dist/TIKR-Client/TIKR-Client.app`
  - Windows: `dist\TIKR-Client\TIKR-Client.exe`
- Para añadir una build macOS Intel (además de Apple Silicon), puedes agregar otro job con `runs-on: macos-13` en el matrix del workflow.

Uso de archivo .spec (opcional)
- PyInstaller genera `TIKR-Client.spec` en la primera ejecución.
- Puedes reconstruir con:
```bash
pyinstaller TIKR-Client.spec
```
- Es útil para fijar exactamente qué plugins/datos incluir. Si editas el `.spec`, vuelve a construir con ese archivo.

Onefile vs Onedir
- Recomendado: `--onedir` para apps PyQt, ya que facilita la carga de plugins y reduce problemas.
- Windows: si prefieres un único binario, puedes probar `--onefile` (ten en cuenta que en ejecución expandirá contenido temporalmente).
- macOS: la salida natural es un `.app` bundle; se mantiene `--windowed` para evitar abrir terminal.

Distribución y empaquetado
- macOS: para distribuir, comprime la app:
```bash
ditto -c -k --sequesterRsrc --keepParent "dist/TIKR-Client/TIKR-Client.app" "TIKR-Client-macOS-arm64.zip"
```
- Windows: comprime la carpeta `dist\TIKR-Client`.

Firma de código (recomendado para distribución)
- macOS: la app no está firmada. Gatekeeper puede mostrar advertencias. Para distribución pública, firma y notariza con un certificado “Developer ID Application”.
- Windows: el `.exe` no está firmado y puede disparar SmartScreen. Considera firmar el ejecutable con un certificado de firma de código.

Solución de problemas específica del empaquetado
- Chrome no se encuentra: instala Google Chrome o define `CHROME_BIN` apuntando a Chromium.
- Descarga de ChromeDriver: `webdriver-manager` lo descarga al primer uso; requiere internet.
- Errores de plugins Qt: usa el comando minimalista mostrado (evita colecciones agresivas de módulos con `--collect-all` si no son necesarias).
- Cambio de versión de Python: recrea el entorno virtual:
  - macOS:
    ```bash
    rm -rf .venv
    python3 -m venv .venv
    source .venv/bin/activate
    ```
  - Windows:
    ```powershell
    rmdir /s /q .venv
    py -m venv .venv
    .\.venv\Scripts\activate
    ```
## Arquitectura del proyecto

Estructura principal:
- `app.py`: punto de entrada (crea `QApplication`, muestra `ExcelDownloader`).
- `ui/excel_downloader.py`: ventana principal, estados UI y coordinación de acciones.
- `ui/token_worker.py`: hilo en segundo plano para generar token (usa Selenium).
- `ui/validate_token_worker.py`: hilo para validar token con una consulta básica.
- `ui/download_worker.py`: hilo que realiza la solicitud de descarga y gestiona la descarga en streaming.
- `ui/client_utils.py`:
  - `create_driver()`: configura Chrome headless con Selenium Wire.
  - `get_access_token(...)`: login y extracción de token `auth`.
  - `ensure_asset_and_token(...)`: valida que el activo existe y que el token es válido.
- `ui/config.py`: `API_URL` del servicio de descarga (configurable).
- `ui/authorized_user_dialog.py`: diálogo para configurar el número de usuario.
- `ui/busy_dialog.py`: diálogo modal para mostrar progreso y permitir cancelar.

## Configuración

- `API_URL`: definida en `ui/config.py` (configurable).
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
  - Comprueba el número de usuario autorizado y el ticker.
  - Revisa el mensaje específico devuelto por el servidor en la alerta.
- Operación cancelada:
  - Algunas tareas se pueden cancelar desde el diálogo de progreso; el mensaje “Operación cancelada por el usuario” es esperado si se aborta.

---
