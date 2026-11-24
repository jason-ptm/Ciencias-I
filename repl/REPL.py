import time

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from model.Database import BaseDatos
from model.Dataloader import cargar_csv
from model.Errors import ErrorBD
from repl.Parser import Parser

FILAS_POR_DEFECTO = 30          # tope de filas en pantalla si no hay LIMIT
NODOS_ARBOL_COMPLETO = 63       # hasta aqui TREE dibuja el arbol entero
NIVELES_POR_DEFECTO = 5

AYUDA = [
    ("Esquemas", """\
  CREATE TABLE t (campo tipo [PRIMARY KEY], ...) [USING AVL|RB]
  DROP TABLE [IF EXISTS] t
  CREATE INDEX ON t (campo)
  SHOW TABLES            DESCRIBE t"""),
    ("Datos", """\
  INSERT INTO t VALUES (v1, v2, ...)
  SELECT * | campo, ... FROM t [WHERE condicion] [LIMIT n]
  UPDATE t SET campo = valor, ... [WHERE condicion]
  DELETE FROM t [WHERE condicion]"""),
    ("Condiciones", """\
  campo = v   campo != v   campo < v   campo <= v   campo > v   campo >= v
  campo BETWEEN a AND b"""),
    ("Arbol y archivos", """\
  TREE t [campo] [niveles]     dibuja el indice (clave primaria si no hay campo)
  LOAD 'archivo.csv' INTO t    carga un CSV completo o nada
  SOURCE 'archivo.sql'         ejecuta un archivo de comandos
  HELP                   EXIT
Tipos: int, text, real, bool.   Valores: 12   3.5   'texto'   true   false"""),
]


def mostrar(valor):
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return escape(str(valor))


