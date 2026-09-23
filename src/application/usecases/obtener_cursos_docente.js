// src/application/use_cases/obtener_cursos_docente.js
// Caso de uso: Consultar cursos asignados por docente (HU 1 / Tarea #18)

class ObtenerCursosDocente {
    constructor(cursoRepository) {
        this.cursoRepository = cursoRepository;
    }

    async ejecutar(docenteId) {
        if (!docenteId) {
            throw new Error("Identificador del docente es requerido para autorizar la consulta.");
        }

        const cursos = await this.cursoRepository.obtenerPorDocenteId(docenteId);

        // Regla CU-01: Si no tiene carga asignada para el período actual
        if (!cursos || cursos.length === 0) {
            return {
                tieneCarga: false,
                mensaje: "Actualmente no tiene cursos asignados. Contacte a U.T.P.",
                cursos: []
            };
        }

        return {
            tieneCarga: true,
            totalCursos: cursos.length,
            cursos: cursos
        };
    }
}

module.exports = ObtenerCursosDocente;