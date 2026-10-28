"""Vista Tkinter del importador de Test Cases. Un boton por accion."""

from __future__ import annotations

from tkinter import filedialog, messagebox, ttk

from qa_toolkit.core.errors import QAToolkitError
from qa_toolkit.modules.testcase_importer.excel_reader import cargar_excel, generar_plantilla
from qa_toolkit.modules.testcase_importer.service import ImportadorTestCases
from qa_toolkit.ui.context import AppContext
from qa_toolkit.ui.widgets import elegir_archivo, fila_campo


class ImporterView(ttk.Frame):
    def __init__(self, parent, ctx: AppContext):
        super().__init__(parent, padding=16)
        self.ctx = ctx
        ttk.Label(self, text="Importar Test Cases a Azure DevOps", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Crea un Test Case por cada fila del Excel y lo agrega a la Suite destino.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        v = ctx.vars
        fila_campo(grid, 0, "Nombre del Test Plan", v["test_plan_name"])
        fila_campo(grid, 1, "Plan ID", v["plan_id"], ancho=12)
        fila_campo(grid, 2, "Suite ID", v["suite_id"], ancho=12)
        fila_campo(grid, 3, "Archivo Excel", v["excel_file"], examinar=elegir_archivo(v["excel_file"]))
        fila_campo(grid, 4, "Hoja", v["excel_sheet_name"], ancho=30)
        ttk.Checkbutton(
            grid, text="Procesar solo el primer caso (prueba)", variable=v["solo_primer_caso"]
        ).grid(row=5, column=1, sticky="w", pady=(6, 0))

        botones = ttk.Frame(self)
        botones.pack(anchor="w", pady=16)
        b1 = ttk.Button(botones, text="Generar plantilla Excel", command=self.plantilla)
        b2 = ttk.Button(botones, text="Validar Excel", command=self.validar_excel)
        b3 = ttk.Button(
            botones, text="Importar a Azure DevOps", style="Accent.TButton", command=self.importar
        )
        for b in (b1, b2, b3):
            b.pack(side="left", padx=(0, 8))
            ctx.register_button(b)

    # ---------------------------------------------------------- acciones
    def plantilla(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="Plantilla_Casos_de_Prueba.xlsx",
            filetypes=[("Excel", "*.xlsx")],
        )
        if not ruta:
            return
        generar_plantilla(ruta)
        self.ctx.log.info("Plantilla creada: %s", ruta)
        messagebox.showinfo("Plantilla", f"Plantilla creada:\n{ruta}")

    def validar_excel(self):
        try:
            s = self.ctx.read_settings()
            df = cargar_excel(s.excel_file, s.excel_sheet_name, s.solo_primer_caso)
        except QAToolkitError as e:
            self.ctx.log.error("Excel inválido: %s", e)
            messagebox.showerror("Validar Excel", str(e))
            return
        self.ctx.log.info("Excel válido: %d casos listos para importar.", len(df))
        messagebox.showinfo("Validar Excel", f"Excel válido.\nCasos detectados: {len(df)}")

    def importar(self):
        try:
            s = self.ctx.read_settings()
            ImportadorTestCases.validar_config(s)
            client = self.ctx.build_client(s)
            df = cargar_excel(s.excel_file, s.excel_sheet_name, s.solo_primer_caso)
        except QAToolkitError as e:
            messagebox.showerror("Importar", str(e))
            return
        if not messagebox.askyesno(
            "Confirmar importación",
            f"Se van a procesar {len(df)} casos en:\n\nProyecto: {s.project}\n"
            f"Plan ID: {s.plan_id}\nSuite ID: {s.suite_id}\n\nEsto crea Work Items en Azure DevOps. ¿Continuar?",
        ):
            return
        importador = ImportadorTestCases(client, self.ctx.log)

        def ok(r):
            messagebox.showinfo(
                "Importación finalizada",
                f"Creados: {r.creados}\nReutilizados: {r.reutilizados}\n"
                f"Agregados a la suite: {r.agregados}\nErrores: {r.errores}",
            )

        self.ctx.run_task("Importar Test Cases", lambda token: importador.ejecutar(s, token), ok)
