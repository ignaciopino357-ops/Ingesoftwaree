"""Módulo Gestión Académica · CASOS DE USO (puertos de entrada).

Orquestan el dominio y los puertos. No conocen HTTP, HTML ni SQL:
reciben datos simples y lanzan errores de negocio (app.compartido.errores).
"""
from datetime import date
from typing import Optional

from app.academico import dominio
from app.academico.dominio import Alumno, Curso, EstadoAsistencia
from app.academico.puertos import (
    ExportadorPlanillas, RepositorioAsistencia, RepositorioCalendario, RepositorioCursos, RepositorioNotas,
)
from app.compartido.errores import Conflicto, DatosInvalidos, NoEncontrado, SinPermiso
from app.seguridad.dominio import Rol, Usuario


# ---------- Acceso a cursos (HU-01 + RBAC) ----------

class AccederCurso:
    """Un profesor jefe solo accede a sus cursos; la directiva administra todos."""

    def __init__(self, cursos: RepositorioCursos):
        self.cursos = cursos

    def ejecutar(self, usuario: Usuario, curso_id: int, permitir_directiva: bool = False) -> Curso:
        curso = self.cursos.obtener(curso_id)
        if curso is None:
            raise NoEncontrado("El curso no existe")
        if usuario.rol == Rol.DIRECTIVA and permitir_directiva:
            return curso
        if usuario.rol != Rol.PROFESOR or curso.profesor_id != usuario.id:
            raise SinPermiso("No tiene acceso a este curso")
        return curso

    def alumnos(self, curso_id: int) -> list[Alumno]:
        return self.cursos.alumnos(curso_id)


class ListarCursos:
    def __init__(self, cursos: RepositorioCursos):
        self.cursos = cursos

    def ejecutar(self, usuario: Usuario) -> list[Curso]:
        if usuario.rol == Rol.DIRECTIVA:
            return self.cursos.listar()
        if usuario.rol == Rol.PROFESOR:
            return self.cursos.listar_de_profesor(usuario.id)
        raise SinPermiso("No tiene acceso a esta sección")


# ---------- HU-05: notas ----------

class ConsultarNotas:
    def __init__(self, notas: RepositorioNotas):
        self.notas = notas

    def asignaturas(self) -> list[dict]:
        return self.notas.asignaturas()

    def de_asignatura(self, curso_id: int, asignatura_id: int) -> dict:
        return self.notas.de_asignatura(curso_id, asignatura_id)

    def de_alumno(self, alumno_id: int) -> dict:
        return self.notas.de_alumno(alumno_id)


class RegistrarNotas:
    """Valida todas las notas y guarda solo si no hay errores (HU-05, criterio 2)."""

    def __init__(self, cursos: RepositorioCursos, notas: RepositorioNotas):
        self.cursos = cursos
        self.notas = notas

    def ejecutar(self, curso_id: int, asignatura_id: int, entradas: list[tuple[int, int, object]]) -> int:
        """entradas = [(alumno_id, numero, valor)]; valor vacío o None = borrar la nota.

        Devuelve cuántas notas quedaron guardadas.
        """
        if asignatura_id not in {a["id"] for a in self.notas.asignaturas()}:
            raise NoEncontrado("La asignatura no existe")
        del_curso = {a.id for a in self.cursos.alumnos(curso_id)}
        errores, cambios = {}, []
        for alumno_id, numero, valor in entradas:
            campo = f"n_{alumno_id}_{numero}"
            if alumno_id not in del_curso:
                errores[campo] = "El alumno no pertenece a este curso"
                continue
            try:
                dominio.validar_numero_evaluacion(numero)
                nota = None if valor in (None, "") or (isinstance(valor, str) and not valor.strip()) \
                    else dominio.validar_nota(valor)
            except ValueError as error:
                errores[campo] = str(error)
                continue
            cambios.append((alumno_id, numero, nota))
        if errores:
            raise DatosInvalidos(
                f"No se guardó: hay {len(errores)} nota(s) inválida(s). Deben estar entre 1.0 y 7.0.",
                detalles=errores,
            )
        self.notas.guardar(asignatura_id, cambios)
        return sum(1 for c in cambios if c[2] is not None)


# ---------- HU-06: asistencia diaria ----------

class PasarLista:
    def __init__(self, cursos: RepositorioCursos, asistencia: RepositorioAsistencia,
                 calendario: RepositorioCalendario):
        self.cursos = cursos
        self.asistencia = asistencia
        self.calendario = calendario

    def bloqueo(self, dia: date, hoy: date) -> Optional[str]:
        inicio, fin = self.calendario.semestre()
        return dominio.motivo_bloqueo_asistencia(dia, hoy, inicio, fin, self.calendario.feriados())

    def consultar(self, curso_id: int, dia: date) -> dict:
        return self.asistencia.del_dia(curso_id, dia)

    def ejecutar(self, curso_id: int, dia: date, estados: dict, hoy: date) -> int:
        """estados = {alumno_id: "P" | "A" | "J"}; quien no aparece queda Presente."""
        motivo = self.bloqueo(dia, hoy)
        if motivo:
            raise DatosInvalidos(f"No se guardó: {motivo}.")
        alumnos = {a.id for a in self.cursos.alumnos(curso_id)}
        ajenos = set(estados) - alumnos
        if ajenos:
            raise DatosInvalidos("Hay alumnos que no pertenecen a este curso", {"alumnos": sorted(ajenos)})
        try:
            limpios = {a: EstadoAsistencia(estados.get(a, "P")).value for a in alumnos}
        except ValueError:
            raise DatosInvalidos("El estado debe ser P, A o J")
        self.asistencia.guardar(dia, limpios)
        return len(limpios)


