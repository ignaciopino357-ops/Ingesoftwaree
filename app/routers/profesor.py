"""Portal profesor jefe.

HU-04 ver curso con riesgo · HU-05 ingresar notas · HU-06 pasar lista · HU-08 exportar a Excel
"""
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app import consultas
from app.auth import exigir_rol
from app.calendario import motivo_no_clases
from app.db import conexion
from app.exportar import excel_asistencia, excel_notas
from app.web import avisar, ir_a, render

router = APIRouter(prefix="/profesor")

ESTADOS = {"P": "Presente", "A": "Ausente", "J": "Justificado"}


def curso_propio(request: Request, curso_id: int) -> tuple:
    """Devuelve (profesor, curso) solo si el curso es del profesor conectado."""
    profesor = exigir_rol(request, "profesor")
    curso = consultas.obtener_curso(curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="El curso no existe")
    if curso["profesor_id"] != profesor["id"]:
        raise HTTPException(status_code=403, detail="No tiene acceso a este curso")
    return profesor, curso


def nombre_archivo(texto: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_).strip("_")


# ---------- HU-04: portal y vista del curso ----------

@router.get("")
def portal_profesor(request: Request):
    profesor = exigir_rol(request, "profesor")
    cursos = consultas.cursos_del_profesor(profesor["id"])
    if len(cursos) == 1:
        return ir_a(f"/profesor/cursos/{cursos[0]['id']}")
    return render(request, "profesor/portal.html", cursos=cursos)


@router.get("/cursos/{curso_id}")
def ver_curso(request: Request, curso_id: int, orden: str = "riesgo"):
    _, curso = curso_propio(request, curso_id)
    alumnos = consultas.resumen_curso(curso_id, orden)
    conteo = {nivel: 0 for nivel in ("Alto", "Medio", "Bajo", "Sin datos")}
    for a in alumnos:
        conteo[a["riesgo"]] += 1
    hay_notas = any(a["promedio"] is not None for a in alumnos)
    hay_asistencia = any(sum(a["conteo"].values()) > 0 for a in alumnos)
    return render(
        request, "profesor/curso.html", curso=curso, alumnos=alumnos, conteo=conteo,
        orden=orden, hay_notas=hay_notas, hay_asistencia=hay_asistencia,
    )


@router.get("/cursos/{curso_id}/alumnos/{alumno_id}")
def ver_alumno(request: Request, curso_id: int, alumno_id: int):
    _, curso = curso_propio(request, curso_id)
    alumno = next((a for a in consultas.alumnos_del_curso(curso_id) if a["id"] == alumno_id), None)
    if alumno is None:
        raise HTTPException(status_code=404, detail="El alumno no pertenece a este curso")
    return render(
        request, "profesor/alumno.html", curso=curso,
        alumno=consultas.resumen_alumno(alumno),
        notas=consultas.notas_del_alumno(alumno_id),
        asistencia=consultas.asistencia_del_alumno(alumno_id),
        estados=ESTADOS,
    )


# ---------- HU-05: ingresar notas ----------

def _pantalla_notas(request, curso, asignatura_id, valores, errores, status_code=200):
    return render(
        request, "profesor/notas.html", status_code=status_code, curso=curso,
        asignaturas=consultas.asignaturas(), asignatura_id=asignatura_id,
        alumnos=consultas.alumnos_del_curso(curso["id"]),
        evaluaciones=range(1, consultas.NUM_EVALUACIONES + 1),
        valores=valores, errores=errores,
    )


@router.get("/cursos/{curso_id}/notas")
def ver_notas(request: Request, curso_id: int, asignatura: int = 0):
    _, curso = curso_propio(request, curso_id)
    asignatura_id = asignatura or consultas.asignaturas()[0]["id"]
    guardadas = consultas.notas_de_asignatura(curso_id, asignatura_id)
    valores = {
        f"n_{alumno_id}_{num}": f"{nota:.1f}"
        for alumno_id, notas in guardadas.items() for num, nota in notas.items()
    }
    return _pantalla_notas(request, curso, asignatura_id, valores, {})


