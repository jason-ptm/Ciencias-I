import unittest

from model.Errors import ErrorBD
from repl.Parser import Parser


class PruebasParser(unittest.TestCase):

    def analizar(self, texto):
        ordenes = Parser().analizar(texto)
        self.assertEqual(len(ordenes), 1)
        return ordenes[0]

    def test_crear_tabla(self):
        orden = self.analizar(
            "CREATE TABLE Alumnos (codigo INT, nombre TEXT, nota REAL, activo BOOL) USING RB")
        self.assertEqual(orden["accion"], "crear_tabla")
        self.assertEqual(orden["tabla"], "alumnos")             # nombres en minuscula
        self.assertEqual(orden["campos"], [("codigo", "int"), ("nombre", "text"),
                                           ("nota", "real"), ("activo", "bool")])
        self.assertEqual(orden["arbol"], "RB")
        self.assertIsNone(orden["clave_primaria"])

    def test_crear_tabla_con_clave_primaria_y_arbol_por_defecto(self):
        orden = self.analizar("create table t (nombre text, cedula int primary key)")
        self.assertEqual(orden["clave_primaria"], "cedula")
        self.assertEqual(orden["arbol"], "AVL")

    def test_borrar_tabla_e_indice(self):
        self.assertEqual(self.analizar("DROP TABLE t"),
                         {"accion": "borrar_tabla", "tabla": "t", "si_existe": False})
        self.assertTrue(self.analizar("DROP TABLE IF EXISTS t")["si_existe"])
        self.assertEqual(self.analizar("CREATE INDEX ON t (nota)"),
                         {"accion": "crear_indice", "tabla": "t", "campo": "nota"})

    def test_insertar_reconoce_los_cuatro_tipos(self):
        orden = self.analizar("INSERT INTO t VALUES (7, 'Ana Maria', -3.5, true)")
        self.assertEqual(orden["valores"], [7, "Ana Maria", -3.5, True])

    def test_textos_con_comillas_y_punto_y_coma(self):
        orden = self.analizar("INSERT INTO t VALUES (1, 'O''Brien; hijo', \"dice \"\"hola\"\"\")")
        self.assertEqual(orden["valores"], [1, "O'Brien; hijo", 'dice "hola"'])

    def test_seleccionar(self):
        orden = self.analizar("SELECT * FROM t")
        self.assertIsNone(orden["campos"])
        self.assertIsNone(orden["condicion"])

        orden = self.analizar("SELECT nombre, nota FROM t WHERE nota>=4.5 LIMIT 10")
        self.assertEqual(orden["campos"], ["nombre", "nota"])
        self.assertEqual(orden["limite"], 10)
        condicion = orden["condicion"]
        self.assertEqual((condicion.campo, condicion.operador, condicion.valor),
                         ("nota", ">=", 4.5))

    def test_operadores(self):
        for texto, esperado in [("=", "="), ("!=", "!="), ("<>", "!="), ("<", "<"),
                                ("<=", "<="), (">", ">"), (">=", ">=")]:
            orden = self.analizar("SELECT * FROM t WHERE x " + texto + " 3")
            self.assertEqual(orden["condicion"].operador, esperado)

    def test_between(self):
        condicion = self.analizar("SELECT * FROM t WHERE x BETWEEN 5 AND 10")["condicion"]
        self.assertEqual((condicion.operador, condicion.valor, condicion.valor_hasta),
                         ("BETWEEN", 5, 10))

    def test_actualizar_y_eliminar(self):
        orden = self.analizar("UPDATE t SET nota = 5, activo = false WHERE codigo = 3")
        self.assertEqual(orden["cambios"], {"nota": 5, "activo": False})
        self.assertEqual(orden["condicion"].valor, 3)

        orden = self.analizar("DELETE FROM t WHERE nota < 3")
        self.assertEqual(orden["accion"], "eliminar")
        self.assertEqual(orden["condicion"].operador, "<")

    def test_cargar_con_y_sin_comillas(self):
        self.assertEqual(self.analizar("LOAD 'datasets/mis datos.csv' INTO t")["ruta"],
                         "datasets/mis datos.csv")
        self.assertEqual(self.analizar("LOAD datasets/datos.csv INTO t")["ruta"],
                         "datasets/datos.csv")

    def test_arbol(self):
        self.assertEqual(self.analizar("TREE t"),
                         {"accion": "dibujar", "tabla": "t", "campo": None, "niveles": None})
        self.assertEqual(self.analizar("TREE t nota 4"),
                         {"accion": "dibujar", "tabla": "t", "campo": "nota", "niveles": 4})

    def test_varias_ordenes_en_una_linea(self):
        ordenes = Parser().analizar("SHOW TABLES; DESCRIBE t;")
        self.assertEqual([o["accion"] for o in ordenes], ["listar_tablas", "describir"])

    def test_errores_de_sintaxis(self):
        malos = [
            "SELEC * FROM t",
            "SELECT * t",
            "CREATE TABLE t (codigo fecha)",
            "CREATE TABLE t (a int PRIMARY KEY, b int PRIMARY KEY)",
            "INSERT INTO t VALUES (1, 2",
            "INSERT INTO t VALUES (hola)",
            "SELECT * FROM t WHERE x",
            "SELECT * FROM t WHERE x BETWEEN 1",
            "UPDATE t nota = 5",
            "DROP TABLE t sobra",
            "SELECT * FROM t WHERE x = 'sin cerrar",
        ]
        for texto in malos:
            with self.subTest(comando=texto):
                with self.assertRaises(ErrorBD):
                    Parser().analizar(texto)


if __name__ == "__main__":
    unittest.main()
