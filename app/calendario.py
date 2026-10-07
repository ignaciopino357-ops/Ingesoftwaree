"""HU-03: días de clases según el semestre y los feriados.

Un día es de clases si:
  - es de lunes a viernes,
  - no es feriado,
  - está dentro del semestre (si la directiva ya lo configuró).
Mientras no haya semestre configurado, solo se bloquean sábados y domingos.
"""
import calendar
from datetime import date, timedelta
from typing import Iterable, Optional

NOMBRES_MES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def motivo_no_clases(
    dia: date,
    inicio: Optional[date],
    fin: Optional[date],
    feriados: dict,
) -> Optional[str]:
    """Devuelve por qué un día NO es de clases, o None si sí lo es."""
    if dia.weekday() >= 5:
        return "Es fin de semana"
    if dia in feriados:
        return f"Es feriado: {feriados[dia]}"
    if inicio and dia < inicio:
        return "Es antes del inicio del semestre"
    if fin and dia > fin:
        return "Es después del fin del semestre"
    return None


def es_dia_de_clases(dia: date, inicio: Optional[date], fin: Optional[date], feriados: dict) -> bool:
    return motivo_no_clases(dia, inicio, fin, feriados) is None


def dias_de_clases(inicio: date, fin: date, feriados: Iterable[date]) -> list:
    """Lista de días de clases entre inicio y fin (ambos incluidos)."""
    feriados = set(feriados)
    dias = []
    dia = inicio
    while dia <= fin:
        if dia.weekday() < 5 and dia not in feriados:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def semanas_del_mes(anio: int, mes: int) -> list:
    """Matriz de semanas (lunes a domingo) con fechas o None, para dibujar el calendario."""
    cal = calendar.Calendar(firstweekday=0)
    return [
        [date(anio, mes, d) if d else None for d in semana]
        for semana in cal.monthdayscalendar(anio, mes)
    ]
