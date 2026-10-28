"""Pestana 'Conexion': datos de Azure DevOps compartidos por todos los modulos."""

from __future__ import annotations

from tkinter import messagebox, ttk

from qa_toolkit.core.errors import QAToolkitError
from qa_toolkit.core.paths import ENV_FILE
from qa_toolkit.ui.context import AppContext
from qa_toolkit.ui.widgets import fila_campo


class ConnectionView(ttk.Frame):
    def __init__(self, parent, ctx: AppContext):
        super().__init__(parent, padding=16)
        self.ctx = ctx
        ttk.Label(self, text="Conexión a Azure DevOps", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Datos compartidos por todas las herramientas. "
            "El PAT se guarda solo en memoria, nunca en disco.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        v = ctx.vars
        fila_campo(grid, 0, "URL (colección)", v["azdo_url"])
        fila_campo(grid, 1, "Proyecto", v["project"])
        fila_campo(grid, 2, "Personal Access Token", ctx.pat, show="•")
        fila_campo(grid, 3, "API version (importador)", v["api_version"], ancho=10)
        ttk.Checkbutton(
            grid,
            text="Usar certificados del sistema (CA interna corporativa)",
            variable=v["use_system_certs"],
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            grid, text="Verificar certificado SSL (desactivar solo si falla)", variable=v["verify_ssl"]
        ).grid(row=5, column=1, sticky="w")

        botones = ttk.Frame(self)
        botones.pack(anchor="w", pady=16)
        probar = ttk.Button(botones, text="Probar conexión", style="Accent.TButton", command=self.probar)
        probar.pack(side="left")
        ctx.register_button(probar)
        ttk.Button(botones, text="Guardar configuración (.env)", command=self.guardar).pack(
            side="left", padx=8
        )

    def probar(self):
        try:
            s = self.ctx.read_settings()
            client = self.ctx.build_client(s)
        except QAToolkitError as e:
            messagebox.showerror("Conexión", str(e))
            return

        def trabajo(_token):
            return client.validar_conexion()

        def ok(proyecto):
            self.ctx.log.info("Conexión correcta. Proyecto: %s", proyecto.get("name", s.project))
            messagebox.showinfo(
                "Conexión", f"Conexión correcta.\nProyecto: {proyecto.get('name', s.project)}"
            )

        self.ctx.run_task("Probar conexión", trabajo, ok)

    def guardar(self):
        try:
            self.ctx.read_settings().save_to_env()
        except QAToolkitError as e:
            messagebox.showerror("Guardar", str(e))
            return
        self.ctx.log.info("Configuración guardada en %s (sin el PAT).", ENV_FILE)
        messagebox.showinfo("Guardar", f"Configuración guardada en:\n{ENV_FILE}\n\nEl PAT no se guarda.")
