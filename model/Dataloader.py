import csv

from model.Errors import ErrorBD


def cargar_csv(tabla, ruta):
    """Inserta en la tabla todas las filas de un CSV, o ninguna si algo falla.

    El encabezado debe traer los mismos campos del esquema (en cualquier orden).
    """
    esquema = tabla.esquema
    try:
        archivo = open(ruta, "r", newline="", encoding="utf-8-sig")
    except OSError as error:
        raise ErrorBD("no se pudo abrir '" + ruta + "' (" + str(error) + ")")

    with archivo:
        lector = csv.DictReader(archivo)
        encabezado = [c.strip().lower() for c in (lector.fieldnames or [])]
        if sorted(encabezado) != sorted(esquema.campos):
            raise ErrorBD("el encabezado del CSV debe ser: " + ", ".join(esquema.campos))
        lector.fieldnames = encabezado

        filas = []
        for numero, fila in enumerate(lector, start=2):     # la linea 1 es el encabezado
            try:
                filas.append([esquema.desde_texto(c, fila[c] or "") for c in esquema.campos])
            except ErrorBD as error:
                raise ErrorBD("linea " + str(numero) + " del CSV: " + str(error))

    return tabla.insertar_varios(filas)
