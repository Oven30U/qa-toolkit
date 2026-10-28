"""Vista Tkinter de reportes de Test Plans. Un boton por accion."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox, ttk

from qa_toolkit.core.errors import QAToolkitError
from qa_toolkit.core.paths import POWERBI_DIR
from qa_toolkit.modules.testplan_reports.service import ReporteTestPlans
from qa_toolkit.ui.context import AppContext
from qa_toolkit.ui.widgets import elegir_archivo, fila_campo


def abrir_en_sistema(ruta: Path | str) -> None:
    ruta = str(ruta)
    if sys.platform.startswith("win"):
        os.startfile(ruta)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])


class ReportsView(ttk.Frame):
    def __init__(self, parent, ctx: AppContext):
        super().__init__(parent, padding=16)
        self.ctx = ctx
        ttk.Label(self, text="Reportes de Test Plans → Excel / Power BI", style="Title.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            self,
            text="Descarga el resultado de cada test point de los planes y arma el Excel para Power BI.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        v = ctx.vars
        fila_campo(grid, 0, "Filtro de planes", v["filtro_planes"])
        ttk.Label(grid, text="Nombres separados por coma. Vacío = todos.", style="Muted.TLabel").grid(
            row=1, column=1, sticky="w"
        )
        fila_campo(
            grid,
            2,
            "Excel de salida",
            v["reports_output_file"],
            examinar=elegir_archivo(v["reports_output_file"], guardar=True),
        )
        fila_campo(grid, 3, "API version (reportes)", v["reports_api_version"], ancho=10)
        ttk.Checkbutton(grid, text="Incluir planes inactivos", variable=v["incluir_inactivos"]).grid(
            row=4, column=1, sticky="w", pady=(6, 0)
        )

        botones = ttk.Frame(self)
        botones.pack(anchor="w", pady=16)
        b1 = ttk.Button(
            botones, text="Generar Excel de resultados", style="Accent.TButton", command=self.generar
        )
        b2 = ttk.Button(botones, text="Abrir Excel", command=self.abrir_excel)
        b3 = ttk.Button(botones, text="Abrir reporte Power BI", command=self.abrir_powerbi)
        for b in (b1, b2, b3):
            b.pack(side="left", padx=(0, 8))
        ctx.register_button(b1)

    def generar(self):
        try:
            s = self.ctx.read_settings()
            client = self.ctx.build_client(s, api_version=s.reports_api_version)
        except QAToolkitError as e:
            messagebox.showerror("Reportes", str(e))
            return
        reporte = ReporteTestPlans(client, self.ctx.log)

        def ok(r):
            messagebox.showinfo("Reporte generado", f"{r.filas} filas de {r.planes} planes.\n\n{r.archivo}")

        self.ctx.run_task("Generar Excel de Test Plans", lambda token: reporte.ejecutar(s, token), ok)

    def abrir_excel(self):
        ruta = Path(self.ctx.vars["reports_output_file"].get())
        if not ruta.is_file():
            messagebox.showwarning("Abrir Excel", "Todavía no existe el Excel. Generalo primero.")
            return
        abrir_en_sistema(ruta)

    def abrir_powerbi(self):
        pbix = sorted(POWERBI_DIR.glob("*.pbix"))
        if not pbix:
            messagebox.showwarning("Power BI", f"No hay archivos .pbix en:\n{POWERBI_DIR}")
            return
        abrir_en_sistema(pbix[-1])
