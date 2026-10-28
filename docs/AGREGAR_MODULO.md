# Cómo agregar una nueva herramienta de QA

1. Crear `qa_toolkit/modules/<mi_herramienta>/` con:
   - `service.py`: la lógica. Sin tkinter. Recibe `client`/`logger`, usa `cancel.check()` entre pasos, lanza excepciones de `core/errors.py`.
   - `view.py`: una clase `ttk.Frame` con `__init__(self, parent, ctx: AppContext)`. Un `ttk.Button` por acción; los botones que lanzan tareas largas se registran con `ctx.register_button(b)` y ejecutan `ctx.run_task("Nombre", lambda token: servicio.ejecutar(...), on_success)`.
   - `__init__.py`: `SPEC = ModuleSpec(id=..., title=..., description=..., view_path="qa_toolkit.modules.<mi_herramienta>.view:MiVista")`.
2. Si necesita ajustes nuevos: agregar el campo a `Settings` (`core/config.py`, incluido `ENV_KEYS`) y a `.env.example`.
3. Registrarla en `qa_toolkit/modules/registry.py` (`MODULES`).
4. Agregar tests en `tests/` con un cliente falso (ver `test_importer_service.py`).
