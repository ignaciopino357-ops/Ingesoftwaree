"""Módulo Motor de Riesgo · ADAPTADOR DE ENTRADA desde Gestión Académica.

Implementa el puerto ObservadorCambios de Gestión Académica: cada vez que se guardan notas
o asistencia de un curso, revisa ese curso y crea las alertas de HU-10 y HU-12.
Así Gestión Académica no depende del Motor de Riesgo (solo conoce su propio puerto).
"""
from datetime import date

from app.academico.puertos import ObservadorCambios
from app.riesgo.casos_uso import VigilarRiesgo


class RevisarAlertasAlGuardar(ObservadorCambios):
    def __init__(self, vigilar: VigilarRiesgo):
        self.vigilar = vigilar

    def datos_actualizados(self, curso_id: int, hoy: date) -> None:
        self.vigilar.revisar_curso(curso_id, hoy)
