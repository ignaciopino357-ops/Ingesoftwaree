"""HU-07: un caso por estado de riesgo más el caso sin datos."""
from app.riesgo import calcular_riesgo, porcentaje_asistencia, promedio_general


def test_bajo():
    assert calcular_riesgo(95.0, 5.5).estado == "Bajo"


def test_medio_por_asistencia():
    r = calcular_riesgo(80.0, 5.5)
    assert r.estado == "Medio"
    assert "Asistencia" in r.motivo


def test_medio_por_promedio():
    r = calcular_riesgo(92.0, 3.8)
    assert r.estado == "Medio"
    assert "Promedio" in r.motivo


def test_alto():
    r = calcular_riesgo(70.0, 3.5)
    assert r.estado == "Alto"
    assert "Asistencia" in r.motivo and "Promedio" in r.motivo


def test_sin_datos_no_es_alto():
    assert calcular_riesgo(None, None).estado == "Sin datos"


def test_umbrales_exactos_son_bajo():
    assert calcular_riesgo(85.0, 4.0).estado == "Bajo"


def test_solo_un_dato_disponible():
    assert calcular_riesgo(None, 3.0).estado == "Medio"
    assert calcular_riesgo(100.0, None).estado == "Bajo"


def test_justificado_cuenta_como_asistencia():
    # 8 presentes + 1 justificado de 10 días = 90 %
    assert porcentaje_asistencia(8, 1, 1) == 90.0
    assert porcentaje_asistencia(0, 0, 0) is None


def test_promedio_de_promedios():
    assert promedio_general({"Lenguaje": [4.0, 6.0], "Matemática": [3.0]}) == 4.0
    assert promedio_general({}) is None
