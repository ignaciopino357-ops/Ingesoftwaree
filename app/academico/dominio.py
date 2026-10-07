"""Módulo Gestión Académica · DOMINIO.

Entidades y reglas puras: notas, asistencia y calendario del semestre.
Solo Python estándar: no importa FastAPI ni la base de datos.
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Iterable, Optional

NOTA_MINIMA = 1.0
NOTA_MAXIMA = 7.0
NUM_EVALUACIONES = 6

NOMBRES_MES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


@dataclass(frozen=True)
class Curso:
    id: int
    nombre: str
    profesor_id: Optional[int]
    profesor: Optional[str]


@dataclass(frozen=True)
class Alumno:
    id: int
    nombre: str


class EstadoAsistencia(str, Enum):
    PRESENTE = "P"
    AUSENTE = "A"
    JUSTIFICADO = "J"

    @property
    def texto(self) -> str:
        return {"P": "Presente", "A": "Ausente", "J": "Justificado"}[self.value]


# ---------- Notas (HU-05) ----------

def validar_nota(valor) -> float:
    """Convierte y valida una nota chilena. Acepta coma o punto.

    Lanza ValueError si no es un número o si está fuera de 1.0–7.0.
    """
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    try:
        nota = round(float(valor), 1)
    except (TypeError, ValueError):
        raise ValueError("No es un número")
    if not NOTA_MINIMA <= nota <= NOTA_MAXIMA:
        raise ValueError(f"Debe estar entre {NOTA_MINIMA} y {NOTA_MAXIMA}")
    return nota


def validar_numero_evaluacion(numero: int) -> int:
    if not 1 <= numero <= NUM_EVALUACIONES:
        raise ValueError(f"La evaluación debe ser de 1 a {NUM_EVALUACIONES}")
    return numero


# ---------- Calendario (HU-03) ----------

def validar_semestre(inicio: date, fin: date) -> None:
    if fin < inicio:
        raise ValueError("La fecha de término es anterior a la de inicio")


def motivo_no_clases(dia: date, inicio: Optional[date], fin: Optional[date], feriados: dict) -> Optional[str]:
    """Devuelve por qué un día NO es de clases, o None si sí lo es.

    Mientras no haya semestre configurado, solo se bloquean sábados y domingos.
    """
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
    dias, dia = [], inicio
    while dia <= fin:
        if dia.weekday() < 5 and dia not in feriados:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def motivo_bloqueo_asistencia(dia: date, hoy: date, inicio, fin, feriados: dict) -> Optional[str]:
    """HU-06: no se puede pasar lista en días futuros ni en días sin clases."""
    if dia > hoy:
        return "No se puede registrar asistencia de un día futuro"
    return motivo_no_clases(dia, inicio, fin, feriados)


def semanas_del_mes(anio: int, mes: int) -> list:
    """Matriz de semanas (lunes a domingo) con fechas o None, para dibujar el calendario."""
    return [
        [date(anio, mes, d) if d else None for d in semana]
        for semana in calendar.Calendar(firstweekday=0).monthdayscalendar(anio, mes)
    ]
