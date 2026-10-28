from qa_toolkit.modules.base import ModuleSpec

SPEC = ModuleSpec(
    id="testcase_importer",
    title="Importar Test Cases",
    description="Carga casos de prueba desde un Excel a un Test Plan / Suite de Azure DevOps.",
    view_path="qa_toolkit.modules.testcase_importer.view:ImporterView",
)
