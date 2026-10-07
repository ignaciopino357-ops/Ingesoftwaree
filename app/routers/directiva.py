"""Portal directiva.

HU-02 asignar alumnos y profesor jefe a cursos · HU-03 configurar calendario del semestre
"""
import sqlite3
from datetime import date

from fastapi import APIRouter, HTTPException, Request

from app import consultas
from app.auth import exigir_rol
from app.calendario import NOMBRES_MES, dias_de_clases, motivo_no_clases, semanas_del_mes
from app.db import conexion
from app.web import avisar, ir_a, render

router = APIRouter(prefix="/directiva")


def _profesores() -> list:
    with conexion() as conn:
        return [dict(f) for f in conn.execute(
            "SELECT id, nombre FROM usuarios WHERE rol = 'profesor' ORDER BY nombre")]


# ---------- HU-02: cursos ----------

@router.get("")
def portal_directiva(request: Request):
    exigir_rol(request, "directiva")
    with conexion() as conn:
        cursos = [dict(f) for f in conn.execute(
            """SELECT c.id, c.nombre, u.nombre AS profesor,
                      (SELECT COUNT(*) FROM alumnos_curso ac WHERE ac.curso_id = c.id) AS alumnos
               FROM cursos c LEFT JOIN usuarios u ON u.id = c.profesor_id
               ORDER BY c.nombre""")]
        sin_curso = conn.execute(
            """SELECT COUNT(*) FROM usuarios u WHERE u.rol = 'alumno'
               AND u.id NOT IN (SELECT alumno_id FROM alumnos_curso)""").fetchone()[0]
    return render(request, "directiva/portal.html", cursos=cursos,
                  profesores=_profesores(), sin_curso=sin_curso)


@router.post("/cursos")
async def crear_curso(request: Request):
    exigir_rol(request, "directiva")
    form = await request.form()
    nombre = (form.get("nombre") or "").strip()
    profesor_id = form.get("profesor_id") or None
    if not nombre:
        avisar(request, "Escriba el nombre del curso.", "error")
        return ir_a("/directiva")
    try:
        with conexion() as conn:
            curso_id = conn.execute(
                "INSERT INTO cursos (nombre, profesor_id) VALUES (?, ?)", (nombre, profesor_id)
            ).lastrowid
    except sqlite3.IntegrityError:
        avisar(request, f"Ya existe un curso llamado {nombre}.", "error")
        return ir_a("/directiva")
    avisar(request, f"Curso {nombre} creado.")
    return ir_a(f"/directiva/cursos/{curso_id}")


@router.get("/cursos/{curso_id}")
def ver_curso(request: Request, curso_id: int):
    exigir_rol(request, "directiva")
    curso = consultas.obtener_curso(curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="El curso no existe")
    with conexion() as conn:
        todos = [dict(f) for f in conn.execute(
            """SELECT u.id, u.nombre, c.nombre AS curso FROM usuarios u
               LEFT JOIN alumnos_curso ac ON ac.alumno_id = u.id
               LEFT JOIN cursos c ON c.id = ac.curso_id
               WHERE u.rol = 'alumno' ORDER BY c.nombre IS NOT NULL, u.nombre""")]
    return render(request, "directiva/curso.html", curso=curso,
                  alumnos=consultas.alumnos_del_curso(curso_id),
                  disponibles=[a for a in todos if a["curso"] != curso["nombre"]],
                  profesores=_profesores())


@router.post("/cursos/{curso_id}/profesor")
async def cambiar_profesor(request: Request, curso_id: int):
    exigir_rol(request, "directiva")
    form = await request.form()
    with conexion() as conn:
        conn.execute("UPDATE cursos SET profesor_id = ? WHERE id = ?",
                     (form.get("profesor_id") or None, curso_id))
    avisar(request, "Profesor jefe actualizado.")
    return ir_a(f"/directiva/cursos/{curso_id}")


@router.post("/cursos/{curso_id}/alumnos")
async def agregar_alumno(request: Request, curso_id: int):
    exigir_rol(request, "directiva")
    form = await request.form()
    alumno_id = int(form.get("alumno_id"))
    with conexion() as conn:
        actual = conn.execute(
            """SELECT c.nombre FROM alumnos_curso ac JOIN cursos c ON c.id = ac.curso_id
               WHERE ac.alumno_id = ?""", (alumno_id,)).fetchone()
        if actual:
            # HU-02, criterio 3: un alumno pertenece a un solo curso
            avisar(request, f"No se guardó: el alumno ya pertenece a {actual['nombre']}. "
                            "Quítelo de ese curso primero.", "error")
            return ir_a(f"/directiva/cursos/{curso_id}")
        conn.execute("INSERT INTO alumnos_curso (alumno_id, curso_id) VALUES (?, ?)",
                     (alumno_id, curso_id))
    avisar(request, "Alumno agregado al curso.")
    return ir_a(f"/directiva/cursos/{curso_id}")


