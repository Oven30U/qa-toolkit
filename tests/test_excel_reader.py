import pandas as pd
import pytest

from qa_toolkit.core.errors import ExcelError
from qa_toolkit.modules.testcase_importer.excel_reader import (
    COLUMNAS_REQUERIDAS,
    cargar_excel,
    construir_steps_xml,
    generar_plantilla,
    quitar_numeracion,
)


def test_quitar_numeracion():
    assert quitar_numeracion("1. Abrir") == "Abrir"
    assert quitar_numeracion("2) Abrir") == "Abrir"
    assert quitar_numeracion("Abrir") == "Abrir"


def test_steps_xml_empareja_y_escapa():
    xml = construir_steps_xml("1. A <b>\n2. B", "ok1")
    assert xml.count("<step ") == 2
    assert "A &lt;b&gt;" in xml
    assert 'last="3"' in xml


def test_steps_xml_sin_instrucciones_usa_paso_por_defecto():
    assert construir_steps_xml("", "").count("<step ") == 1


def test_plantilla_es_valida(tmp_path):
    ruta = tmp_path / "p.xlsx"
    generar_plantilla(str(ruta))
    df = cargar_excel(str(ruta), "Casos de prueba")
    assert list(df.columns) == COLUMNAS_REQUERIDAS and len(df) == 1


def _excel(tmp_path, filas, columnas=COLUMNAS_REQUERIDAS):
    ruta = tmp_path / "x.xlsx"
    pd.DataFrame(filas, columns=columnas).to_excel(ruta, sheet_name="Casos de prueba", index=False)
    return str(ruta)


def test_ids_duplicados(tmp_path):
    fila = ["CP-1"] + ["x"] * 6
    with pytest.raises(ExcelError, match="duplicados"):
        cargar_excel(_excel(tmp_path, [fila, fila]), "Casos de prueba")


def test_columnas_faltantes(tmp_path):
    with pytest.raises(ExcelError, match="Faltan columnas"):
        cargar_excel(_excel(tmp_path, [["a"]], ["ID caso de prueba"]), "Casos de prueba")


def test_archivo_inexistente():
    with pytest.raises(ExcelError, match="No se encontró"):
        cargar_excel("/no/existe.xlsx", "Casos de prueba")


def test_solo_primer_caso(tmp_path):
    filas = [[f"CP-{i}"] + ["x"] * 6 for i in range(3)]
    assert len(cargar_excel(_excel(tmp_path, filas), "Casos de prueba", True)) == 1
