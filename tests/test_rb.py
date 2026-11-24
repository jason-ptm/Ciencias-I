import math
import random
import unittest

from model.RBNode import NEGRO, ROJO
from model.RBTree import ArbolRojoNegro
from tests.ayudas import verificar_rojinegro


def arbol_con(claves):
    arbol = ArbolRojoNegro()
    for clave in claves:
        arbol.insertar(clave, "dato " + str(clave))
    return arbol


class PruebasInsercion(unittest.TestCase):

    def test_la_raiz_siempre_es_negra(self):
        arbol = arbol_con([10])
        self.assertEqual(arbol.raiz.color, NEGRO)

    def test_tio_rojo_solo_recolorea(self):
        arbol = arbol_con([20, 10, 30, 5])
        self.assertEqual(arbol.rotaciones, [])
        self.assertEqual(arbol.buscar(10).color, NEGRO)
        self.assertEqual(arbol.buscar(30).color, NEGRO)
        self.assertEqual(arbol.buscar(5).color, ROJO)
        verificar_rojinegro(arbol)

    def test_linea_rota_el_abuelo(self):
        arbol = arbol_con([10, 20, 30])
        self.assertEqual(arbol.rotaciones, ["simple izquierda sobre 10"])
        self.assertEqual(arbol.raiz.clave, 20)
        self.assertEqual(arbol.raiz.color, NEGRO)
        self.assertEqual(arbol.buscar(10).color, ROJO)
        self.assertEqual(arbol.buscar(30).color, ROJO)

    def test_triangulo_hace_rotacion_doble(self):
        arbol = arbol_con([10, 30, 20])
        self.assertEqual(arbol.rotaciones,
                         ["simple derecha sobre 30", "simple izquierda sobre 10"])
        self.assertEqual(arbol.raiz.clave, 20)
        verificar_rojinegro(arbol)


class PruebasRojoNegro(unittest.TestCase):

    def test_insertar_y_buscar(self):
        arbol = arbol_con([50, 30, 70, 20, 40, 60, 80])
        self.assertEqual(arbol.buscar(60).dato, "dato 60")
        self.assertIsNone(arbol.buscar(65))
        verificar_rojinegro(arbol)

    def test_clave_repetida_no_entra(self):
        arbol = arbol_con([1, 2, 3])
        self.assertFalse(arbol.insertar(3, "otro"))
        self.assertEqual(arbol.total_nodos, 3)

    def test_inorden_y_sucesor(self):
        claves = [15, 3, 99, 42, 7, 61, 28]
        arbol = arbol_con(claves)
        ordenadas = sorted(claves)
        self.assertEqual(arbol.claves(), ordenadas)
        for actual, siguiente in zip(ordenadas, ordenadas[1:] + [None]):
            self.assertEqual(arbol.sucesor(actual), siguiente)

    def test_eliminar_con_dos_hijos_usa_el_sucesor(self):
        arbol = arbol_con([50, 30, 70, 20, 40, 60, 80, 65])
        nodo = arbol.buscar(50)
        arbol.eliminar(50)
        self.assertEqual(nodo.clave, 60)            # recibio la clave del sucesor
        self.assertEqual(arbol.claves(), [20, 30, 40, 60, 65, 70, 80])
        verificar_rojinegro(arbol)

    def test_eliminar_hasta_vaciar(self):
        claves = list(range(1, 64))
        arbol = arbol_con(claves)
        random.Random(5).shuffle(claves)
        for clave in claves:
            self.assertTrue(arbol.eliminar(clave))
            verificar_rojinegro(arbol)
        self.assertIsNone(arbol.raiz)
        self.assertEqual(arbol.total_nodos, 0)

    def test_eliminar_clave_inexistente(self):
        arbol = arbol_con([1, 2, 3])
        self.assertFalse(arbol.eliminar(9))

    def test_rango(self):
        arbol = arbol_con(range(0, 100, 5))
        claves = [clave for clave, dato in arbol.rango(20, 40)]
        self.assertEqual(claves, [20, 25, 30, 35, 40])
        claves = [clave for clave, dato in arbol.rango(20, 40, False, False)]
        self.assertEqual(claves, [25, 30, 35])

    def test_operaciones_al_azar_mantienen_los_invariantes(self):
        azar = random.Random(23)
        arbol = ArbolRojoNegro()
        referencia = {}
        for paso in range(3000):
            clave = azar.randint(0, 300)
            if azar.random() < 0.6:
                self.assertEqual(arbol.insertar(clave, paso), clave not in referencia)
                referencia.setdefault(clave, paso)
            else:
                self.assertEqual(arbol.eliminar(clave), clave in referencia)
                referencia.pop(clave, None)
            if paso % 50 == 0:
                verificar_rojinegro(arbol)
        verificar_rojinegro(arbol)
        self.assertEqual(arbol.inorden(), sorted(referencia.items()))

    def test_altura_logaritmica_con_claves_ordenadas(self):
        n = 10000
        arbol = arbol_con(range(n))
        self.assertLessEqual(arbol.altura, 2 * math.log2(n + 1))
        self.assertTrue(arbol.esta_equilibrado)


if __name__ == "__main__":
    unittest.main()
