"""Pruebas unitarias del Motor de Riesgo (HU-07). Patrón Arrange-Act-Assert.

No necesitan base de datos ni FastAPI: es el beneficio de tener el dominio aislado.
"""
import pytest

from app.riesgo.dominio import calcular_riesgo, porcentaje_asistencia, promedio_general


# 1. Caso normal + regla: los cuatro estados en una sola prueba parametrizada
@pytest.mark.parametrize(
    "asistencia, promedio, esperado",
    [
        (95.0, 5.5, "Bajo"),    # cumple ambas
        (80.0, 5.5, "Medio"),   # falla solo la asistencia
        (92.0, 3.8, "Medio"),   # falla solo el promedio
        (70.0, 3.5, "Alto"),    # fallan ambas
        (None, None, "Sin datos"),
    ],
)
def test_clasifica_cada_estado(asistencia, promedio, esperado):
    # Act
    resultado = calcular_riesgo(asistencia, promedio)
    # Assert
    assert resultado.estado == esperado


# 2. Caso límite: justo en los umbrales el alumno NO está en riesgo
def test_umbral_exacto_es_bajo():
    assert calcular_riesgo(85.0, 4.0).estado == "Bajo"


@pytest.mark.parametrize("asistencia, promedio", [(84.9, 4.0), (85.0, 3.9)])
def test_bajo_el_umbral_por_una_decima_es_medio(asistencia, promedio):
    assert calcular_riesgo(asistencia, promedio).estado == "Medio"


# 3. Excepción: datos imposibles se rechazan
@pytest.mark.parametrize("asistencia, promedio", [(-1, 5.0), (101, 5.0), (90, 0.5), (90, 7.5)])
def test_valores_fuera_de_rango_lanzan_error(asistencia, promedio):
    with pytest.raises(ValueError):
        calcular_riesgo(asistencia, promedio)


# 4. Regla: el motivo explica por qué y el semáforo coincide con el estado
def test_motivo_y_semaforo_del_riesgo_alto():
    # Arrange
    asistencia, promedio = 70.0, 3.5
    # Act
    resultado = calcular_riesgo(asistencia, promedio)
    # Assert
    assert "Asistencia bajo 85 %" in resultado.motivo
    assert "Promedio bajo 4.0" in resultado.motivo
    assert resultado.semaforo == "Rojo"


def test_solo_con_un_dato_se_evalua_ese_dato():
    assert calcular_riesgo(None, 3.0).estado == "Medio"
    assert calcular_riesgo(100.0, None).estado == "Bajo"


# 5. Comportamiento propio: cálculo del % de asistencia y del promedio
def test_justificado_cuenta_como_asistencia():
    # 8 presentes + 1 justificado de 10 días = 90 %
    assert porcentaje_asistencia(8, 1, 1) == 90.0


def test_sin_dias_registrados_no_hay_porcentaje():
    assert porcentaje_asistencia(0, 0, 0) is None


def test_conteo_negativo_lanza_error():
    with pytest.raises(ValueError, match="negativos"):
        porcentaje_asistencia(-1, 0, 0)


def test_promedio_de_promedios_por_asignatura():
    # Lenguaje promedia 5.0 y Matemática 3.0 -> 4.0 (no 4.33 como sería el promedio simple)
    assert promedio_general({"Lenguaje": [4.0, 6.0], "Matemática": [3.0]}) == pytest.approx(4.0)
    assert promedio_general({}) is None
