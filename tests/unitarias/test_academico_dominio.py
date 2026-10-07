"""Pruebas unitarias del dominio de Gestión Académica: notas (HU-05) y calendario (HU-03)."""
from datetime import date

import pytest

from app.academico.dominio import (
    EstadoAsistencia, dias_de_clases, es_dia_de_clases, motivo_bloqueo_asistencia, motivo_no_clases,
    validar_nota, validar_semestre,
)

FERIADOS = {date(2026, 10, 12): "Encuentro de Dos Mundos"}


# ---------- Notas ----------

@pytest.mark.parametrize("entrada, esperado", [("6,5", 6.5), ("4.0", 4.0), (7, 7.0), (" 1,0 ", 1.0), (5, 5.0)])
def test_validar_nota_acepta_coma_o_punto(entrada, esperado):
    assert validar_nota(entrada) == esperado


@pytest.mark.parametrize("entrada", ["0.9", "7.1", "8", "-3"])
def test_nota_fuera_de_rango_lanza_error(entrada):
    with pytest.raises(ValueError, match="entre 1.0 y 7.0"):
        validar_nota(entrada)


@pytest.mark.parametrize("entrada", ["abc", "", None])
def test_nota_que_no_es_numero_lanza_error(entrada):
    with pytest.raises(ValueError, match="No es un número"):
        validar_nota(entrada)


def test_estado_de_asistencia_invalido():
    assert EstadoAsistencia("J").texto == "Justificado"
    with pytest.raises(ValueError):
        EstadoAsistencia("X")


# ---------- Calendario ----------

def test_semana_con_feriado_tiene_4_dias_de_clases():
    # Lunes 12 al domingo 18 de octubre de 2026; el lunes es feriado
    dias = dias_de_clases(date(2026, 10, 12), date(2026, 10, 18), FERIADOS)
    assert len(dias) == 4
    assert date(2026, 10, 12) not in dias


def test_feriado_bloqueado_con_su_nombre():
    assert "Encuentro de Dos Mundos" in motivo_no_clases(date(2026, 10, 12), None, None, FERIADOS)


def test_fin_de_semana_no_es_dia_de_clases():
    assert motivo_no_clases(date(2026, 10, 10), None, None, {}) == "Es fin de semana"


def test_fuera_del_semestre():
    inicio, fin = date(2026, 7, 27), date(2026, 12, 4)
    assert not es_dia_de_clases(date(2026, 12, 7), inicio, fin, {})
    assert es_dia_de_clases(date(2026, 10, 13), inicio, fin, FERIADOS)


def test_sin_semestre_solo_bloquea_fines_de_semana():
    assert es_dia_de_clases(date(2026, 1, 5), None, None, {})


def test_no_se_pasa_lista_en_dias_futuros():
    motivo = motivo_bloqueo_asistencia(date(2026, 10, 9), hoy=date(2026, 10, 8), inicio=None, fin=None, feriados={})
    assert "futuro" in motivo


def test_semestre_con_fechas_invertidas_lanza_error():
    with pytest.raises(ValueError, match="anterior"):
        validar_semestre(date(2026, 12, 1), date(2026, 8, 1))
