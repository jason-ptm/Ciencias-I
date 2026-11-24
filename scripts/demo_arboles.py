"""Demostracion de los dos arboles: mismas claves, dos formas de balancear.

    python scripts/demo_arboles.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.AVLTree import ArbolAVL
from model.RBTree import ArbolRojoNegro

CLAVES = [10, 20, 30, 40, 50, 25, 5, 4, 3, 35, 45, 60]


def titulo_seccion(texto):
    print("")
    print("=" * 64)
    print(texto)
    print("=" * 64)


def insertar_paso_a_paso(arbol, claves):
    for clave in claves:
        arbol.limpiar_rotaciones()
        arbol.insertar(clave)
        if len(arbol.rotaciones) == 0:
            print("insertar " + str(clave).rjust(2))
        else:
            print("insertar " + str(clave).rjust(2) + "   ->  rotacion " +
                  ", ".join(arbol.rotaciones))


def resumen(arbol):
    print("Inorden:", arbol.claves())
    print("Altura:", arbol.altura, "  Nodos:", arbol.total_nodos,
          "  Equilibrado:", arbol.esta_equilibrado)


def eliminar_y_mostrar(arbol, clave, nombre):
    arbol.limpiar_rotaciones()
    print("")
    print("Eliminar " + str(clave) + " (tiene dos hijos): lo reemplaza su sucesor, " +
          str(arbol.sucesor(clave)))
    arbol.eliminar(clave)
    arbol.reporte_rotaciones()
    arbol.dibujar(nombre + " despues de eliminar " + str(clave))
    resumen(arbol)


if __name__ == "__main__":
    avl = ArbolAVL()
    rojinegro = ArbolRojoNegro()

    titulo_seccion("INSERCION EN EL AVL (balancea por alturas)")
    insertar_paso_a_paso(avl, CLAVES)
    print("")
    avl.dibujar("ARBOL AVL BALANCEADO")
    resumen(avl)

    titulo_seccion("INSERCION EN EL ROJO-NEGRO (balancea por colores)")
    insertar_paso_a_paso(rojinegro, CLAVES)
    print("")
    rojinegro.dibujar("ARBOL ROJO-NEGRO BALANCEADO")
    resumen(rojinegro)

    titulo_seccion("SUCESOR")
    print("El sucesor es la siguiente clave del inorden.")
    for clave in [3, 25, 30, 60]:
        print("clave " + str(clave).rjust(2) + "   sucesor: " + str(avl.sucesor(clave)))

    titulo_seccion("ELIMINACION CON LA REGLA DEL SUCESOR")
    eliminar_y_mostrar(avl, 30, "AVL")
    eliminar_y_mostrar(rojinegro, 20, "ROJO-NEGRO")
