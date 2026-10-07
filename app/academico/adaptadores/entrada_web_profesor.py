"""Módulo Gestión Académica · ADAPTADOR DE ENTRADA WEB: portal del profesor jefe (Controlador del MVC).

Solo traduce HTTP <-> casos de uso. No contiene reglas de negocio ni SQL.
HU-04 ver curso · HU-05 notas · HU-06 pasar lista · HU-08 exportar
"""
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app import contenedor
from app.academico.dominio import NUM_EVALUACIONES, EstadoAsistencia
from app.compartido.errores import DatosInvalidos, NoEncontrado
from app.seguridad.adaptadores.entrada_web import usuario_web
from app.seguridad.dominio import Rol
from app.web.vistas import avisar, ir_a, render

router = APIRouter(prefix="/profesor", include_in_schema=False)

ESTADOS = {e.value: e.texto for e in EstadoAsistencia}
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _curso(request: Request, curso_id: int):
    usuario = usuario_web(request, Rol.PROFESOR)
    return contenedor.acceder_curso.ejecutar(usuario, curso_id)


def nombre_archivo(texto: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_).strip("_")


# ---------- HU-04 ----------

@router.get("")
def portal(request: Request):
    usuario = usuario_web(request, Rol.PROFESOR)
    cursos = contenedor.listar_cursos.ejecutar(usuario)
    if len(cursos) == 1:
        return ir_a(f"/profesor/cursos/{cursos[0].id}")
    return render(request, "profesor/portal.html", cursos=cursos)


@router.get("/cursos/{curso_id}")
def ver_curso(request: Request, curso_id: int, orden: str = "riesgo"):
    curso = _curso(request, curso_id)
    alumnos = contenedor.consultar_riesgo.ejecutar(curso_id, orden)
    return render(
        request, "profesor/curso.html", curso=curso, alumnos=alumnos, orden=orden,
        conteo=contenedor.consultar_riesgo.conteo_por_estado(alumnos),
        hay_notas=contenedor.exportar_curso.hay_notas(curso_id),
        hay_asistencia=contenedor.exportar_curso.hay_asistencia(curso_id),
    )


@router.get("/cursos/{curso_id}/alumnos/{alumno_id}")
def ver_alumno(request: Request, curso_id: int, alumno_id: int):
    curso = _curso(request, curso_id)
    alumno = next((a for a in contenedor.acceder_curso.alumnos(curso_id) if a.id == alumno_id), None)
    if alumno is None:
        raise NoEncontrado("El alumno no pertenece a este curso")
    return render(
        request, "profesor/alumno.html", curso=curso,
        alumno=contenedor.consultar_riesgo.alumno(alumno.id, alumno.nombre),
        notas=contenedor.consultar_notas.de_alumno(alumno_id),
        asistencia=[{"fecha": f, "estado": e} for f, e in contenedor.consultar_asistencia.de_alumno(alumno_id)],
        estados=ESTADOS,
    )


# ---------- HU-05 ----------

def _pantalla_notas(request, curso, asignatura_id, valores, errores, status_code=200):
    return render(
        request, "profesor/notas.html", status_code=status_code, curso=curso,
        asignaturas=contenedor.consultar_notas.asignaturas(), asignatura_id=asignatura_id,
        alumnos=contenedor.acceder_curso.alumnos(curso.id), evaluaciones=range(1, NUM_EVALUACIONES + 1),
        valores=valores, errores=errores,
    )


@router.get("/cursos/{curso_id}/notas")
def ver_notas(request: Request, curso_id: int, asignatura: int = 0):
    curso = _curso(request, curso_id)
    asignatura_id = asignatura or contenedor.consultar_notas.asignaturas()[0]["id"]
    guardadas = contenedor.consultar_notas.de_asignatura(curso_id, asignatura_id)
    valores = {f"n_{a}_{n}": f"{nota:.1f}" for a, notas in guardadas.items() for n, nota in notas.items()}
    return _pantalla_notas(request, curso, asignatura_id, valores, {})


@router.post("/cursos/{curso_id}/notas")
async def guardar_notas(request: Request, curso_id: int):
    curso = _curso(request, curso_id)
    form = await request.form()
    asignatura_id = int(form.get("asignatura_id"))
    entradas, valores = [], {}
    for alumno in contenedor.acceder_curso.alumnos(curso_id):
        for numero in range(1, NUM_EVALUACIONES + 1):
            campo = f"n_{alumno.id}_{numero}"
            valores[campo] = (form.get(campo) or "").strip()
            entradas.append((alumno.id, numero, valores[campo]))
    try:
        contenedor.registrar_notas.ejecutar(curso_id, asignatura_id, entradas)
    except DatosInvalidos as error:
        avisar(request, error.mensaje, "error")
        return _pantalla_notas(request, curso, asignatura_id, valores, error.detalles, status_code=400)
    avisar(request, "Notas guardadas. Promedios y estado de riesgo actualizados.")
    return ir_a(f"/profesor/cursos/{curso_id}/notas?asignatura={asignatura_id}")


# ---------- HU-06 ----------

@router.get("/cursos/{curso_id}/asistencia")
def ver_asistencia(request: Request, curso_id: int, fecha: str = ""):
    curso = _curso(request, curso_id)
    fecha = fecha or date.today().isoformat()
    try:
        dia = date.fromisoformat(fecha)
        bloqueo = contenedor.pasar_lista.bloqueo(dia, date.today())
        registrada = contenedor.pasar_lista.consultar(curso_id, dia)
    except ValueError:
        bloqueo, registrada = "Fecha inválida", {}
    return render(
        request, "profesor/asistencia.html", curso=curso, fecha=fecha, bloqueo=bloqueo,
        alumnos=contenedor.acceder_curso.alumnos(curso_id), registrada=registrada,
        ya_registrada=bool(registrada), estados=ESTADOS,
    )


@router.post("/cursos/{curso_id}/asistencia")
async def guardar_asistencia(request: Request, curso_id: int):
    _curso(request, curso_id)
    form = await request.form()
    fecha = form.get("fecha", "")
    estados = {a.id: form.get(f"estado_{a.id}", "P") for a in contenedor.acceder_curso.alumnos(curso_id)}
    try:
        dia = date.fromisoformat(fecha)
        contenedor.pasar_lista.ejecutar(curso_id, dia, estados, hoy=date.today())
    except ValueError:
        avisar(request, "No se guardó: fecha inválida.", "error")
    except DatosInvalidos as error:
        avisar(request, error.mensaje, "error")
    else:
        avisar(request, f"Asistencia del {dia.strftime('%d-%m-%Y')} guardada.")
    return ir_a(f"/profesor/cursos/{curso_id}/asistencia?fecha={fecha}")


# ---------- HU-08 ----------

@router.get("/cursos/{curso_id}/exportar/{tipo}")
def exportar(request: Request, curso_id: int, tipo: str):
    curso = _curso(request, curso_id)
    generar = {"notas": contenedor.exportar_curso.notas_excel,
               "asistencia": contenedor.exportar_curso.asistencia_excel}.get(tipo)
    if generar is None:
        raise NoEncontrado("Tipo de exportación desconocido")
    try:
        contenido = generar(curso_id)
    except NoEncontrado as error:
        avisar(request, error.mensaje, "error")
        return ir_a(f"/profesor/cursos/{curso_id}")
    return Response(contenido, media_type=TIPO_EXCEL, headers={
        "Content-Disposition": f'attachment; filename="{tipo}_{nombre_archivo(curso.nombre)}.xlsx"'})
