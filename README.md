# Seguimiento de trayectorias y riesgo de deserción · Sprints 1 y 2

Proyecto semestral de Ingeniería de Software · Desafío N°7.

**Integrantes:** Diego Rubilar · Mirko Massa · Constanza Rodríguez · Ignacio Pino

Aplicación web en FastAPI con tres portales (directiva, profesor jefe y alumno) que cruza
notas y asistencia para mostrar el estado de riesgo de cada alumno. Sigue la arquitectura
definida en el Hito 1: **monolito modular con arquitectura hexagonal (puertos y adaptadores)**,
MVC en el adaptador web y control de acceso por roles (RBAC) con JWT en la API.

## Cómo ejecutarlo (Windows + VS Code)

```powershell
# 1. Abrir la carpeta en VS Code y abrir una terminal (Ctrl + ñ)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Levantar el servidor
uvicorn app.main:app --reload
```

- Portal web: <http://127.0.0.1:8000>
- API REST documentada (Swagger): <http://127.0.0.1:8000/docs>. Primero `POST /api/login`,
  copiar el `access_token` y pegarlo en el botón **Authorize**.
- La primera vez se crea `liceo.db` con datos de prueba. Para empezar de cero: `python -m app.compartido.seed --reset`.

Pruebas automáticas (102 pruebas):

```powershell
pytest -v                    # todas
pytest tests/unitarias -v    # solo dominio y casos de uso (no usan base de datos)
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

## Arquitectura

Monolito modular: 3 módulos activos de los 5 definidos en el Hito 1. Cada módulo es un hexágono:

| Capa | Archivo en cada módulo | Qué contiene | Puede importar |
| --- | --- | --- | --- |
| Dominio | `dominio.py` | Entidades y reglas puras (ej. `calcular_riesgo`, `validar_nota`) | Solo Python estándar |
| Puertos de salida | `puertos.py` | Interfaces (`ABC`) de lo que el núcleo necesita: repositorios, exportador | Dominio |
| Casos de uso (puertos de entrada) | `casos_uso.py` | Orquestan dominio y puertos; lanzan errores de negocio | Dominio y puertos |
| Adaptadores de entrada | `adaptadores/entrada_web*.py`, `adaptadores/entrada_api.py` | Páginas HTML (controladores MVC) y API REST con Pydantic | Casos de uso |
| Adaptadores de salida | `adaptadores/salida_*.py` | SQLite, Excel (openpyxl) | Puertos |

```
app/
  main.py               arma la app y traduce errores de negocio a HTTP (400/401/403/404/409)
  contenedor.py         raíz de composición: conecta adaptadores con casos de uso
  compartido/           conexión SQLite, datos de prueba y errores de negocio
  seguridad/            Seguridad y Usuarios: login, JWT, RBAC
  academico/            Gestión Académica: cursos, notas, asistencia, calendario, exportar
  riesgo/               Motor de Riesgo: cálculo del semáforo
  web/templates, static vistas HTML (la V del MVC)
tests/
  unitarias/            dominio, casos de uso con repositorios falsos, seguridad, arquitectura
  integracion/          páginas web y API REST