@router.post("/cursos/{curso_id}/notas")
async def guardar_notas(request: Request, curso_id: int):
    _, curso = curso_propio(request, curso_id)
    form = await request.form()
    asignatura_id = int(form.get("asignatura_id"))
    alumnos = consultas.alumnos_del_curso(curso_id)

    valores, errores, a_guardar = {}, {}, []
    for alumno in alumnos:
        for num in range(1, consultas.NUM_EVALUACIONES + 1):
            campo = f"n_{alumno['id']}_{num}"
            texto = (form.get(campo) or "").strip().replace(",", ".")
            valores[campo] = texto
            if texto == "":
                a_guardar.append((alumno["id"], num, None))
                continue
            try:
                nota = round(float(texto), 1)
            except ValueError:
                errores[campo] = "No es un número"
                continue
            if not 1.0 <= nota <= 7.0:
                errores[campo] = "Debe estar entre 1.0 y 7.0"
                continue
            a_guardar.append((alumno["id"], num, nota))

    # HU-05, criterio 2: si hay un error no se guarda nada
    if errores:
        avisar(request, f"No se guardó: hay {len(errores)} nota(s) inválida(s). Deben estar entre 1.0 y 7.0.", "error")
        return _pantalla_notas(request, curso, asignatura_id, valores, errores, status_code=400)

    with conexion() as conn:
        for alumno_id, num, nota in a_guardar:
            if nota is None:
                conn.execute(
                    "DELETE FROM notas WHERE alumno_id = ? AND asignatura_id = ? AND numero = ?",
                    (alumno_id, asignatura_id, num),
                )
            else:
                conn.execute(
                    """INSERT INTO notas (alumno_id, asignatura_id, numero, nota) VALUES (?, ?, ?, ?)
                       ON CONFLICT (alumno_id, asignatura_id, numero) DO UPDATE SET nota = excluded.nota""",
                    (alumno_id, asignatura_id, num, nota),
                )
    avisar(request, "Notas guardadas. Promedios y estado de riesgo actualizados.")
    return ir_a(f"/profesor/cursos/{curso_id}/notas?asignatura={asignatura_id}")


# ---------- HU-06: registrar asistencia diaria ----------

def _validar_fecha(texto: str) -> tuple:
    """Devuelve (fecha, motivo_de_bloqueo). motivo es None si se puede pasar lista ese día."""
    try:
        dia = date.fromisoformat(texto)
    except ValueError:
        return None, "Fecha inválida"
    if dia > date.today():
        return dia, "No se puede registrar asistencia de un día futuro"
    inicio, fin = consultas.obtener_semestre()
    return dia, motivo_no_clases(dia, inicio, fin, consultas.obtener_feriados())


@router.get("/cursos/{curso_id}/asistencia")
def ver_asistencia(request: Request, curso_id: int, fecha: str = ""):
    _, curso = curso_propio(request, curso_id)
    fecha = fecha or date.today().isoformat()
    dia, bloqueo = _validar_fecha(fecha)
    registrada = consultas.asistencia_del_dia(curso_id, fecha) if dia else {}
    return render(
        request, "profesor/asistencia.html", curso=curso, fecha=fecha, bloqueo=bloqueo,
        alumnos=consultas.alumnos_del_curso(curso_id), registrada=registrada,
        ya_registrada=bool(registrada), estados=ESTADOS,
    )


@router.post("/cursos/{curso_id}/asistencia")
async def guardar_asistencia(request: Request, curso_id: int):
    _, curso = curso_propio(request, curso_id)
    form = await request.form()
    fecha = form.get("fecha", "")
    dia, bloqueo = _validar_fecha(fecha)
    if bloqueo:
        avisar(request, f"No se guardó: {bloqueo}.", "error")
        return ir_a(f"/profesor/cursos/{curso_id}/asistencia?fecha={fecha}")

    with conexion() as conn:
        for alumno in consultas.alumnos_del_curso(curso_id):
            estado = form.get(f"estado_{alumno['id']}", "P")
            if estado not in ESTADOS:
                estado = "P"
            conn.execute(
                """INSERT INTO asistencia (alumno_id, fecha, estado) VALUES (?, ?, ?)
                   ON CONFLICT (alumno_id, fecha) DO UPDATE SET estado = excluded.estado""",
                (alumno["id"], dia.isoformat(), estado),
            )
    avisar(request, f"Asistencia del {dia.strftime('%d-%m-%Y')} guardada.")
    return ir_a(f"/profesor/cursos/{curso_id}/asistencia?fecha={fecha}")


# ---------- HU-08: exportar a Excel ----------

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _descarga(contenido: bytes, archivo: str) -> Response:
    return Response(
        contenido, media_type=TIPO_EXCEL,
        headers={"Content-Disposition": f'attachment; filename="{archivo}"'},
    )


@router.get("/cursos/{curso_id}/exportar/notas")
def exportar_notas(request: Request, curso_id: int):
    _, curso = curso_propio(request, curso_id)
    if not any(consultas.notas_del_alumno(a["id"]) for a in consultas.alumnos_del_curso(curso_id)):
        avisar(request, "No hay datos para exportar.", "error")
        return ir_a(f"/profesor/cursos/{curso_id}")
    return _descarga(excel_notas(curso_id), f"notas_{nombre_archivo(curso['nombre'])}.xlsx")


@router.get("/cursos/{curso_id}/exportar/asistencia")
def exportar_asistencia(request: Request, curso_id: int):
    _, curso = curso_propio(request, curso_id)
    if not consultas.fechas_con_asistencia(curso_id):
        avisar(request, "No hay datos para exportar.", "error")
        return ir_a(f"/profesor/cursos/{curso_id}")
    return _descarga(excel_asistencia(curso_id), f"asistencia_{nombre_archivo(curso['nombre'])}.xlsx")
