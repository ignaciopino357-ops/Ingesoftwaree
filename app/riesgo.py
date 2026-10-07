"""HU-07: cálculo del estado de riesgo de deserción.

Regla simple y explicable:
  - Bajo:  asistencia >= 85 % y promedio >= 4.0
  - Medio: falla solo una de las dos condiciones
  - Alto:  fallan ambas
  - Sin datos: el alumno no tiene notas ni asistencia registradas

Los umbrales son constantes para que sea fácil cambiarlos.
"""
from dataclasses import dataclass
from typing import Optional

UMBRAL_ASISTENCIA = 85.0  # porcentaje
UMBRAL_PROMEDIO = 4.0

# Orden usado para ordenar la tabla del curso (más riesgo primero)
ORDEN_RIESGO = {"Alto": 0, "Medio": 1, "Bajo": 2, "Sin datos": 3}


@dataclass
class Riesgo:
    estado: str  # "Bajo", "Medio", "Alto" o "Sin datos"
    motivo: str


def calcular_riesgo(asistencia: Optional[float], promedio: Optional[float]) -> Riesgo:
    """Clasifica a un alumno. Si falta uno de los dos datos, se evalúa solo el otro."""
    if asistencia is None and promedio is None:
        return Riesgo("Sin datos", "Aún no hay notas ni asistencia registradas")

    fallas = []
    if asistencia is not None and asistencia < UMBRAL_ASISTENCIA:
        fallas.append(f"Asistencia bajo {UMBRAL_ASISTENCIA:g} %")
    if promedio is not None and promedio < UMBRAL_PROMEDIO:
        fallas.append(f"Promedio bajo {UMBRAL_PROMEDIO:.1f}")

    if len(fallas) == 0:
        return Riesgo("Bajo", "Asistencia y promedio sobre el umbral")
    if len(fallas) == 1:
        return Riesgo("Medio", fallas[0])
    return Riesgo("Alto", " y ".join(fallas))


def porcentaje_asistencia(presentes: int, ausentes: int, justificados: int) -> Optional[float]:
    """HU-06: % de asistencia = (Presente + Justificado) / días registrados."""
    total = presentes + ausentes + justificados
    if total == 0:
        return None
    return round((presentes + justificados) * 100 / total, 1)


def promedio_general(notas_por_asignatura: dict) -> Optional[float]:
    """Promedio de los promedios por asignatura, redondeado a 1 decimal."""
    promedios = [sum(n) / len(n) for n in notas_por_asignatura.values() if n]
    if not promedios:
        return None
    return round(sum(promedios) / len(promedios), 1)
