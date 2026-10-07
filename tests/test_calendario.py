"""HU-03: días de clases con feriados y semestre."""
from datetime import date

from app.calendario import dias_de_clases, es_dia_de_clases, motivo_no_clases

FERIADOS = {date(2026, 10, 12): "Encuentro de Dos Mundos"}


def test_semana_con_feriado_tiene_4_dias():
    # Lunes 12 al domingo 18 de octubre de 2026; el lunes es feriado
    dias = dias_de_clases(date(2026, 10, 12), date(2026, 10, 18), FERIADOS)
    assert len(dias) == 4
    assert date(2026, 10, 12) not in dias


def test_fin_de_semana_no_es_clases():
    assert motivo_no_clases(date(2026, 10, 10), None, None, {}) == "Es fin de semana"


def test_feriado_bloqueado_con_su_nombre():
    assert "Encuentro de Dos Mundos" in motivo_no_clases(date(2026, 10, 12), None, None, FERIADOS)


def test_fuera_del_semestre():
    inicio, fin = date(2026, 7, 27), date(2026, 12, 4)
    assert not es_dia_de_clases(date(2026, 12, 7), inicio, fin, {})
    assert es_dia_de_clases(date(2026, 10, 13), inicio, fin, FERIADOS)


def test_sin_semestre_solo_bloquea_fines_de_semana():
    assert es_dia_de_clases(date(2026, 1, 5), None, None, {})