class REPL:
    """Linea de comandos: lee, manda al Parser, ejecuta sobre la base y muestra."""

    def __init__(self, directorio="data", consola=None):
        self.consola = consola if consola is not None else Console()
        self.parser = Parser()
        self.bd = BaseDatos(directorio)
        self.activo = True

    # =========================================================
    # CICLO PRINCIPAL
    # =========================================================

    def iniciar(self):
        self.consola.print("[bold]Motor de base de datos con arboles autobalanceados[/bold]")
        self.consola.print("Tablas restauradas: " + str(len(self.bd.tablas)) +
                           ".  Escriba HELP para ver los comandos.")
        for aviso in self.bd.avisos:
            self.consola.print("[yellow]aviso:[/yellow] " + escape(aviso))

        while self.activo:
            try:
                linea = input("bd> ")
            except (EOFError, KeyboardInterrupt):
                break
            self.ejecutar(linea)
        self.consola.print("Hasta luego.")

    def ejecutar(self, linea):
        """Ejecuta una linea. Devuelve False si hubo error."""
        if linea.strip() == "" or linea.strip().startswith("--"):
            return True                         # vacia o comentario
        try:
            for orden in self.parser.analizar(linea):
                getattr(self, "_" + orden["accion"])(orden)
            return True
        except ErrorBD as error:
            self.consola.print("[red]Error:[/red] " + escape(str(error)))
            return False

    def ejecutar_script(self, ruta):
        """Ejecuta un archivo linea por linea y se detiene en el primer error."""
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                lineas = archivo.read().splitlines()
        except OSError as error:
            raise ErrorBD("no se pudo abrir '" + ruta + "' (" + str(error) + ")")

        for numero, linea in enumerate(lineas, start=1):
            if linea.strip() == "" or linea.strip().startswith("--"):
                continue
            self.consola.print("[dim]bd> " + escape(linea.strip()) + "[/dim]")
            if not self.ejecutar(linea):
                raise ErrorBD("el script se detuvo en la linea " + str(numero))
            if not self.activo:
                break

    # =========================================================
    # ESQUEMAS
    # =========================================================

    def _crear_tabla(self, orden):
        tabla = self.bd.crear_tabla(orden["tabla"], orden["campos"],
                                    orden["clave_primaria"], orden["arbol"])
        self.consola.print("Tabla '" + tabla.nombre + "' creada (arbol " + tabla.tipo_arbol +
                           ", clave primaria '" + tabla.esquema.clave_primaria + "').")

    def _borrar_tabla(self, orden):
        if orden["si_existe"] and orden["tabla"] not in self.bd.tablas:
            return
        self.bd.borrar_tabla(orden["tabla"])
        self.consola.print("Tabla '" + orden["tabla"] + "' eliminada.")

    def _crear_indice(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        tabla.crear_indice(orden["campo"])
        self.consola.print("Indice " + tabla.tipo_arbol + " creado sobre '" +
                           orden["campo"] + "' (" +
                           str(tabla.secundarios[orden["campo"]].total_nodos) +
                           " valores distintos).")

    def _listar_tablas(self, orden):
        if len(self.bd.tablas) == 0:
            self.consola.print("No hay tablas.")
            return
        vista = Table("tabla", "arbol", "registros", "altura", "indices")
        for nombre in self.bd.nombres():
            t = self.bd.tabla(nombre)
            vista.add_row(nombre, t.tipo_arbol, str(t.total), str(t.primario.altura),
                          ", ".join(sorted(t.secundarios)) or "-")
        self.consola.print(vista)

    def _describir(self, orden):
        t = self.bd.tabla(orden["tabla"])
        vista = Table("campo", "tipo", "indice")
        for campo in t.esquema.campos:
            if campo == t.esquema.clave_primaria:
                indice = "clave primaria"
            elif campo in t.secundarios:
                indice = "secundario"
            else:
                indice = "-"
            vista.add_row(campo, t.esquema.tipos[campo], indice)
        self.consola.print(vista)
        self.consola.print("arbol " + t.tipo_arbol + " · " + str(t.total) + " registros · altura " +
                           str(t.primario.altura) + " · equilibrado: " +
                           str(t.primario.esta_equilibrado))

    # =========================================================
    # DATOS
    # =========================================================

    def _informar_rotaciones(self, tabla):
        rotaciones = tabla.primario.rotaciones
        if len(rotaciones) == 0:
            return
        if len(rotaciones) <= 4:
            detalle = ", ".join("rotacion " + r for r in rotaciones)
        else:
            detalle = str(len(rotaciones)) + " rotaciones"
        self.consola.print("[dim]  balanceo " + tabla.tipo_arbol + ": " +
                           escape(detalle) + "[/dim]")

    def _insertar(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        tabla.insertar(orden["valores"])
        self.consola.print("1 registro insertado.")
        self._informar_rotaciones(tabla)

    def _seleccionar(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        campos = orden["campos"] or tabla.esquema.campos
        for campo in campos:
            tabla.esquema.exigir_campo(campo)

        inicio = time.perf_counter()
        registros, plan = tabla.seleccionar(orden["condicion"])
        milisegundos = (time.perf_counter() - inicio) * 1000

        limite = orden["limite"]
        if limite is None:
            limite = FILAS_POR_DEFECTO
        vista = Table(*campos)
        for registro in registros[:limite]:
            vista.add_row(*[mostrar(registro[c]) for c in campos])
        if len(registros) > 0:
            self.consola.print(vista)

        resumen = str(len(registros)) + " registro(s)"
        if len(registros) > limite:
            resumen = resumen + ", se muestran " + str(limite) + " (use LIMIT n)"
        self.consola.print(resumen + " · " + plan + " · " +
                           format(milisegundos, ".3f") + " ms")

    def _actualizar(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        cantidad = tabla.actualizar(orden["cambios"], orden["condicion"])
        self.consola.print(str(cantidad) + " registro(s) actualizado(s).")

    def _eliminar(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        cantidad = tabla.eliminar(orden["condicion"])
        self.consola.print(str(cantidad) + " registro(s) eliminado(s).")
        self._informar_rotaciones(tabla)

    def _cargar_csv(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        inicio = time.perf_counter()
        cantidad = cargar_csv(tabla, orden["ruta"])
        milisegundos = (time.perf_counter() - inicio) * 1000
        self.consola.print(str(cantidad) + " registro(s) cargado(s) en " +
                           format(milisegundos, ".1f") + " ms.")
        self._informar_rotaciones(tabla)

    # =========================================================
    # ARBOL Y OTROS
    # =========================================================

    def _dibujar(self, orden):
        tabla = self.bd.tabla(orden["tabla"])
        arbol = tabla.arbol_de(orden["campo"])
        campo = orden["campo"] or tabla.esquema.clave_primaria

        niveles = orden["niveles"]
        if niveles is None and arbol.total_nodos > NODOS_ARBOL_COMPLETO:
            niveles = NIVELES_POR_DEFECTO       # un arbol grande no cabe en pantalla

        titulo = ("Indice " + tabla.tipo_arbol + " sobre '" + campo + "' · " +
                  str(arbol.total_nodos) + " nodos · altura " + str(arbol.altura))
        if niveles is not None:
            titulo = titulo + " · primeros " + str(niveles) + " niveles"
        arbol.dibujar(titulo, niveles, self.consola)
        self.consola.print("equilibrado: " + str(arbol.esta_equilibrado))

    def _ejecutar_archivo(self, orden):
        self.ejecutar_script(orden["ruta"])

    def _ayuda(self, orden):
        for titulo, texto in AYUDA:
            self.consola.print("[bold]" + titulo + "[/bold]")
            self.consola.print(escape(texto))       # los [corchetes] son parte del texto

    def _salir(self, orden):
        self.activo = False
