"""Pruebas unitarias de las reglas nuevas del Sprint 3 (funciones puras, sin base de datos)."""
from datetime import date

import pytest

from app.academico.dominio import mes_siguiente, porcentaje_asistencia, promedio
from app.riesgo.dominio import debe_alertar_alto, rachas_de_ausencias, semanas_entre
from app.seguridad.dominio import validar_nuevo_usuario

D = date  # abreviatura para las listas de fechas


# ---------- HU-10: cuándo alertar por riesgo Alto ----------

@pytest.mark.parametrize("anterior, actual, alerta", [
    (None, "Alto", True),       # primera vez que se evalúa y ya está en Alto
    ("Medio", "Alto", True),    # entra a Alto
    ("Alto", "Alto", False),    # sigue en Alto: no se repite
    ("Alto", "Medio", False),   # baja
    ("Bajo", "Medio", False),   # empeora, pero no a Alto
])
def test_alerta_solo_al_entrar_a_alto(anterior, actual, alerta):
    assert debe_alertar_alto(anterior, actual) is alerta


# ---------- HU-12: ausencias seguidas ----------

def test_tres_ausencias_seguidas_forman_una_racha():
    registros = [(D(2026, 10, 5), "A"), (D(2026, 10, 6), "A"), (D(2026, 10, 7), "A")]
    assert rachas_de_ausencias(registros) == [[D(2026, 10, 5), D(2026, 10, 6), D(2026, 10, 7)]]


def test_fin_de_semana_y_feriado_no_cortan_la_racha():
    # Viernes 9, (fin de semana y lunes 12 feriado: sin registro), martes 13
    registros = [(D(2026, 10, 8), "A"), (D(2026, 10, 9), "A"), (D(2026, 10, 13), "A")]
    assert len(rachas_de_ausencias(registros)) == 1


@pytest.mark.parametrize("corte", ["P", "J"])
def test_presente_o_justificado_cortan_la_racha(corte):
    registros = [(D(2026, 10, 5), "A"), (D(2026, 10, 6), "A"), (D(2026, 10, 7), corte), (D(2026, 10, 8), "A")]
    assert rachas_de_ausencias(registros) == []


def test_dos_ausencias_no_alcanzan():
    assert rachas_de_ausencias([(D(2026, 10, 5), "A"), (D(2026, 10, 6), "A")]) == []


def test_registros_desordenados_y_dos_rachas_distintas():
    registros = [(D(2026, 10, 9), "A"), (D(2026, 10, 5), "A"), (D(2026, 10, 6), "A"), (D(2026, 10, 7), "A"),
                 (D(2026, 10, 8), "P"), (D(2026, 10, 13), "A"), (D(2026, 10, 14), "A")]
    rachas = rachas_de_ausencias(registros)
    assert [r[0] for r in rachas] == [D(2026, 10, 5), D(2026, 10, 9)]


# ---------- HU-13: semanas del historial ----------

def test_semanas_van_de_lunes_a_domingo():
    semanas = semanas_entre(D(2026, 7, 29), D(2026, 8, 10))  # miércoles a lunes
    assert semanas[0] == (D(2026, 7, 27), D(2026, 8, 2))
    assert semanas[-1] == (D(2026, 8, 10), D(2026, 8, 16))
    assert len(semanas) == 3


def test_sin_semanas_si_el_rango_esta_invertido():
    assert semanas_entre(D(2026, 8, 10), D(2026, 8, 1)) == []


# ---------- HU-09 / HU-16: utilidades académicas ----------

def test_promedio_por_asignatura():
    assert promedio([5.0, 6.0, 6.5]) == 5.8
    assert promedio([]) is None


def test_porcentaje_asistencia_se_comparte_con_el_motor_de_riesgo():
    from app.riesgo import dominio as riesgo
    assert riesgo.porcentaje_asistencia is porcentaje_asistencia


@pytest.mark.parametrize("anio, mes, paso, esperado", [(2026, 12, 1, (2027, 1)), (2026, 1, -1, (2025, 12)),
                                                       (2026, 7, 5, (2026, 12))])
def test_mes_siguiente(anio, mes, paso, esperado):
    assert mes_siguiente(anio, mes, paso) == esperado


# ---------- HU-11: validar datos del nuevo usuario ----------

def test_datos_correctos_no_tienen_errores():
    assert validar_nuevo_usuario("Nora Paz", "npaz", "secreto1", "alumno") == {}


@pytest.mark.parametrize("nombre, usuario, clave, rol, campo", [
    ("", "npaz", "secreto1", "alumno", "nombre"),
    ("Nora Paz", "n paz", "secreto1", "alumno", "usuario"),   # con espacio
    ("Nora Paz", "ñandú", "secreto1", "alumno", "usuario"),   # con tilde/ñ
    ("Nora Paz", "np", "secreto1", "alumno", "usuario"),      # muy corto
    ("Nora Paz", "npaz", "12345", "alumno", "clave"),         # menos de 6
    ("Nora Paz", "npaz", "secreto1", "directiva", "rol"),     # la directiva no se registra aquí
])
def test_cada_dato_invalido_marca_su_campo(nombre, usuario, clave, rol, campo):
    assert campo in validar_nuevo_usuario(nombre, usuario, clave, rol)
