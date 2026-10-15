// src/infrastructure/server.js
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const CursoRepository = require('./adapters/out/curso_repository');
const ObtenerCursosDocente = require('../application/usecases/obtener_cursos_docente');
const CursoController = require('./adapters/in/curso_controller');

const cursoRepo = new CursoRepository();
const obtenerCursosUseCase = new ObtenerCursosDocente(cursoRepo);
const cursoController = new CursoController(obtenerCursosUseCase);

const PORT = 3000;

const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        return res.end();
    }

    // Servir Interfaz Frontend
    if (req.method === 'GET' && (parsedUrl.pathname === '/' || parsedUrl.pathname === '/index.html')) {
        const filePath = path.join(__dirname, '../../public/index.html');
        fs.readFile(filePath, (err, content) => {
            if (err) {
                res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
                return res.end('Error al cargar interfaz');
            }
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            return res.end(content);
        });
        return;
    }

    // Endpoint API
    if (req.method === 'GET' && parsedUrl.pathname === '/api/cursos') {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        const fakeReq = { query: parsedUrl.query };
        const fakeRes = {
            status: (code) => {
                res.statusCode = code;
                return {
                    json: (data) => res.end(JSON.stringify(data, null, 2))
                };
            }
        };
        return await cursoController.listarCursos(fakeReq, fakeRes);
    }

    res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ exito: false, mensaje: 'No encontrado' }));
});

server.listen(PORT, () => {
    console.log(`Servidor en ejecución: http://localhost:${PORT}`);
});