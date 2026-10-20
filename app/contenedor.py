"""Raíz de composición: el único lugar donde se eligen los adaptadores concretos.

Aquí se "enchufan" los repositorios SQLite y el exportador Excel en los casos de uso.
Para usar PostgreSQL bastaría con escribir otros repositorios y cambiarlos en este archivo.
"""
from app.academico import casos_uso as academico
from app.academico.adaptadores.salida_excel import ExportadorExcel
from app.academico.adaptadores.salida_sqlite import (
    RepositorioAsistenciaSQLite, RepositorioCalendarioSQLite, RepositorioCursosSQLite, RepositorioNotasSQLite,
)
from app.riesgo import casos_uso as riesgo
from app.riesgo.adaptadores.entrada_academico import RevisarAlertasAlGuardar
from app.riesgo.adaptadores.salida_academico import FuenteAcademicaLocal
from app.riesgo.adaptadores.salida_sqlite import RepositorioAlertasSQLite
from app.seguridad.adaptadores.salida_sqlite import RepositorioUsuariosSQLite
from app.seguridad.casos_uso import IniciarSesion, ObtenerUsuario, RegistrarUsuario

# Adaptadores de salida
usuarios = RepositorioUsuariosSQLite()
cursos = RepositorioCursosSQLite()
notas = RepositorioNotasSQLite()
asistencia = RepositorioAsistenciaSQLite()
calendario = RepositorioCalendarioSQLite()
alertas = RepositorioAlertasSQLite()

# Módulo Seguridad y Usuarios
iniciar_sesion = IniciarSesion(usuarios)
obtener_usuario = ObtenerUsuario(usuarios)
registrar_usuario = RegistrarUsuario(usuarios)

# Módulo Motor de Riesgo (depende de Gestión Académica a través de FuenteAcademica)
fuente_academica = FuenteAcademicaLocal(cursos, notas, asistencia, calendario)
consultar_riesgo = riesgo.ConsultarCursoConRiesgo(fuente_academica)
vigilar_riesgo = riesgo.VigilarRiesgo(fuente_academica, alertas)
historial_riesgo = riesgo.HistorialRiesgo(fuente_academica)
resumen_riesgo = riesgo.ResumenRiesgoCursos(fuente_academica)

# Módulo Gestión Académica. Al guardar notas o asistencia avisa al observador,
# que revisa las alertas del curso (HU-10 y HU-12).
observador = RevisarAlertasAlGuardar(vigilar_riesgo)
acceder_curso = academico.AccederCurso(cursos)
listar_cursos = academico.ListarCursos(cursos)
consultar_notas = academico.ConsultarNotas(notas)
registrar_notas = academico.RegistrarNotas(cursos, notas, observador)
pasar_lista = academico.PasarLista(cursos, asistencia, calendario, observador)
consultar_asistencia = academico.ConsultarAsistencia(asistencia)
consultar_mis_datos = academico.ConsultarMisDatos(cursos, notas, asistencia)
consultar_mi_calendario = academico.ConsultarMiCalendario(calendario, asistencia)
administrar_cursos = academico.AdministrarCursos(cursos)
administrar_calendario = academico.AdministrarCalendario(calendario)
exportar_curso = academico.ExportarCurso(cursos, notas, asistencia, ExportadorExcel())
