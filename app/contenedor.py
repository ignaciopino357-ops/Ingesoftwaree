"""Raíz de composición: el único lugar donde se eligen los adaptadores concretos.

Aquí se "enchufan" los repositorios SQLite y el exportador Excel en los casos de uso.
Para usar PostgreSQL bastaría con escribir otros repositorios y cambiarlos en este archivo.
"""
from app.academico import casos_uso as academico
from app.academico.adaptadores.salida_excel import ExportadorExcel
from app.academico.adaptadores.salida_sqlite import (
    RepositorioAsistenciaSQLite, RepositorioCalendarioSQLite, RepositorioCursosSQLite, RepositorioNotasSQLite,
)
from app.riesgo.adaptadores.salida_academico import FuenteAcademicaLocal
from app.riesgo.casos_uso import ConsultarCursoConRiesgo
from app.seguridad.adaptadores.salida_sqlite import RepositorioUsuariosSQLite
from app.seguridad.casos_uso import IniciarSesion, ObtenerUsuario

# Adaptadores de salida
usuarios = RepositorioUsuariosSQLite()
cursos = RepositorioCursosSQLite()
notas = RepositorioNotasSQLite()
asistencia = RepositorioAsistenciaSQLite()
calendario = RepositorioCalendarioSQLite()

# Módulo Seguridad y Usuarios
iniciar_sesion = IniciarSesion(usuarios)
obtener_usuario = ObtenerUsuario(usuarios)

# Módulo Gestión Académica
acceder_curso = academico.AccederCurso(cursos)
listar_cursos = academico.ListarCursos(cursos)
consultar_notas = academico.ConsultarNotas(notas)
registrar_notas = academico.RegistrarNotas(cursos, notas)
pasar_lista = academico.PasarLista(cursos, asistencia, calendario)
consultar_asistencia = academico.ConsultarAsistencia(asistencia)
administrar_cursos = academico.AdministrarCursos(cursos)
administrar_calendario = academico.AdministrarCalendario(calendario)
exportar_curso = academico.ExportarCurso(cursos, notas, asistencia, ExportadorExcel())

# Módulo Motor de Riesgo
consultar_riesgo = ConsultarCursoConRiesgo(FuenteAcademicaLocal(cursos, notas, asistencia))