@router.post("/cursos/{curso_id}/alumnos/{alumno_id}/quitar")
def quitar_alumno(request: Request, curso_id: int, alumno_id: int):
    exigir_rol(request, "directiva")
    with conexion() as conn:
        conn.execute("DELETE FROM alumnos_curso WHERE alumno_id = ? AND curso_id = ?",
                     (alumno_id, curso_id))
    avisar(request, "Alumno quitado del curso. Sus notas y asistencia se conservan.")
    return ir_a(f"/directiva/cursos/{curso_id}")


# ---------- HU-03: calendario del semestre ----------

@router.get("/calendario")
def ver_calendario(request: Request, mes: str = ""):
    exigir_rol(request, "directiva")
    inicio, fin = consultas.obtener_semestre()
    feriados = consultas.obtener_feriados()
    try:
        anio, num_mes = (int(x) for x in mes.split("-"))
        date(anio, num_mes, 1)
    except ValueError:
        hoy = date.today()
        anio, num_mes = hoy.year, hoy.month

    semanas = []
    for semana in semanas_del_mes(anio, num_mes):
        fila = []
        for dia in semana:
            if dia is None:
                fila.append(None)
                continue
            motivo = motivo_no_clases(dia, inicio, fin, feriados)
            if motivo is None:
                tipo = "clases"
            elif dia in feriados:
                tipo = "feriado"
            elif dia.weekday() >= 5:
                tipo = "finde"
            else:
                tipo = "fuera"
            fila.append({"dia": dia, "tipo": tipo, "titulo": motivo or "Día de clases"})
        semanas.append(fila)

    anterior = f"{anio - 1}-12" if num_mes == 1 else f"{anio}-{num_mes - 1:02d}"
    siguiente = f"{anio + 1}-01" if num_mes == 12 else f"{anio}-{num_mes + 1:02d}"
    total_clases = len(dias_de_clases(inicio, fin, feriados)) if inicio else None
    return render(
        request, "directiva/calendario.html", inicio=inicio, fin=fin,
        feriados=sorted(feriados.items()), semanas=semanas,
        titulo_mes=f"{NOMBRES_MES[num_mes - 1]} {anio}",
        anterior=anterior, siguiente=siguiente, total_clases=total_clases,
    )


@router.post("/calendario/semestre")
async def guardar_semestre(request: Request):
    exigir_rol(request, "directiva")
    form = await request.form()
    try:
        inicio = date.fromisoformat(form.get("inicio", ""))
        fin = date.fromisoformat(form.get("fin", ""))
    except ValueError:
        avisar(request, "Ingrese ambas fechas.", "error")
        return ir_a("/directiva/calendario")
    if fin < inicio:
        # HU-03, criterio 1
        avisar(request, "No se guardó: la fecha de término es anterior a la de inicio.", "error")
        return ir_a("/directiva/calendario")
    with conexion() as conn:
        conn.execute(
            """INSERT INTO semestre (id, inicio, fin) VALUES (1, ?, ?)
               ON CONFLICT (id) DO UPDATE SET inicio = excluded.inicio, fin = excluded.fin""",
            (inicio.isoformat(), fin.isoformat()),
        )
    avisar(request, "Semestre guardado.")
    return ir_a(f"/directiva/calendario?mes={inicio.year}-{inicio.month:02d}")


@router.post("/calendario/feriados")
async def agregar_feriado(request: Request):
    exigir_rol(request, "directiva")
    form = await request.form()
    nombre = (form.get("nombre") or "").strip()
    try:
        fecha = date.fromisoformat(form.get("fecha", ""))
    except ValueError:
        fecha = None
    if fecha is None or not nombre:
        avisar(request, "Ingrese la fecha y el nombre del feriado.", "error")
        return ir_a("/directiva/calendario")
    with conexion() as conn:
        conn.execute(
            """INSERT INTO feriados (fecha, nombre) VALUES (?, ?)
               ON CONFLICT (fecha) DO UPDATE SET nombre = excluded.nombre""",
            (fecha.isoformat(), nombre),
        )
    aviso = f"Feriado {nombre} agregado."
    if fecha.weekday() >= 5:
        aviso += " Cae en fin de semana, así que no cambia los días de clases."
    avisar(request, aviso)
    return ir_a(f"/directiva/calendario?mes={fecha.year}-{fecha.month:02d}")


@router.post("/calendario/feriados/{fecha}/eliminar")
def eliminar_feriado(request: Request, fecha: str):
    exigir_rol(request, "directiva")
    with conexion() as conn:
        conn.execute("DELETE FROM feriados WHERE fecha = ?", (fecha,))
    avisar(request, "Feriado eliminado.")
    return ir_a("/directiva/calendario")
