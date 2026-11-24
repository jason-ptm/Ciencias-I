import unittest

from model.Condition import Condicion
from model.Errors import ErrorBD
from model.Schema import Esquema
from model.Table import Tabla
from tests.ayudas import verificar_bst

CAMPOS = [("codigo", "int"), ("nombre", "text"), ("promedio", "real"), ("activo", "bool")]
FILAS = [
    [5, "Ana", 4.5, True],
    [2, "Luis", 3.0, True],
    [8, "Sofia", 4.5, False],
    [1, "Mateo", 2.8, True],
    [9, "Paula", 3.9, True],
    [4, "Daniel", 3.0, False],
]


def tabla_con_datos(tipo_arbol):
    tabla = Tabla("estudiantes", Esquema(CAMPOS), tipo_arbol)   # sin almacen: en memoria
    tabla.insertar_varios(FILAS)
    return tabla


def codigos(registros):
    return [registro["codigo"] for registro in registros]


class PruebasTabla(unittest.TestCase):
    """Cada prueba corre dos veces: con indice AVL y con indice Rojo-Negro."""

    def con_cada_arbol(self):
        for tipo_arbol in ("AVL", "RB"):
            with self.subTest(arbol=tipo_arbol):
                yield tabla_con_datos(tipo_arbol)

    # ---------------- esquema ----------------

    def test_esquema_rechaza_definiciones_invalidas(self):
        with self.assertRaises(ErrorBD):
            Esquema([])
        with self.assertRaises(ErrorBD):
            Esquema([("a", "int"), ("a", "text")])              # campo repetido
        with self.assertRaises(ErrorBD):
            Esquema([("a", "fecha")])                           # tipo desconocido
        with self.assertRaises(ErrorBD):
            Esquema([("a", "int")], clave_primaria="b")         # clave inexistente

    # ---------------- insert ----------------

    def test_insertar_valida_tipos_y_cantidad(self):
        for tabla in self.con_cada_arbol():
            with self.assertRaises(ErrorBD):
                tabla.insertar([20, "Eva", "cuatro", True])     # real mal
            with self.assertRaises(ErrorBD):
                tabla.insertar(["20", "Eva", 4.0, True])        # int mal
            with self.assertRaises(ErrorBD):
                tabla.insertar([20, "Eva", 4.0, 1])             # bool mal
            with self.assertRaises(ErrorBD):
                tabla.insertar([20, "Eva", 4.0])                # falta un valor
            self.assertEqual(tabla.total, len(FILAS))

    def test_entero_en_campo_real_se_guarda_como_real(self):
        for tabla in self.con_cada_arbol():
            tabla.insertar([20, "Eva", 4, True])
            self.assertIsInstance(tabla.buscar(20)["promedio"], float)

    def test_clave_primaria_repetida(self):
        for tabla in self.con_cada_arbol():
            with self.assertRaises(ErrorBD):
                tabla.insertar([5, "Otra", 1.0, True])
            self.assertEqual(tabla.buscar(5)["nombre"], "Ana")

    def test_insertar_varios_es_todo_o_nada(self):
        for tabla in self.con_cada_arbol():
            lote = [[30, "A", 1.0, True], [31, "B", "malo", True]]
            with self.assertRaises(ErrorBD):
                tabla.insertar_varios(lote)
            self.assertIsNone(tabla.buscar(30))
            self.assertEqual(tabla.total, len(FILAS))

    # ---------------- select ----------------

    def test_seleccionar_todo_sale_ordenado_por_clave(self):
        for tabla in self.con_cada_arbol():
            registros, plan = tabla.seleccionar()
            self.assertEqual(codigos(registros), [1, 2, 4, 5, 8, 9])

    def test_buscar_por_clave_primaria_usa_el_indice(self):
        for tabla in self.con_cada_arbol():
            registros, plan = tabla.seleccionar(Condicion("codigo", "=", 8))
            self.assertEqual(codigos(registros), [8])
            self.assertIn("clave primaria", plan)
            registros, plan = tabla.seleccionar(Condicion("codigo", "=", 77))
            self.assertEqual(registros, [])

    def test_rangos_sobre_la_clave_primaria(self):
        for tabla in self.con_cada_arbol():
            casos = [
                (Condicion("codigo", "BETWEEN", 2, 8), [2, 4, 5, 8]),
                (Condicion("codigo", ">", 5), [8, 9]),
                (Condicion("codigo", ">=", 5), [5, 8, 9]),
                (Condicion("codigo", "<", 4), [1, 2]),
                (Condicion("codigo", "<=", 4), [1, 2, 4]),
            ]
            for condicion, esperado in casos:
                registros, plan = tabla.seleccionar(condicion)
                self.assertEqual(codigos(registros), esperado, condicion)
                self.assertIn("clave primaria", plan)

    def test_campo_sin_indice_recorre_todo(self):
        for tabla in self.con_cada_arbol():
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 4.5))
            self.assertEqual(codigos(registros), [5, 8])
            self.assertIn("recorrido completo", plan)

    def test_indice_secundario_igualdad_y_rango(self):
        for tabla in self.con_cada_arbol():
            tabla.crear_indice("promedio")
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 4.5))
            self.assertEqual(codigos(registros), [5, 8])
            self.assertIn("indice", plan)
            self.assertIn("promedio", plan)
            registros, plan = tabla.seleccionar(Condicion("promedio", "BETWEEN", 3, 4))
            self.assertEqual(codigos(registros), [2, 4, 9])     # 3.0, 3.0, 3.9
            registros, plan = tabla.seleccionar(Condicion("promedio", "<", 3))
            self.assertEqual(codigos(registros), [1])

    def test_distinto_de(self):
        for tabla in self.con_cada_arbol():
            registros, plan = tabla.seleccionar(Condicion("activo", "!=", True))
            self.assertEqual(codigos(registros), [4, 8])

    def test_condicion_con_campo_o_tipo_invalido(self):
        for tabla in self.con_cada_arbol():
            with self.assertRaises(ErrorBD):
                tabla.seleccionar(Condicion("edad", "=", 3))
            with self.assertRaises(ErrorBD):
                tabla.seleccionar(Condicion("codigo", "=", "cinco"))

    # ---------------- update ----------------

    def test_actualizar_un_registro(self):
        for tabla in self.con_cada_arbol():
            cantidad = tabla.actualizar({"nombre": "Ana Maria"}, Condicion("codigo", "=", 5))
            self.assertEqual(cantidad, 1)
            self.assertEqual(tabla.buscar(5)["nombre"], "Ana Maria")
            self.assertEqual(tabla.buscar(5)["promedio"], 4.5)  # lo demas no cambia

    def test_actualizar_varios_mantiene_el_indice_secundario(self):
        for tabla in self.con_cada_arbol():
            tabla.crear_indice("promedio")
            cantidad = tabla.actualizar({"promedio": 5.0}, Condicion("promedio", "=", 3.0))
            self.assertEqual(cantidad, 2)
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 3.0))
            self.assertEqual(registros, [])
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 5.0))
            self.assertEqual(codigos(registros), [2, 4])
            self.assertFalse(tabla.secundarios["promedio"].contiene(3.0))
            verificar_bst(tabla.secundarios["promedio"])

    def test_actualizar_rechaza_clave_primaria_y_tipos_malos(self):
        for tabla in self.con_cada_arbol():
            with self.assertRaises(ErrorBD):
                tabla.actualizar({"codigo": 99}, Condicion("codigo", "=", 5))
            with self.assertRaises(ErrorBD):
                tabla.actualizar({"promedio": "alto"}, Condicion("codigo", "=", 5))
            self.assertEqual(tabla.buscar(5)["promedio"], 4.5)

    # ---------------- delete ----------------

    def test_eliminar_por_clave(self):
        for tabla in self.con_cada_arbol():
            self.assertEqual(tabla.eliminar(Condicion("codigo", "=", 5)), 1)
            self.assertIsNone(tabla.buscar(5))
            self.assertEqual(tabla.eliminar(Condicion("codigo", "=", 5)), 0)
            self.assertTrue(tabla.primario.esta_equilibrado)

    def test_eliminar_por_condicion_limpia_los_indices(self):
        for tabla in self.con_cada_arbol():
            tabla.crear_indice("promedio")
            self.assertEqual(tabla.eliminar(Condicion("activo", "=", False)), 2)
            registros, plan = tabla.seleccionar()
            self.assertEqual(codigos(registros), [1, 2, 5, 9])
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 4.5))
            self.assertEqual(codigos(registros), [5])
            registros, plan = tabla.seleccionar(Condicion("promedio", "=", 3.0))
            self.assertEqual(codigos(registros), [2])
            verificar_bst(tabla.primario)
            verificar_bst(tabla.secundarios["promedio"])

    def test_eliminar_todo(self):
        for tabla in self.con_cada_arbol():
            self.assertEqual(tabla.eliminar(), len(FILAS))
            self.assertEqual(tabla.total, 0)

    # ---------------- indices ----------------

    def test_crear_indice_invalido(self):
        for tabla in self.con_cada_arbol():
            tabla.crear_indice("promedio")
            with self.assertRaises(ErrorBD):
                tabla.crear_indice("promedio")                  # ya existe
            with self.assertRaises(ErrorBD):
                tabla.crear_indice("codigo")                    # es la clave primaria
            with self.assertRaises(ErrorBD):
                tabla.crear_indice("edad")                      # no existe


if __name__ == "__main__":
    unittest.main()
