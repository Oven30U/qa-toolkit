from qa_toolkit.modules.base import ModuleSpec

SPEC = ModuleSpec(
    id="testplan_reports",
    title="Reportes Test Plans",
    description="Descarga los resultados de los Test Plans a Excel para Power BI.",
    view_path="qa_toolkit.modules.testplan_reports.view:ReportsView",
)