class ConsultarAsistencia:
    def __init__(self, asistencia: RepositorioAsistencia):
        self.asistencia = asistencia

    def de_alumno(self, alumno_id: int) -> list[tuple[str, str]]:
        return self.asistencia.de_alumno(alumno_id)

    def conteo(self, alumno_id: int) -> dict:
        return self.asistencia.conteo(alumno_id)


# ---------- HU-02: cursos (directiva) ----------

class AdministrarCursos:
    def __init__(self, cursos: RepositorioCursos):
        self.cursos = cursos

    def crear(self, nombre: str, profesor_id: Optional[int]) -> int:
        nombre = (nombre or "").strip()
        if not nombre:
            raise DatosInvalidos("Escriba el nombre del curso.")
        if self.cursos.existe_nombre(nombre):
            raise Conflicto(f"Ya existe un curso llamado {nombre}.")
        return self.cursos.crear(nombre, profesor_id)

    def asignar_profesor(self, curso_id: int, profesor_id: Optional[int]) -> None:
        self._curso(curso_id)
        self.cursos.asignar_profesor(curso_id, profesor_id)

    def agregar_alumno(self, curso_id: int, alumno_id: int) -> None:
        self._curso(curso_id)
        if alumno_id not in {a.id for a, _ in self.cursos.todos_los_alumnos()}:
            raise NoEncontrado("El alumno no existe")
        actual = self.cursos.curso_de_alumno(alumno_id)
        if actual:
            # HU-02, criterio 3: un alumno pertenece a un solo curso
            raise Conflicto(f"No se guardó: el alumno ya pertenece a {actual}. Quítelo de ese curso primero.")
        self.cursos.agregar_alumno(curso_id, alumno_id)

    def quitar_alumno(self, curso_id: int, alumno_id: int) -> None:
        self._curso(curso_id)
        self.cursos.quitar_alumno(curso_id, alumno_id)

    def todos_los_alumnos(self) -> list[tuple[Alumno, Optional[str]]]:
        return self.cursos.todos_los_alumnos()

    def _curso(self, curso_id: int) -> Curso:
        curso = self.cursos.obtener(curso_id)
        if curso is None:
            raise NoEncontrado("El curso no existe")
        return curso


# ---------- HU-03: calendario del semestre ----------

class AdministrarCalendario:
    def __init__(self, calendario: RepositorioCalendario):
        self.calendario = calendario

    def semestre(self):
        return self.calendario.semestre()

    def feriados(self) -> dict:
        return self.calendario.feriados()

    def configurar_semestre(self, inicio: date, fin: date) -> None:
        try:
            dominio.validar_semestre(inicio, fin)
        except ValueError as error:
            raise DatosInvalidos(f"No se guardó: {str(error).lower()}.")
        self.calendario.guardar_semestre(inicio, fin)

    def agregar_feriado(self, dia: date, nombre: str) -> None:
        if not (nombre or "").strip():
            raise DatosInvalidos("Ingrese la fecha y el nombre del feriado.")
        self.calendario.guardar_feriado(dia, nombre.strip())

    def eliminar_feriado(self, dia: date) -> None:
        self.calendario.eliminar_feriado(dia)

    def dias_de_clases(self) -> Optional[int]:
        inicio, fin = self.calendario.semestre()
        return len(dominio.dias_de_clases(inicio, fin, self.calendario.feriados())) if inicio else None

    def mes(self, anio: int, mes: int) -> list:
        """Semanas del mes con el tipo de cada día: clases, feriado, finde o fuera."""
        inicio, fin = self.calendario.semestre()
        feriados = self.calendario.feriados()
        semanas = []
        for semana in dominio.semanas_del_mes(anio, mes):
            fila = []
            for dia in semana:
                if dia is None:
                    fila.append(None)
                    continue
                motivo = dominio.motivo_no_clases(dia, inicio, fin, feriados)
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
        return semanas


# ---------- HU-08: exportar a Excel ----------

class ExportarCurso:
    def __init__(self, cursos: RepositorioCursos, notas: RepositorioNotas,
                 asistencia: RepositorioAsistencia, exportador: ExportadorPlanillas):
        self.cursos = cursos
        self.notas = notas
        self.asistencia = asistencia
        self.exportador = exportador

    def hay_notas(self, curso_id: int) -> bool:
        return any(self.notas.de_alumno(a.id) for a in self.cursos.alumnos(curso_id))

    def hay_asistencia(self, curso_id: int) -> bool:
        return bool(self.asistencia.fechas(curso_id))

    def notas_excel(self, curso_id: int) -> bytes:
        if not self.hay_notas(curso_id):
            raise NoEncontrado("No hay datos para exportar.")
        hojas = [(a["nombre"], self.notas.de_asignatura(curso_id, a["id"])) for a in self.notas.asignaturas()]
        return self.exportador.notas(self.cursos.alumnos(curso_id), hojas)

    def asistencia_excel(self, curso_id: int) -> bytes:
        fechas = self.asistencia.fechas(curso_id)
        if not fechas:
            raise NoEncontrado("No hay datos para exportar.")
        alumnos = self.cursos.alumnos(curso_id)
        registros = {a.id: dict(self.asistencia.de_alumno(a.id)) for a in alumnos}
        conteos = {a.id: self.asistencia.conteo(a.id) for a in alumnos}
        return self.exportador.asistencia(alumnos, fechas, registros, conteos)
