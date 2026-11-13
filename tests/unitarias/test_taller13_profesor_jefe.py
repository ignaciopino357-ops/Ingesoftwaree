"""Regresión de BUG-01 y BUG-02 (taller semana 13): el profesor jefe debe existir y tener rol profesor."""
import pytest

from app.academico.casos_uso import AdministrarCursos
from app.compartido.errores import DatosInvalidos, NoEncontrado
from tests.unitarias.test_casos_uso import CursosFalsos


def test_bug01_alumno_no_puede_ser_profesor_jefe_al_crear():
    cursos = CursosFalsos()
    with pytest.raises(DatosInvalidos):
        AdministrarCursos(cursos).crear("4° Medio Z", 10)
    assert not cursos.existe_nombre("4° Medio Z")


def test_bug01_alumno_no_puede_ser_profesor_jefe_al_reasignar():
    cursos = CursosFalsos()
    with pytest.raises(DatosInvalidos):
        AdministrarCursos(cursos).asignar_profesor(1, 11)
    assert cursos.obtener(1).profesor_id == 2


def test_directiva_tampoco_puede_ser_profesor_jefe():
    with pytest.raises(DatosInvalidos):
        AdministrarCursos(CursosFalsos()).crear("4° Medio Z", 1)


def test_bug02_profesor_inexistente_es_no_encontrado():
    with pytest.raises(NoEncontrado):
        AdministrarCursos(CursosFalsos()).crear("4° Medio Y", 999)
    with pytest.raises(NoEncontrado):
        AdministrarCursos(CursosFalsos()).asignar_profesor(1, 999)


def test_profesor_id_no_numerico_es_dato_invalido():
    with pytest.raises(DatosInvalidos):
        AdministrarCursos(CursosFalsos()).crear("4° Medio X", "abc")


@pytest.mark.parametrize("profesor_id", [3, "3"])
def test_profesor_valido_se_acepta_como_numero_o_texto(profesor_id):
    cursos = CursosFalsos()
    nuevo = AdministrarCursos(cursos).crear("4° Medio A", profesor_id)
    assert cursos.obtener(nuevo).profesor_id == 3


@pytest.mark.parametrize("vacio", [None, ""])
def test_curso_sin_profesor_jefe_sigue_permitido(vacio):
    cursos = CursosFalsos()
    nuevo = AdministrarCursos(cursos).crear("4° Medio B", vacio)
    assert cursos.obtener(nuevo).profesor_id is None