```

`tests/unitarias/test_arquitectura.py` falla si alguien importa FastAPI, SQLite u openpyxl dentro
del dominio o de los casos de uso: así la regla de dependencias del Hito 1 no se rompe sin aviso.

Los módulos **Intervención Psicosocial** y **Comunidad y Dirección** quedan fuera del alcance actual.

## Qué historia está en qué archivo

| Historia | Sprint | Núcleo | Web | API REST |
| --- | --- | --- | --- | --- |
| HU-01 Iniciar sesión según rol | 1 | `seguridad/casos_uso.py` | `seguridad/adaptadores/entrada_web.py` | `POST /api/login` |
| HU-04 Ver curso con riesgo | 1 | `riesgo/casos_uso.py` | `academico/adaptadores/entrada_web_profesor.py` | `GET /api/cursos/{id}/riesgo` |
| HU-05 Ingresar notas | 1 | `academico/casos_uso.py` (`RegistrarNotas`) | `entrada_web_profesor.py` | `PUT /api/cursos/{id}/notas` |
| HU-06 Asistencia diaria | 1 | `academico/casos_uso.py` (`PasarLista`) | `entrada_web_profesor.py` | `PUT /api/cursos/{id}/asistencia` |
| HU-07 Calcular riesgo | 1 | `riesgo/dominio.py` (`calcular_riesgo`) | — | — |
| HU-02 Asignar alumnos y profesor | 2 | `academico/casos_uso.py` (`AdministrarCursos`) | `entrada_web_directiva.py` | `POST /api/cursos`, `POST /api/cursos/{id}/alumnos` |
| HU-03 Calendario del semestre | 2 | `academico/dominio.py`, `AdministrarCalendario` | `entrada_web_directiva.py` | `PUT /api/calendario/semestre`, `POST /api/calendario/feriados` |
| HU-08 Exportar a Excel | 2 | `ExportarCurso` + `adaptadores/salida_excel.py` | `entrada_web_profesor.py` | `GET /api/cursos/{id}/exportar/{tipo}` |
| HU-09 Portal alumno | 3 | — | `seguridad/adaptadores/entrada_web_alumno.py` (aviso) | — |

## Pruebas unitarias propias (taller de pytest)

| N° | Archivo | Función | Qué comprueba | Tipo |
| --- | --- | --- | --- | --- |
| 1 | `tests/unitarias/test_riesgo.py` | `calcular_riesgo` | Los 4 estados (Bajo, Medio, Alto, Sin datos) con `parametrize` | Caso normal |
| 2 | `tests/unitarias/test_riesgo.py` | `calcular_riesgo` | 85 % y 4.0 exactos son Bajo; una décima menos es Medio | Caso límite |
| 3 | `tests/unitarias/test_academico_dominio.py` | `validar_nota` | Notas 0.9, 7.1, 8 y -3 lanzan `ValueError` (`pytest.raises`) | Excepción |
| 4 | `tests/unitarias/test_casos_uso.py` | `RegistrarNotas` | Si una nota es inválida no se guarda ninguna (repositorio falso) | Regla de negocio |
| 5 | `tests/unitarias/test_riesgo.py` | `porcentaje_asistencia` | Una falta justificada cuenta como asistencia (8 P + 1 J de 10 = 90 %) | Comportamiento propio |

Todas siguen el patrón Arrange · Act · Assert y se ejecutan sin base de datos.

## Decisiones respecto del Hito 1

| Decisión | Hito 1 | Ahora | Por qué |
| --- | --- | --- | --- |
| Estilo | Hexagonal + monolito modular | Se mantiene | — |
| Backend | Node.js / Spring Boot | FastAPI (Python) | Herramienta del taller del curso |
| Base de datos | PostgreSQL | SQLite en desarrollo | Para cambiar a PostgreSQL solo se escriben otros `salida_*.py` y se cambian en `contenedor.py` |
| Frontend | SPA React/Vue | HTML servido por FastAPI + API REST | Menos piezas; la API queda lista para otro frontend |
| Autenticación | JWT + RBAC | JWT (60 min) en la API, sesión firmada en la web, RBAC en ambos | Cumple RF01 sin complicar las páginas |
| Motor de riesgo | Tiempo real | Se calcula al consultar, con los datos recién guardados | 45 alumnos en milisegundos; no se justifica un bus de eventos |
| Regla de riesgo | Alto si falla asistencia o promedio | Bajo (verde) / Medio (amarillo, falla una) / Alto (rojo, fallan ambas) | Distingue un problema de dos; mismos umbrales 85 % y 4.0 |

- **% de asistencia** = (Presente + Justificado) / días registrados.
- **Privacidad:** el estado de riesgo solo lo ve el profesor jefe del curso (ni la directiva ni el alumno).
- **Antes de configurar el semestre** solo se bloquean sábados y domingos al pasar lista.
- La clave que firma la sesión y los JWT se define con la variable de entorno `SECRET_KEY`.
