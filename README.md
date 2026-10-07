# Seguimiento de trayectorias y riesgo de deserción · Sprints 1 y 2

Proyecto semestral de Ingeniería de Software · Desafío N°7.

**Integrantes:** Diego Rubilar · Mirko Massa · Constanza Rodríguez · Ignacio Pino

Aplicación web en FastAPI con tres portales (directiva, profesor jefe y alumno) que cruza
notas y asistencia para mostrar el estado de riesgo de cada alumno.

## Cómo ejecutarlo (Windows + VS Code)

```powershell
# 1. Abrir la carpeta en VS Code y abrir una terminal (Ctrl + ñ)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Levantar el servidor
uvicorn app.main:app --reload
```

Abrir <http://127.0.0.1:8000>. La primera vez se crea `liceo.db` con datos de prueba.
Para empezar de cero: `python -m app.seed --reset`.

Pruebas automáticas (31 pruebas, una o más por criterio de aceptación):

```powershell
pytest
```

## Usuarios de prueba

| Rol | Usuario | Contraseña | Qué ver |
| --- | --- | --- | --- |
| Directiva | `directiva` | `directiva123` | Cursos, asignación de alumnos y calendario |
| Profesor jefe 3° Medio A | `pjara` | `profe123` | Curso con 8 alumnos y riesgos variados |
| Profesor jefe 3° Medio B | `cmunoz` | `profe123` | Curso con 2 alumnos |
| Profesor sin curso | `pnuevo` | `profe123` | Mensaje "no tiene cursos asignados" |
| Alumno | `alumno1` … `alumno12` | `alumno123` | Portal alumno (Sprint 3) |

Los nombres son inventados. Los feriados cargados son de ejemplo: revisarlos en el portal directiva.

## Qué historia está en qué archivo

| Historia | Sprint | Archivos |
| --- | --- | --- |
| HU-01 Iniciar sesión según rol | 1 | `app/auth.py`, `app/routers/login.py` |
| HU-04 Ver curso con notas, asistencia y riesgo | 1 | `app/routers/profesor.py` (`ver_curso`, `ver_alumno`), `app/consultas.py` |
| HU-05 Ingresar notas | 1 | `app/routers/profesor.py` (`ver_notas`, `guardar_notas`) |
| HU-06 Registrar asistencia diaria | 1 | `app/routers/profesor.py` (`ver_asistencia`, `guardar_asistencia`) |
| HU-07 Calcular estado de riesgo | 1 | `app/riesgo.py` |
| HU-02 Asignar alumnos y profesor jefe | 2 | `app/routers/directiva.py` (cursos) |
| HU-03 Calendario del semestre | 2 | `app/calendario.py`, `app/routers/directiva.py` (calendario) |
| HU-08 Exportar a Excel | 2 | `app/exportar.py`, `app/routers/profesor.py` (`exportar_*`) |
| HU-09 Portal alumno | 3 | `app/routers/alumno.py` (por ahora solo una página de aviso) |

## Estructura

```
app/
  main.py          arranque de FastAPI, sesión y manejo de errores
  db.py            SQLite: tablas y conexión (sqlite3, sin ORM)
  seed.py          datos de prueba
  auth.py          contraseñas, sesión y control por rol
  riesgo.py        regla de riesgo (umbrales en constantes)
  calendario.py    días de clases, fines de semana y feriados
  consultas.py     consultas compartidas
  exportar.py      archivos Excel
  routers/         una ruta por portal
  templates/       páginas HTML (Jinja2)
  static/style.css estilos
tests/             pruebas con pytest
```

## Decisiones de diseño

- **Regla de riesgo:** Bajo si asistencia ≥ 85 % y promedio ≥ 4.0; Medio si falla una; Alto si fallan ambas.
  Los umbrales están en `app/riesgo.py`.
- **% de asistencia** = (Presente + Justificado) / días registrados. Una falta justificada no suma riesgo.
- **Privacidad:** el estado de riesgo solo lo ve el profesor jefe del curso; el alumno nunca ve etiquetas de riesgo.
- **Antes de configurar el semestre** solo se bloquean sábados y domingos al pasar lista.
- La clave de la sesión se define con la variable de entorno `SECRET_KEY` (hay un valor por defecto solo para desarrollo).
