# Cómo conseguir los datos de Azure DevOps

Guía para completar el `.env` (o la pestaña **Conexión**). Los nombres de menús pueden variar levemente según la versión de tu Azure DevOps.

## 1. URL y proyecto (`AZDO_URL`, `PROJECT`)

Abrí tu proyecto en el navegador y mirá la URL:

| Tipo | URL del navegador | `AZDO_URL` | `PROJECT` |
|---|---|---|---|
| Azure DevOps Services | `https://dev.azure.com/acme/MiProyecto/_testPlans` | `https://dev.azure.com/acme` | `MiProyecto` |
| Azure DevOps Server (on-premise) | `https://servidor/Coleccion/MiProyecto/_testPlans` | `https://servidor/Coleccion` | `MiProyecto` |

`AZDO_URL` **no lleva el proyecto** ni barra final. El nombre del proyecto debe coincidir exactamente (mayúsculas, espacios).

## 2. Versión de API (`API_VERSION`, `REPORTS_API_VERSION`)

| Tu plataforma | API version |
|---|---|
| Azure DevOps Services | 7.1 |
| Azure DevOps Server 2022 | 7.0 |
| Azure DevOps Server 2020 | 6.0 |
| Azure DevOps Server 2019 | 5.0 / 5.1 |
| TFS 2018 | 4.1 |

En un servidor on-premise, la versión se ve en el menú de ayuda (**?** → **About**). Si "Probar conexión" devuelve 404, bajá la versión.

## 3. Personal Access Token (`AZDO_PAT`)

1. Arriba a la derecha, abrí el menú de tu usuario → **Personal access tokens** (en Server: **Security → Personal access tokens**).
2. **+ New Token**.
3. Completá:
   - **Name**: p. ej. `QA Toolkit`.
   - **Organization**: la que corresponda.
   - **Expiration**: una fecha razonable (evitá "sin vencimiento").
4. **Scopes → Custom defined** y marcá (si no ves la lista completa, **Show all scopes**):
   - **Work Items → Read & write** (importador)
   - **Test Management → Read & write** (importador) — para los reportes alcanza con *Read*
   - **Project and Team → Read** (necesario para "Probar conexión" en algunas versiones)
5. **Create** y copiá el token: se muestra **una sola vez**.

Pegalo en la pestaña **Conexión** (queda solo en memoria). No lo escribas en código, Excel ni chats; si se expone, revocalo en la misma pantalla y generá uno nuevo.

## 4. Test Plan y Test Suite (`PLAN_ID`, `SUITE_ID`)

1. Menú lateral → **Test Plans** y abrí el plan; si no existe, **+ New Test Plan** y creá una suite dentro.
2. Seleccioná la suite destino en el árbol de la izquierda.
3. Mirá la URL: `…/_testPlans/execute?planId=1234&suiteId=1235`
   - `planId` → `PLAN_ID`
   - `suiteId` → `SUITE_ID`

Antes de la primera carga confirmá que la suite esté vacía, o que los casos que ya tiene sean los que querés reutilizar (el importador solo reutiliza casos de **esa** suite, nunca de otras).

## 5. Excel de casos (`EXCEL_FILE`, `EXCEL_SHEET_NAME`)

Usá el botón **Generar plantilla Excel** y completala. Columnas requeridas (nombres exactos):

| Columna | Contenido |
|---|---|
| `ID caso de prueba` | Único (ej. `CP-001`). Se usa como tag y para no duplicar. |
| `Módulo`, `Funcionalidad` | Clasificación del caso (se cargan como tags). |
| `Nombre del caso de prueba` | Título; el Work Item queda como `[ID] Nombre`. |
| `Descripción del caso de prueba` | Objetivo del caso. |
| `Instrucciones de ejecución` | Un paso por línea (Alt+Enter en la celda). La numeración inicial es opcional. |
| `Resultado esperado` | Una línea por paso, en el mismo orden que las instrucciones. |

Podés agregar columnas propias a la derecha: se ignoran. El botón **Validar Excel** revisa columnas e IDs duplicados sin tocar Azure DevOps.

## Errores frecuentes

| Síntoma | Causa probable |
|---|---|
| 401 | PAT inválido, vencido o de otra organización. |
| 403 | Faltan scopes en el PAT. |
| 404 | `AZDO_URL`/`PROJECT` mal escritos (¿incluiste el proyecto en la URL?), IDs inexistentes o `API_VERSION` no soportada. |
| Error de certificado SSL | Activá `USE_SYSTEM_CERTS`; como último recurso `VERIFY_SSL=false`. |
| "No se pudo escribir el Excel" | El archivo de salida está abierto en Excel o Power BI. |
