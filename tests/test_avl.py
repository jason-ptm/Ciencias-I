import math
import random
import unittest

from model.AVLTree import ArbolAVL
from tests.ayudas import verificar_avl


def arbol_con(claves):
    arbol = ArbolAVL()
    for clave in claves:
        arbol.insertar(clave, "dato " + str(clave))
    return arbol


class PruebasRotaciones(unittest.TestCase):

    def test_izquierda_izquierda_rota_a_la_derecha(self):
        arbol = arbol_con([30, 20, 10])
        self.assertEqual(arbol.rotaciones, ["simple derecha sobre 30"])
        self.assertEqual(arbol.raiz.clave, 20)

    def test_derecha_derecha_rota_a_la_izquierda(self):
        arbol = arbol_con([10, 20, 30])
        self.assertEqual(arbol.rotaciones, ["simple izquierda sobre 10"])
        self.assertEqual(arbol.raiz.clave, 20)

    def test_izquierda_derecha_hace_rotacion_doble(self):
        arbol = arbol_con([30, 10, 20])
        self.assertEqual(arbol.rotaciones,
                         ["simple izquierda sobre 10", "simple derecha sobre 30"])
        self.assertEqual(arbol.raiz.clave, 20)

    def test_derecha_izquierda_hace_rotacion_doble(self):
        arbol = arbol_con([10, 30, 20])
        self.assertEqual(arbol.rotaciones,
                         ["simple derecha sobre 30", "simple izquierda sobre 10"])
        self.assertEqual(arbol.raiz.clave, 20)


class PruebasAVL(unittest.TestCase):

    def test_insertar_y_buscar(self):
        arbol = arbol_con([50, 30, 70, 20, 40, 60, 80])
        self.assertEqual(arbol.buscar(40).dato, "dato 40")
        self.assertIsNone(arbol.buscar(45))
        self.assertEqual(arbol.total_nodos, 7)
        verificar_avl(arbol)

    def test_clave_repetida_no_entra(self):
        arbol = arbol_con([1, 2, 3])
        self.assertFalse(arbol.insertar(2, "otro"))
        self.assertEqual(arbol.buscar(2).dato, "dato 2")
        self.assertEqual(arbol.total_nodos, 3)

    def test_inorden_sale_ordenado(self):
        claves = [15, 3, 99, 42, 7, 61, 28]
        self.assertEqual(arbol_con(claves).claves(), sorted(claves))

    def test_sucesor(self):
        arbol = arbol_con([20, 10, 30, 25, 40])
        self.assertEqual(arbol.sucesor(10), 20)     # sube hasta un ancestro
        self.assertEqual(arbol.sucesor(20), 25)     # minimo del subarbol derecho
        self.assertIsNone(arbol.sucesor(40))        # el mayor no tiene
        self.assertIsNone(arbol.sucesor(99))        # clave que no existe

    def test_eliminar_hoja_y_nodo_con_un_hijo(self):
        arbol = arbol_con([20, 10, 30, 25])
        self.assertTrue(arbol.eliminar(10))         # hoja
        self.assertTrue(arbol.eliminar(30))         # un solo hijo
        self.assertEqual(arbol.claves(), [20, 25])
        verificar_avl(arbol)

    def test_eliminar_con_dos_hijos_usa_el_sucesor(self):
        arbol = arbol_con([50, 30, 70, 20, 40, 60, 80, 65])
        raiz = arbol.raiz
        arbol.eliminar(50)
        self.assertIs(arbol.raiz, raiz)             # el nodo se queda...
        self.assertEqual(raiz.clave, 60)            # ...con la clave del sucesor
        self.assertEqual(raiz.dato, "dato 60")
        self.assertEqual(arbol.claves(), [20, 30, 40, 60, 65, 70, 80])
        verificar_avl(arbol)

    def test_eliminar_obliga_a_rebalancear(self):
        arbol = arbol_con([20, 10, 30, 25, 40])
        arbol.limpiar_rotaciones()
        arbol.eliminar(10)
        self.assertEqual(arbol.rotaciones, ["simple izquierda sobre 20"])
        verificar_avl(arbol)

    def test_eliminar_clave_inexistente(self):
        arbol = arbol_con([1, 2, 3])
        self.assertFalse(arbol.eliminar(9))
        self.assertEqual(arbol.total_nodos, 3)

    def test_rango(self):
        arbol = arbol_con(range(0, 100, 5))
        claves = [clave for clave, dato in arbol.rango(20, 40)]
        self.assertEqual(claves, [20, 25, 30, 35, 40])
        claves = [clave for clave, dato in arbol.rango(20, 40, False, False)]
        self.assertEqual(claves, [25, 30, 35])
        claves = [clave for clave, dato in arbol.rango(None, 12)]
        self.assertEqual(claves, [0, 5, 10])
        claves = [clave for clave, dato in arbol.rango(88, None)]
        self.assertEqual(claves, [90, 95])
        self.assertEqual(arbol.rango(41, 44), [])

    def test_operaciones_al_azar_mantienen_el_invariante(self):
        azar = random.Random(11)
        arbol = ArbolAVL()
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
                verificar_avl(arbol)
        verificar_avl(arbol)
        self.assertEqual(arbol.inorden(), sorted(referencia.items()))

    def test_altura_logaritmica_con_claves_ordenadas(self):
        # el peor caso de un BST comun: aqui la altura sigue siendo O(log n)
        n = 10000
        arbol = arbol_con(range(n))
        self.assertLessEqual(arbol.altura, 1.44 * math.log2(n + 2))
        self.assertTrue(arbol.esta_equilibrado)


if __name__ == "__main__":
    unittest.main()
