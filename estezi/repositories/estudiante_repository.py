# API/repositories/estudiante_repository.py
from database import obtener_conexion

class EstudianteRepository:
    @staticmethod
    def obtener_por_id(estudiante_id):
        con = obtener_conexion()
        est = con.execute("SELECT * FROM Estudiante WHERE id = ?", (estudiante_id,)).fetchone()
        if not est:
            con.close()
            return None
        curso = con.execute("SELECT * FROM Curso WHERE id = ?", (est["id_curso"],)).fetchone()
        registros = con.execute(
            "SELECT fecha, asistencia, nota FROM RegistroAcademico WHERE id_estudiante = ? ORDER BY fecha",
            (estudiante_id,),
        ).fetchall()
        con.close()
        return {"estudiante": dict(est), "curso": dict(curso) if curso else None,
                "registros": [dict(r) for r in registros]}

    @staticmethod
    def listar_alumnos_ejemplo():
        """Para el selector del login de alumno: id, nombre y curso."""
        con = obtener_conexion()
        filas = con.execute(
            "SELECT e.id, e.nombres, e.apellidos, c.nombre AS curso "
            "FROM Estudiante e JOIN Curso c ON c.id = e.id_curso ORDER BY e.id"
        ).fetchall()
        con.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_por_curso(curso_id):
        con = obtener_conexion()
        curso = con.execute("SELECT * FROM Curso WHERE id = ?", (curso_id,)).fetchone()
        if not curso:
            con.close()
            return None
        estudiantes = con.execute(
            "SELECT * FROM Estudiante WHERE id_curso = ?", (curso_id,)
        ).fetchall()
        resultado = []
        for e in estudiantes:
            regs = con.execute(
                "SELECT asistencia, nota FROM RegistroAcademico WHERE id_estudiante = ?", (e["id"],)
            ).fetchall()
            notas = [r["nota"] for r in regs if r["nota"] is not None]
            asis = [r["asistencia"] for r in regs if r["asistencia"] is not None]
            d = dict(e)
            d["promedio_notas"] = round(sum(notas) / len(notas), 1) if notas else None
            d["promedio_asistencia"] = round(sum(asis) / len(asis), 1) if asis else None
            resultado.append(d)
        con.close()
        return {"curso": dict(curso), "estudiantes": resultado}

    @staticmethod
    def obtener_estadisticas_curso(curso_id):
        """Tarea 2 (Back/BD): query agregada de promedio de notas y % asistencia por curso."""
        con = obtener_conexion()
        curso = con.execute("SELECT * FROM Curso WHERE id = ?", (curso_id,)).fetchone()
        if not curso:
            con.close()
            return None
        fila = con.execute(
            """
            SELECT
                ROUND(AVG(ra.nota), 1)        AS promedio_notas_curso,
                ROUND(AVG(ra.asistencia), 1)  AS porcentaje_asistencia_curso,
                COUNT(DISTINCT e.id)          AS total_estudiantes,
                COUNT(ra.id)                  AS total_registros
            FROM Estudiante e
            LEFT JOIN RegistroAcademico ra ON ra.id_estudiante = e.id
            WHERE e.id_curso = ?
            """,
            (curso_id,),
        ).fetchone()
        con.close()
        return {"curso": dict(curso), **dict(fila)}
