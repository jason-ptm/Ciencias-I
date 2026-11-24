import math
import os
import shutil
import tempfile
import unittest

from model.Condition import Condicion
from model.Database import BaseDatos
from model.Errors import ErrorBD

CAMPOS = [("id", "int"), ("nombre", "text"), ("precio", "real"), ("disponible", "bool")]


def fila(i):
    return [i, "producto " + str(i), i * 1.5, i % 2 == 0]


class PruebasPersistencia(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta)

    def abrir(self):
        # cada llamada simula reiniciar el gestor
        return BaseDatos(self.carpeta)

    def ruta(self, archivo):
        return os.path.join(self.carpeta, archivo)

    # ---------------- recuperacion tras reinicio ----------------

    def test_los_datos_sobreviven_al_reinicio(self):
        for tipo_arbol in ("AVL", "RB"):
            with self.subTest(arbol=tipo_arbol):
                nombre = "productos_" + tipo_arbol.lower()
                tabla = self.abrir().crear_tabla(nombre, CAMPOS, tipo_arbol=tipo_arbol)
                tabla.insertar_varios([fila(i) for i in range(1, 51)])
                tabla.crear_indice("precio")
                tabla.actualizar({"nombre": "cambiado"}, Condicion("id", "=", 10))
                tabla.eliminar(Condicion("id", ">", 40))

                restaurada = self.abrir().tabla(nombre)
                self.assertEqual(restaurada.tipo_arbol, tipo_arbol)
                self.assertEqual(restaurada.esquema.campos, [c for c, t in CAMPOS])
                self.assertEqual(restaurada.total, 40)
                self.assertEqual(restaurada.buscar(10)["nombre"], "cambiado")
                self.assertIsNone(restaurada.buscar(41))
                self.assertEqual(restaurada.seleccionar()[0], tabla.seleccionar()[0])

                # el indice secundario se reconstruyo y responde
                self.assertIn("precio", restaurada.secundarios)
                registros, plan = restaurada.seleccionar(Condicion("precio", "<=", 4.5))
                self.assertEqual([r["id"] for r in registros], [1, 2, 3])
                self.assertIn("indice", plan)

    def test_la_reconstruccion_deja_altura_minima_sin_rotar(self):
        for tipo_arbol in ("AVL", "RB"):
            for cantidad in (1, 2, 10, 100, 1000):
                with self.subTest(arbol=tipo_arbol, n=cantidad):
                    bd = self.abrir()
                    tabla = bd.crear_tabla("t", CAMPOS, tipo_arbol=tipo_arbol)
                    tabla.insertar_varios([fila(i) for i in range(cantidad)])

                    arbol = self.abrir().tabla("t").primario
                    self.assertEqual(arbol.total_nodos, cantidad)
                    self.assertEqual(arbol.altura, math.ceil(math.log2(cantidad + 1)))
                    self.assertTrue(arbol.esta_equilibrado)
                    bd.borrar_tabla("t")

    def test_tabla_vacia_y_borrado_sobreviven_al_reinicio(self):
        bd = self.abrir()
        bd.crear_tabla("vacia", CAMPOS)
        bd.crear_tabla("temporal", CAMPOS)
        bd.borrar_tabla("temporal")

        bd = self.abrir()
        self.assertEqual(bd.nombres(), ["vacia"])
        self.assertEqual(bd.tabla("vacia").total, 0)
        self.assertFalse(os.path.exists(self.ruta("temporal.json")))

    def test_no_se_puede_crear_dos_veces_la_misma_tabla(self):
        bd = self.abrir()
        bd.crear_tabla("t", CAMPOS)
        with self.assertRaises(ErrorBD):
            bd.crear_tabla("t", CAMPOS)
        with self.assertRaises(ErrorBD):
            self.abrir().crear_tabla("t", CAMPOS)               # tampoco tras reiniciar

    # ---------------- atomicidad ----------------

    def romper_disco(self, tabla):
        def guardar_que_falla(datos):
            raise OSError("disco lleno (simulado)")
        tabla.almacen.guardar = guardar_que_falla

    def test_si_falla_el_guardado_la_operacion_se_revierte(self):
        for tipo_arbol in ("AVL", "RB"):
            with self.subTest(arbol=tipo_arbol):
                bd = self.abrir()
                tabla = bd.crear_tabla("t", CAMPOS, tipo_arbol=tipo_arbol)
                tabla.insertar_varios([fila(i) for i in range(1, 21)])
                tabla.crear_indice("precio")
                antes = [dict(r) for r in tabla.seleccionar()[0]]
                self.romper_disco(tabla)

                with self.assertRaises(ErrorBD):
                    tabla.insertar(fila(99))
                with self.assertRaises(ErrorBD):
                    tabla.actualizar({"precio": 0.0}, Condicion("id", "<", 10))
                with self.assertRaises(ErrorBD):
                    tabla.eliminar(Condicion("id", ">", 5))
                with self.assertRaises(ErrorBD):
                    tabla.crear_indice("nombre")

                # memoria: igual que antes de las operaciones fallidas
                self.assertEqual(tabla.seleccionar()[0], antes)
                self.assertTrue(tabla.primario.esta_equilibrado)
                self.assertNotIn("nombre", tabla.secundarios)
                registros, plan = tabla.seleccionar(Condicion("precio", "=", 0.0))
                self.assertEqual(registros, [])
                registros, plan = tabla.seleccionar(Condicion("precio", "=", 3.0))
                self.assertEqual([r["id"] for r in registros], [2])

                # disco: tambien igual
                self.assertEqual(self.abrir().tabla("t").seleccionar()[0], antes)
                bd.tablas["t"].almacen.borrar()

    def test_una_operacion_invalida_no_toca_el_archivo(self):
        tabla = self.abrir().crear_tabla("t", CAMPOS)
        tabla.insertar(fila(1))
        with open(self.ruta("t.json"), encoding="utf-8") as archivo:
            antes = archivo.read()

        with self.assertRaises(ErrorBD):
            tabla.insertar(fila(1))                             # clave repetida
        with self.assertRaises(ErrorBD):
            tabla.insertar([2, "x", "caro", True])              # tipo malo

        with open(self.ruta("t.json"), encoding="utf-8") as archivo:
            self.assertEqual(archivo.read(), antes)

    # ---------------- politica de recuperacion ----------------

    def test_escritura_interrumpida_se_descarta(self):
        tabla = self.abrir().crear_tabla("t", CAMPOS)
        tabla.insertar(fila(1))
        # el programa murio escribiendo el temporal, antes de renombrarlo
        with open(self.ruta("t.json.tmp"), "w", encoding="utf-8") as archivo:
            archivo.write('{"tabla": "t", "registros": [[1, "a medio escr')

        bd = self.abrir()
        self.assertEqual(bd.tabla("t").total, 1)                # ultimo estado valido
        self.assertFalse(os.path.exists(self.ruta("t.json.tmp")))
        self.assertEqual(len(bd.avisos), 1)

    def test_un_archivo_danado_no_tumba_las_demas_tablas(self):
        bd = self.abrir()
        bd.crear_tabla("buena", CAMPOS).insertar(fila(1))
        with open(self.ruta("mala.json"), "w", encoding="utf-8") as archivo:
            archivo.write("esto no es JSON")

        bd = self.abrir()
        self.assertEqual(bd.nombres(), ["buena"])
        self.assertEqual(bd.tabla("buena").total, 1)
        self.assertEqual(len(bd.avisos), 1)


if __name__ == "__main__":
    unittest.main()
