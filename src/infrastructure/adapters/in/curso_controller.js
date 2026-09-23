// src/infrastructure/adapters/in/curso_controller.js
// Adaptador Primario REST: Endpoint para listar cursos asignados (HU 1 / Tarea #18)

class CursoController {
    constructor(obtenerCursosDocenteUseCase) {
        this.obtenerCursosDocenteUseCase = obtenerCursosDocenteUseCase;
    }

    async listarCursos(req, res) {
        const inicioConsulta = Date.now();
        const docenteId = req.query.docenteId || req.user?.id;

        try {
            if (!docenteId) {
                return res.status(400).json({
                    exito: false,
                    mensaje: "Debe especificar el parámetro docenteId."
                });
            }

            const resultado = await this.obtenerCursosDocenteUseCase.ejecutar(Number(docenteId));
            const duracionMs = Date.now() - inicioConsulta;

            return res.status(200).json({
                exito: true,
                tiempoRespuestaMs: duracionMs,
                ...resultado
            });

        } catch (error) {
            // Regla CU-01: Si falla la conexión, registrar en log interno y alertar
            console.error(`[LOG ERROR BD][${new Date().toISOString()}]:`, error.message);
            return res.status(500).json({
                exito: false,
                mensaje: "Error al cargar los cursos. Reintentando..."
            });
        }
    }
}

module.exports = CursoController;