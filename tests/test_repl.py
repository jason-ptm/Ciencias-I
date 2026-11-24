import io
import os
import shutil
import tempfile
import unittest

from rich.console import Console

from repl.REPL import REPL

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEQUENO = os.path.join(RAIZ, "datasets", "estudiantes_pequeno.csv")
MEDIANO = os.path.join(RAIZ, "datasets", "productos_mediano.csv")


class PruebasREPL(unittest.TestCase):
    """De punta a punta: comandos de texto -> parser -> tablas -> disco."""

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()
        self.abrir()

    def tearDown(self):
        shutil.rmtree(self.carpeta)

    def abrir(self):
        # cada llamada simula reiniciar el gestor
        self.salida = io.StringIO()
        self.repl = REPL(self.carpeta, Console(file=self.salida, width=200))

    def ejecutar(self, comando):
        self.salida.seek(0)
        self.salida.truncate()
        correcto = self.repl.ejecutar(comando)
        return correcto, self.salida.getvalue()

    def bien(self, comando):
        correcto, texto = self.ejecutar(comando)
        self.assertTrue(correcto, texto)
        return texto

    def test_crud_completo_y_reinicio(self):
        self.bien("CREATE TABLE notas (codigo int, nombre text, nota real, activo bool)")
        self.bien("INSERT INTO notas VALUES (1, 'Ana', 4.5, true)")
        self.bien("INSERT INTO notas VALUES (2, 'Luis', 2.9, true)")
        self.bien("INSERT INTO notas VALUES (3, 'Sofia', 3.8, false)")

        texto = self.bien("SELECT * FROM notas WHERE codigo = 2")
        self.assertIn("Luis", texto)
        self.assertIn("1 registro(s)", texto)

        self.assertIn("1 registro(s) actualizado(s)",
                      self.bien("UPDATE notas SET nota = 3.0 WHERE codigo = 2"))
        self.assertIn("1 registro(s) eliminado(s)",
                      self.bien("DELETE FROM notas WHERE activo = false"))

        self.abrir()                                            # reinicio
        texto = self.bien("SELECT * FROM notas")
        self.assertIn("2 registro(s)", texto)
        self.assertIn("3.0", texto)
        self.assertNotIn("Sofia", texto)

    def test_los_errores_se_informan_sin_tumbar_el_repl(self):
        self.bien("CREATE TABLE t (id int, nombre text)")
        for comando in ["INSERT INTO t VALUES ('uno', 'x')",       # tipo malo
                        "SELECT * FROM no_existe",
                        "SELECT edad FROM t",
                        "ESTO NO ES UN COMANDO"]:
            correcto, texto = self.ejecutar(comando)
            self.assertFalse(correcto)
            self.assertIn("Error:", texto)
        self.assertIn("0 registro(s)", self.bien("SELECT * FROM t"))

    def test_dataset_pequeno_en_avl(self):
        self.bien("CREATE TABLE estudiantes (codigo int, nombre text, carrera text, "
                  "semestre int, promedio real, activo bool) USING AVL")
        self.assertIn("25 registro(s) cargado(s)",
                      self.bien("LOAD '" + PEQUENO + "' INTO estudiantes"))
        self.bien("CREATE INDEX ON estudiantes (promedio)")
        texto = self.bien("SELECT * FROM estudiantes WHERE promedio >= 4.5")
        self.assertIn("indice AVL sobre 'promedio'", texto)
        texto = self.bien("TREE estudiantes")
        self.assertIn("raiz", texto)
        self.assertIn("equilibrado: True", texto)

    def test_dataset_mediano_en_rojinegro_y_reinicio(self):
        self.bien("CREATE TABLE productos (id int, nombre text, categoria text, "
                  "precio real, stock int, disponible bool) USING RB")
        self.assertIn("3000 registro(s) cargado(s)",
                      self.bien("LOAD '" + MEDIANO + "' INTO productos"))
        self.bien("CREATE INDEX ON productos (precio)")
        self.bien("DELETE FROM productos WHERE id > 2500")

        self.abrir()                                            # reinicio
        tabla = self.repl.bd.tabla("productos")
        self.assertEqual(tabla.total, 2500)
        self.assertTrue(tabla.primario.esta_equilibrado)
        texto = self.bien("SELECT id FROM productos WHERE id BETWEEN 100 AND 104")
        self.assertIn("5 registro(s)", texto)
        self.assertIn("indice RB de la clave primaria", texto)

    def test_cargar_csv_repetido_no_inserta_nada(self):
        self.bien("CREATE TABLE estudiantes (codigo int, nombre text, carrera text, "
                  "semestre int, promedio real, activo bool)")
        self.bien("LOAD '" + PEQUENO + "' INTO estudiantes")
        correcto, texto = self.ejecutar("LOAD '" + PEQUENO + "' INTO estudiantes")
        self.assertFalse(correcto)                              # claves repetidas
        self.assertEqual(self.repl.bd.tabla("estudiantes").total, 25)


if __name__ == "__main__":
    unittest.main()
