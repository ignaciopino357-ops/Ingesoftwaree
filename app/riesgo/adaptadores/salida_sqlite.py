"""Módulo Motor de Riesgo · ADAPTADOR DE SALIDA: alertas en SQLite (HU-10 y HU-12)."""
from datetime import date
from typing import Optional

from app.compartido.db import conexion
from app.riesgo.puertos import Alerta, RepositorioAlertas

_SQL_ALERTA = """SELECT al.*, u.nombre AS alumno, c.id AS curso_id, c.nombre AS curso, c.profesor_id
                 FROM alertas al JOIN usuarios u ON u.id = al.alumno_id
                 LEFT JOIN alumnos_curso ac ON ac.alumno_id = al.alumno_id
                 LEFT JOIN cursos c ON c.id = ac.curso_id"""


def _a_alerta(f) -> Alerta:
    return Alerta(id=f["id"], alumno_id=f["alumno_id"], alumno=f["alumno"], curso_id=f["curso_id"],
                  curso=f["curso"], profesor_id=f["profesor_id"], tipo=f["tipo"], motivo=f["motivo"],
                  fecha=date.fromisoformat(f["fecha"]), revisada=bool(f["revisada"]))


class RepositorioAlertasSQLite(RepositorioAlertas):
    def crear(self, alumno_id: int, tipo: str, clave: str, motivo: str, fecha: date) -> bool:
        with conexion() as conn:
            cursor = conn.execute(
                """INSERT INTO alertas (alumno_id, tipo, clave, motivo, fecha) VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT (alumno_id, tipo, clave) DO NOTHING""",
                (alumno_id, tipo, clave, motivo, fecha.isoformat()))
            return cursor.rowcount == 1

    def pendientes(self, profesor_id: int) -> list[Alerta]:
        with conexion() as conn:
            filas = conn.execute(f"{_SQL_ALERTA} WHERE al.revisada = 0 AND c.profesor_id = ? "
                                 "ORDER BY al.fecha DESC, al.id DESC", (profesor_id,)).fetchall()
        return [_a_alerta(f) for f in filas]

    def obtener(self, alerta_id: int) -> Optional[Alerta]:
        with conexion() as conn:
            fila = conn.execute(f"{_SQL_ALERTA} WHERE al.id = ?", (alerta_id,)).fetchone()
        return _a_alerta(fila) if fila else None

    def marcar_revisada(self, alerta_id: int) -> None:
        with conexion() as conn:
            conn.execute("UPDATE alertas SET revisada = 1 WHERE id = ?", (alerta_id,))

    def ultimo_estado(self, alumno_id: int) -> Optional[str]:
        with conexion() as conn:
            fila = conn.execute("SELECT estado FROM ultimo_riesgo WHERE alumno_id = ?", (alumno_id,)).fetchone()
        return fila["estado"] if fila else None

    def guardar_estado(self, alumno_id: int, estado: str) -> None:
        with conexion() as conn:
            conn.execute("""INSERT INTO ultimo_riesgo (alumno_id, estado) VALUES (?, ?)
                            ON CONFLICT (alumno_id) DO UPDATE SET estado = excluded.estado""", (alumno_id, estado))
