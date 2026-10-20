"""Gráfico de línea simple en SVG para el historial de riesgo (HU-13).

Se dibuja en el servidor (sin librerías JavaScript): el adaptador web calcula las coordenadas
y la plantilla solo pinta. Un gráfico por indicador, cada uno con su línea de umbral.
"""
ANCHO, ALTO = 640, 170
MARGEN_IZQ, MARGEN_DER, MARGEN_SUP, MARGEN_INF = 60, 26, 16, 30


def linea(semanas: list, valor, minimo: float, maximo: float, umbral: float, etiqueta_umbral: str,
          formato: str = "{:g}") -> dict:
    """Devuelve lo necesario para dibujar: puntos, línea de umbral, ejes y etiquetas."""
    n = len(semanas)
    ancho_util = ANCHO - MARGEN_IZQ - MARGEN_DER
    alto_util = ALTO - MARGEN_SUP - MARGEN_INF

    def x(i):
        return round(MARGEN_IZQ + (ancho_util * i / (n - 1) if n > 1 else ancho_util / 2), 1)

    def y(v):
        return round(MARGEN_SUP + alto_util * (maximo - v) / (maximo - minimo), 1)

    puntos = [{"x": x(i), "y": y(valor(s)), "texto": formato.format(valor(s)), "semana": s.lunes.strftime("%d-%m")}
              for i, s in enumerate(semanas) if valor(s) is not None]
    marcas = [{"x": x(i), "texto": s.lunes.strftime("%d-%m")} for i, s in enumerate(semanas)]
    paso = max(1, -(-len(marcas) // 8))  # como máximo ~8 etiquetas en el eje X
    return {
        "ancho": ANCHO, "alto": ALTO, "izq": MARGEN_IZQ, "der": ANCHO - MARGEN_DER,
        "base": ALTO - MARGEN_INF, "tope": MARGEN_SUP,
        "polilinea": " ".join(f"{p['x']},{p['y']}" for p in puntos),
        "puntos": puntos,
        "umbral": {"y": y(umbral), "texto": etiqueta_umbral},
        "eje_y": [{"y": y(v), "texto": formato.format(v)} for v in (minimo, maximo)],
        "marcas": marcas[::paso],
    }
