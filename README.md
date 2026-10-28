# QA Toolkit

Sistema unificado de herramientas de QA con interfaz gráfica (Tkinter). Cada funcionalidad se ejecuta con un botón; la lógica de negocio está separada de la UI y cada herramienta es un módulo independiente, así el sistema crece sumando módulos sin tocar el resto.

## Herramientas incluidas

| Pestaña | Botones | Qué hace |
|---|---|---|
| **Conexión** | Probar conexión · Guardar configuración | Datos de Azure DevOps compartidos por todas las herramientas. |
| **Importar Test Cases** | Generar plantilla Excel · Validar Excel · Importar a Azure DevOps | Crea un Test Case por fila del Excel y lo agrega a un Test Plan / Suite. No duplica los que ya están en la suite. |
| **Reportes Test Plans** | Generar Excel de resultados · Abrir Excel · Abrir reporte Power BI | Descarga el resultado de cada test point y arma el Excel (`Detalle` + `Resumen`) que consume Power BI. |

## Instalación desde cero

**Requisitos:** Python 3.10 o superior (`python --version`) y Git. En Windows, Tkinter viene incluido con Python; instalá Python desde [python.org](https://www.python.org/downloads/) tildando **Add Python to PATH**.

### Windows (PowerShell)

```powershell
# 1. Clonar el repo
git clone https://github.com/Oven30U/qa-toolkit.git
cd qa-toolkit

# 2. Crear el entorno virtual
python -m venv .venv

# 3. Activarlo (el prompt muestra "(.venv)")
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. (Opcional) Crear tu configuración
copy .env.example .env

# 6. Ejecutar
python main.py
```

- Si el paso 3 dice que la ejecución de scripts está deshabilitada, corré una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí el paso 3.
- En CMD, el paso 3 es `.venv\Scripts\activate.bat`.

### Linux / macOS

```bash
git clone https://github.com/Oven30U/qa-toolkit.git && cd qa-toolkit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # opcional
python main.py
```

En Linux, si falta Tkinter: `sudo apt install python3-tk`.

### Próximas veces

Abrí una terminal en la carpeta del proyecto, activá el entorno (paso 3) y corré `python main.py`.

## Configuración (`.env`)

Podés completar los datos de dos maneras:

- **Desde la app (recomendado):** pestaña **Conexión** → completar → **Guardar configuración (.env)**. El PAT nunca se guarda.
- **A mano:** editá `.env` (copia de [`.env.example`](.env.example), que tiene cada variable comentada). `.env` está en `.gitignore`: es personal, no lo subas.

Cómo conseguir cada valor en Azure DevOps:

### 1. `AZDO_URL` y `PROJECT`
Abrí tu proyecto en el navegador y mirá la URL:

| Tipo | URL del navegador | `AZDO_URL` | `PROJECT` |
|---|---|---|---|
| Azure DevOps Services | `https://dev.azure.com/acme/MiProyecto/_testPlans` | `https://dev.azure.com/acme` | `MiProyecto` |
| Azure DevOps Server (on-premise) | `https://servidor/Coleccion/MiProyecto/_testPlans` | `https://servidor/Coleccion` | `MiProyecto` |

`AZDO_URL` **no incluye el proyecto** ni barra final. El proyecto debe coincidir exacto (mayúsculas y espacios).

### 2. `API_VERSION` y `REPORTS_API_VERSION`
Services: `7.1` · Server 2022: `7.0` · Server 2020: `6.0` · Server 2019: `5.0`/`5.1` · TFS 2018: `4.1`. En un servidor propio la versión se ve en el menú de ayuda (**?** → **About**). Si "Probar conexión" da 404, bajá la versión. Valores por defecto: `5.1` (importador) y `4.1` (reportes).

### 3. `AZDO_PAT` (Personal Access Token)
1. Menú de tu usuario (arriba a la derecha) → **Personal access tokens** (en Server: **Security → Personal access tokens**).
2. **+ New Token** → poné un nombre (ej. `QA Toolkit`), la organización y una fecha de vencimiento razonable.
3. **Scopes → Custom defined** y marcá:
   - **Work Items → Read & write** (importador)
   - **Test Management → Read & write** (importador; para reportes alcanza *Read*)
   - **Project and Team → Read** (lo necesita "Probar conexión" en algunas versiones)
4. **Create** y copiá el token: se muestra una sola vez.
5. Pegalo en la pestaña **Conexión** (queda solo en memoria). Dejá `AZDO_PAT` comentado en el `.env` salvo que aceptes guardarlo en texto plano.

### 4. `PLAN_ID` y `SUITE_ID` (importador)
1. Menú lateral → **Test Plans** y abrí el plan (o creá uno con **+ New Test Plan** y una suite dentro).
2. Seleccioná la suite destino en el árbol de la izquierda.
3. En la URL: `…/_testPlans/execute?planId=1234&suiteId=1235` → `PLAN_ID=1234`, `SUITE_ID=1235`.

Antes de la primera carga, verificá que la suite esté vacía o que sus casos sean los que querés reutilizar.

### 5. `EXCEL_FILE` y `EXCEL_SHEET_NAME` (importador)
Usá el botón **Generar plantilla Excel**, completala y elegí el archivo con **Examinar…**. La hoja se llama `Casos de prueba` por defecto. **Validar Excel** revisa columnas e IDs duplicados sin tocar Azure DevOps.

### 6. Opcionales
- `USE_SYSTEM_CERTS=true`: usa los certificados del sistema (necesario con CA interna corporativa). Si falla el SSL, como último recurso `VERIFY_SSL=false`.
- `FILTRO_PLANES`: planes a incluir en el reporte, separados por coma (vacío = todos). `INCLUIR_INACTIVOS`: incluye planes inactivos.
- `SOLO_PRIMER_CASO=true`: importa solo la primera fila, para probar.

Guía ampliada con errores frecuentes (401, 403, 404, SSL): [docs/AZURE_DEVOPS_SETUP.md](docs/AZURE_DEVOPS_SETUP.md).

## Uso

1. Pestaña **Conexión** → completar → **Probar conexión**.
2. Elegí una herramienta y usá sus botones. El registro de actividad (abajo) muestra el avance y **Cancelar tarea** corta al terminar el paso en curso.

## Estructura

```
qa-toolkit/
├── main.py                      # punto de entrada
├── qa_toolkit/
│   ├── app.py                   # ventana principal (pestañas + logs)
│   ├── core/                    # núcleo compartido, SIN tkinter
│   │   ├── azdo.py              #   cliente único de Azure DevOps
│   │   ├── config.py            #   Settings (.env) – el PAT nunca se persiste
│   │   ├── errors.py · tasks.py · logging_setup.py · ssl_utils.py · paths.py
│   ├── ui/                      # capa de presentación compartida
│   │   ├── context.py           #   estado de la GUI + ejecutor de tareas en segundo plano
│   │   ├── connection_view.py · widgets.py
│   └── modules/                 # una carpeta = una herramienta
│       ├── base.py · registry.py
│       ├── testcase_importer/   #   service.py (lógica) · excel_reader.py · view.py (Tkinter)
│       └── testplan_reports/    #   service.py (lógica) · view.py (Tkinter)
├── tests/                       # pytest (sin red ni Azure DevOps real)
├── .github/workflows/ci.yml     # CI: ruff + pytest
├── assets/powerbi/              # tu .pbix local (no se versiona)
├── output/ · logs/              # generados (ignorados por git)
└── docs/
    ├── AZURE_DEVOPS_SETUP.md    # cómo obtener URL, PAT, IDs, versión de API
    └── AGREGAR_MODULO.md        # cómo sumar una herramienta nueva
```

Principios: servicios sin tkinter ni `print`/`sys.exit` (lanzan excepciones y escriben en el logger) → testeables; tareas largas en hilos para no congelar la ventana; un único cliente HTTP con manejo de errores común.

## Tests

```bash
pip install -r requirements-dev.txt
pytest          # tests
ruff check .    # lint
```

## Seguridad

- El PAT vive solo en memoria (campo oculto). Alternativa: variable de entorno `AZDO_PAT`.
- `.env`, `output/` y `logs/` están en `.gitignore`.
- Si un PAT alguna vez estuvo escrito en código o en un `.env` compartido, revocalo y generá uno nuevo.

## Power BI

El botón **Abrir reporte Power BI** abre el primer `.pbix` que encuentre en `assets/powerbi/`. Los `.pbix` no se versionan (están en `.gitignore`) porque pueden contener datos del cliente: copiá ahí tu propio reporte.

Para construirlo, en Power BI Desktop elegí *Obtener datos → Excel* y apuntá a `output/testplans_resultados.xlsx` (hojas `Detalle` y `Resumen`), que genera el botón **Generar Excel de resultados**.
