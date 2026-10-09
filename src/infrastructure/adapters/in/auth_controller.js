// src/infrastructure/adapters/in/auth_controller.js
// Adaptador Primario REST: Endpoint base de autenticación para HU01

const loginHandler = (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({
            exito: false,
            mensaje: "Credenciales incompletas: email y password requeridos"
        });
    }

    return res.status(200).json({
        exito: true,
        token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token_prueba_semana_7",
        rol: "DOCENTE",
        expiraEn: "60m"
    });
};

module.exports = { loginHandler };
