"""Genera los dos datasets de prueba en datasets/ (siempre los mismos datos).

    python scripts/generar_datasets.py
"""
import csv
import os
import random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "datasets")

NOMBRES = ["Ana", "Luis", "Camila", "Andres", "Sofia", "Mateo", "Valentina", "Daniel",
           "Laura", "Santiago", "Paula", "Felipe", "Mariana", "Nicolas", "Juliana"]
APELLIDOS = ["Rojas", "Gomez", "Martinez", "Castro", "Vargas", "Moreno", "Suarez",
             "Pardo", "Leon", "Cardenas", "Rincon", "Beltran", "Acosta", "Mejia"]
CARRERAS = ["Sistemas", "Electronica", "Industrial", "Catastral", "Electrica"]

CATEGORIAS = {
    "papeleria": ["Cuaderno", "Lapicero", "Resaltador", "Carpeta", "Borrador"],
    "tecnologia": ["Teclado", "Mouse", "Monitor", "Audifonos", "Memoria USB"],
    "hogar": ["Lampara", "Almohada", "Sarten", "Toalla", "Escoba"],
    "deportes": ["Balon", "Guantes", "Cuerda", "Termo", "Rodilleras"],
    "alimentos": ["Cafe", "Arroz", "Chocolate", "Galletas", "Avena"],
}
MARCAS = ["Andina", "Norte", "Sabana", "Monserrate", "Pacifico", "Tequendama"]


def escribir(nombre, encabezado, filas):
    os.makedirs(CARPETA, exist_ok=True)
    ruta = os.path.join(CARPETA, nombre)
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(encabezado)
        escritor.writerows(filas)
    print(nombre + ": " + str(len(filas)) + " filas")


def estudiantes(cantidad):
    azar = random.Random(2026)
    codigos = list(range(2024001, 2024001 + cantidad))
    azar.shuffle(codigos)                       # desordenados: el arbol los ordena
    filas = []
    for codigo in codigos:
        filas.append([
            codigo,
            azar.choice(NOMBRES) + " " + azar.choice(APELLIDOS),
            azar.choice(CARRERAS),
            azar.randint(1, 10),
            round(azar.uniform(2.5, 5.0), 1),
            "true" if azar.random() < 0.85 else "false",
        ])
    return filas


def productos(cantidad):
    azar = random.Random(1948)
    ids = list(range(1, cantidad + 1))
    azar.shuffle(ids)
    filas = []
    for identificador in ids:
        categoria = azar.choice(list(CATEGORIAS))
        nombre = azar.choice(CATEGORIAS[categoria]) + " " + azar.choice(MARCAS)
        stock = azar.randint(0, 500)
        filas.append([
            identificador,
            nombre,
            categoria,
            round(azar.uniform(1500, 950000), 2),
            stock,
            "true" if stock > 0 else "false",
        ])
    return filas


if __name__ == "__main__":
    escribir("estudiantes_pequeno.csv",
             ["codigo", "nombre", "carrera", "semestre", "promedio", "activo"],
             estudiantes(25))
    escribir("productos_mediano.csv",
             ["id", "nombre", "categoria", "precio", "stock", "disponible"],
             productos(3000))
