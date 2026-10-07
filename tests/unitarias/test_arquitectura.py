"""Prueba de arquitectura: protege la regla de dependencias del Hito 1.

El dominio y los casos de uso NO pueden depender de frameworks ni de la base de datos.
Si alguien importa FastAPI o sqlite3 en el núcleo, esta prueba falla.
"""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"
MODULOS = ["seguridad", "academico", "riesgo"]
NUCLEO = [APP / m / archivo for m in MODULOS for archivo in ("dominio.py", "puertos.py", "casos_uso.py")
          if (APP / m / archivo).exists()]
PROHIBIDOS = ("fastapi", "starlette", "sqlite3", "openpyxl", "jinja2", "app.compartido.db")


def _importaciones(archivo: Path) -> set:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


@pytest.mark.parametrize("archivo", NUCLEO, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_el_nucleo_no_depende_de_infraestructura(archivo):
    importados = _importaciones(archivo)
    prohibidos = {i for i in importados if i.startswith(PROHIBIDOS) or ".adaptadores" in i}
    assert not prohibidos, f"{archivo.name} importa infraestructura: {prohibidos}"


def test_cada_modulo_tiene_sus_capas():
    for modulo in MODULOS:
        for parte in ("dominio.py", "casos_uso.py", "adaptadores"):
            assert (APP / modulo / parte).exists(), f"Falta {modulo}/{parte}"
