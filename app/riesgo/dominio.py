"""Módulo Motor de Riesgo · DOMINIO (HU-07).

El activo central del sistema según el Hito 1. Funciones puras: sin base de datos,
sin FastAPI, sin archivos. Por eso se prueban con pruebas unitarias simples.

Regla (umbrales en constantes para poder calibrarlos sin tocar nada más):
  - Bajo  (Verde):    asistencia >= 85 % y promedio >= 4.0
  - Medio (Amarillo): falla solo una de las dos condiciones
  - Alto  (Rojo):     fallan ambas
  - Sin datos:        no hay notas ni asistencia registradas
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

# El % de asistencia es una regla académica: el Motor de Riesgo la reutiliza
# (dependencia permitida Motor de Riesgo -> Gestión Académica, Hito 1).
from app.academico.dominio import porcentaje_asistencia  # noqa: F401

UMBRAL_ASISTENCIA = 85.0  # porcentaje
UMBRAL_PROMEDIO = 4.0

SEMAFORO = {"Bajo": "Verde", "Medio": "Amarillo", "Alto": "Rojo", "Sin datos": "Gris"}
ORDEN_RIESGO = {"Alto": 0, "Medio": 1, "Bajo": 2, "Sin datos": 3}


@dataclass(frozen=True)
class EvaluacionRiesgo:
    estado: str   # "Bajo", "Medio", "Alto" o "Sin datos"
    motivo: str

    @property
    def semaforo(self) -> str:
        return SEMAFORO[self.estado]


def calcular_riesgo(asistencia: Optional[float], promedio: Optional[float]) -> EvaluacionRiesgo:
    """Clasifica a un alumno. Si falta uno de los dos datos, se evalúa solo el otro.

    Lanza ValueError si la asistencia no está entre 0 y 100 o el promedio entre 1.0 y 7.0.
    """
    if asistencia is not None and not 0 <= asistencia <= 100:
        raise ValueError("La asistencia debe estar entre 0 y 100")
    if promedio is not None and not 1.0 <= promedio <= 7.0:
        raise ValueError("El promedio debe estar entre 1.0 y 7.0")
    if asistencia is None and promedio is None:
        return EvaluacionRiesgo("Sin datos", "Aún no hay notas ni asistencia registradas")

    fallas = []
    if asistencia is not None and asistencia < UMBRAL_ASISTENCIA:
        fallas.append(f"Asistencia bajo {UMBRAL_ASISTENCIA:g} %")
    if promedio is not None and promedio < UMBRAL_PROMEDIO:
        fallas.append(f"Promedio bajo {UMBRAL_PROMEDIO:.1f}")

    if not fallas:
        return EvaluacionRiesgo("Bajo", "Asistencia y promedio sobre el umbral")
    if len(fallas) == 1:
        return EvaluacionRiesgo("Medio", fallas[0])
    return EvaluacionRiesgo("Alto", " y ".join(fallas))


def promedio_general(notas_por_asignatura: dict) -> Optional[float]:
    """Promedio de los promedios por asignatura, redondeado a 1 decimal."""
    promedios = [sum(n) / len(n) for n in notas_por_asignatura.values() if n]
    if not promedios:
        return None
    return round(sum(promedios) / len(promedios), 1)


# ---------- Alertas (HU-10 y HU-12) ----------

AUSENCIAS_SEGUIDAS = 3


def debe_alertar_alto(anterior: Optional[str], actual: str) -> bool:
    """HU-10: se alerta solo cuando el alumno ENTRA a riesgo Alto.

    Si ya estaba en Alto no se repite; si bajó y vuelve a subir, se alerta de nuevo.
    """
    return actual == "Alto" and anterior != "Alto"


def rachas_de_ausencias(registros: list, minimo: int = AUSENCIAS_SEGUIDAS) -> list:
    """HU-12: rachas de al menos `minimo` ausencias (A) seguidas.

    `registros` = [(date, estado)] de días con lista pasada. Solo se pasa lista en días de clases,
    así que fines de semana y feriados no aparecen: ni cortan ni suman a la racha.
    Un día P o J corta la racha. Devuelve una lista de rachas, cada una con sus fechas en orden.
    """
    rachas, actual = [], []
    for dia, estado in sorted(registros):
        if estado == "A":
            actual.append(dia)
        else:
            if len(actual) >= minimo:
                rachas.append(actual)
            actual = []
    if len(actual) >= minimo:
        rachas.append(actual)
    return rachas


# ---------- Historial (HU-13) ----------

def semanas_entre(inicio: date, hasta: date) -> list:
    """Semanas (lunes, domingo) desde la semana de `inicio` hasta la semana de `hasta`."""
    if hasta < inicio:
        return []
    lunes = inicio - timedelta(days=inicio.weekday())
    semanas = []
    while lunes <= hasta:
        semanas.append((lunes, lunes + timedelta(days=6)))
        lunes += timedelta(days=7)
    return semanas
