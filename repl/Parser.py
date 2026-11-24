import re

from model.Condition import Condicion
from model.Errors import ErrorBD

# cada alternativa es un tipo de token; el orden importa
PATRON = re.compile(r"""
    \s*(?:
        (?P<texto>'(?:[^']|'')*'|"(?:[^"]|"")*")       # 'entre comillas'
      | (?P<numero>-?\d+(?:\.\d+)?(?![\w./\\]))        # 12   -3.5
      | (?P<ruta>[\w.\-/\\:]*[./\\][\w.\-/\\:]*)       # datasets/archivo.csv
      | (?P<palabra>[A-Za-z_]\w*)                      # palabras clave y nombres
      | (?P<simbolo>!=|<>|<=|>=|[=<>(),*;])
    )""", re.VERBOSE)

TIPOS = {
    "int": "int", "integer": "int", "entero": "int",
    "text": "text", "string": "text", "str": "text", "texto": "text",
    "real": "real", "float": "real", "double": "real",
    "bool": "bool", "boolean": "bool", "booleano": "bool",
}


def tokenizar(texto):
    tokens = []
    posicion = 0
    texto = texto.rstrip()
    while posicion < len(texto):
        m = PATRON.match(texto, posicion)
        if m is None:
            raise ErrorBD("no se entiende: " + texto[posicion:].strip()[:20])
        tipo = m.lastgroup
        valor = m.group(tipo)
        if tipo == "texto":
            comilla = valor[0]
            valor = valor[1:-1].replace(comilla * 2, comilla)   # '' -> '
        elif tipo == "numero":
            valor = float(valor) if "." in valor else int(valor)
        tokens.append((tipo, valor))
        posicion = m.end()
    return tokens


class Parser:
    """Convierte una linea SQL-like en ordenes: diccionarios con una
    'accion' y sus datos, listos para que el REPL los ejecute."""

    def analizar(self, texto):
        """Devuelve la lista de ordenes de la linea (separadas por ;)."""
        ordenes = []
        grupo = []
        for token in tokenizar(texto) + [("simbolo", ";")]:
            if token == ("simbolo", ";"):
                if len(grupo) > 0:
                    ordenes.append(self._orden(grupo))
                grupo = []
            else:
                grupo.append(token)
        return ordenes

    # =========================================================
    # LECTURA DE TOKENS
    # =========================================================

    def _ver(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return ("fin", None)

    def _viene(self, palabra):
        tipo, valor = self._ver()
        return tipo == "palabra" and valor.upper() == palabra

    def _tomar_si(self, palabra):
        if self._viene(palabra):
            self.i = self.i + 1
            return True
        return False

    def _exigir(self, *palabras):
        for palabra in palabras:
            if not self._tomar_si(palabra):
                raise ErrorBD("se esperaba " + palabra)

    def _simbolo(self, simbolo):
        if self._ver() != ("simbolo", simbolo):
            raise ErrorBD("se esperaba '" + simbolo + "'")
        self.i = self.i + 1

    def _nombre(self, que="un nombre"):
        tipo, valor = self._ver()
        if tipo != "palabra":
            raise ErrorBD("se esperaba " + que)
        self.i = self.i + 1
        return valor.lower()                    # los nombres no distinguen mayusculas

    def _valor(self):
        tipo, valor = self._ver()
        self.i = self.i + 1
        if tipo in ("texto", "numero"):
            return valor
        if tipo == "palabra" and valor.upper() in ("TRUE", "FALSE"):
            return valor.upper() == "TRUE"
        raise ErrorBD("se esperaba un valor (numero, 'texto', true o false)")

    def _ruta(self):
        tipo, valor = self._ver()
        if tipo not in ("texto", "ruta", "palabra"):
            raise ErrorBD("se esperaba la ruta de un archivo")
        self.i = self.i + 1
        return valor

    def _entero(self):
        tipo, valor = self._ver()
        if tipo != "numero" or not isinstance(valor, int) or valor < 0:
            raise ErrorBD("se esperaba un numero entero positivo")
        self.i = self.i + 1
        return valor

    def _lista(self, leer):
        # elemento , elemento , ...
        elementos = [leer()]
        while self._ver() == ("simbolo", ","):
            self.i = self.i + 1
            elementos.append(leer())
        return elementos

    # =========================================================
    # ORDENES
    # =========================================================

    def _orden(self, tokens):
        self.tokens = tokens
        self.i = 0

        if self._tomar_si("CREATE"):
            if self._tomar_si("TABLE"):
                orden = self._crear_tabla()
            else:
                self._exigir("INDEX", "ON")
                orden = {"accion": "crear_indice", "tabla": self._nombre("la tabla")}
                self._simbolo("(")
                orden["campo"] = self._nombre("el campo")
                self._simbolo(")")
        elif self._tomar_si("DROP"):
            self._exigir("TABLE")
            orden = {"accion": "borrar_tabla", "si_existe": False}
            if self._tomar_si("IF"):
                self._exigir("EXISTS")
                orden["si_existe"] = True
            orden["tabla"] = self._nombre("la tabla")
        elif self._tomar_si("INSERT"):
            self._exigir("INTO")
            orden = {"accion": "insertar", "tabla": self._nombre("la tabla")}
            self._exigir("VALUES")
            self._simbolo("(")
            orden["valores"] = self._lista(self._valor)
            self._simbolo(")")
        elif self._tomar_si("SELECT"):
            orden = self._seleccionar()
        elif self._tomar_si("UPDATE"):
            orden = {"accion": "actualizar", "tabla": self._nombre("la tabla")}
            self._exigir("SET")
            orden["cambios"] = dict(self._lista(self._asignacion))
            orden["condicion"] = self._donde()
        elif self._tomar_si("DELETE"):
            self._exigir("FROM")
            orden = {"accion": "eliminar", "tabla": self._nombre("la tabla")}
            orden["condicion"] = self._donde()
        elif self._tomar_si("LOAD"):
            orden = {"accion": "cargar_csv", "ruta": self._ruta()}
            self._exigir("INTO")
            orden["tabla"] = self._nombre("la tabla")
        elif self._tomar_si("SOURCE"):
            orden = {"accion": "ejecutar_archivo", "ruta": self._ruta()}
        elif self._tomar_si("TREE"):
            orden = self._arbol()
        elif self._tomar_si("SHOW"):
            self._exigir("TABLES")
            orden = {"accion": "listar_tablas"}
        elif self._tomar_si("DESCRIBE"):
            orden = {"accion": "describir", "tabla": self._nombre("la tabla")}
        elif self._tomar_si("HELP"):
            orden = {"accion": "ayuda"}
        elif self._tomar_si("EXIT") or self._tomar_si("QUIT"):
            orden = {"accion": "salir"}
        else:
            raise ErrorBD("comando no reconocido (escriba HELP)")

        if self.i < len(self.tokens):
            raise ErrorBD("sobra texto al final: " + str(self._ver()[1]))
        return orden

    def _crear_tabla(self):
        # CREATE TABLE t (campo tipo [PRIMARY KEY], ...) [USING AVL|RB]
        orden = {"accion": "crear_tabla", "tabla": self._nombre("la tabla"),
                 "clave_primaria": None, "arbol": "AVL"}
        self._simbolo("(")
        orden["campos"] = self._lista(lambda: self._campo(orden))
        self._simbolo(")")
        if self._tomar_si("USING"):
            orden["arbol"] = self._nombre("AVL o RB").upper()
        return orden

    def _campo(self, orden):
        nombre = self._nombre("el nombre del campo")
        tipo = self._nombre("el tipo del campo")
        if tipo not in TIPOS:
            raise ErrorBD("tipo desconocido '" + tipo + "' (use int, text, real o bool)")
        if self._tomar_si("PRIMARY"):
            self._exigir("KEY")
            if orden["clave_primaria"] is not None:
                raise ErrorBD("solo puede haber una clave primaria")
            orden["clave_primaria"] = nombre
        return (nombre, TIPOS[tipo])

    def _seleccionar(self):
        # SELECT * | campo, ... FROM t [WHERE condicion] [LIMIT n]
        orden = {"accion": "seleccionar", "campos": None, "limite": None}
        if self._ver() == ("simbolo", "*"):
            self.i = self.i + 1
        else:
            orden["campos"] = self._lista(lambda: self._nombre("un campo"))
        self._exigir("FROM")
        orden["tabla"] = self._nombre("la tabla")
        orden["condicion"] = self._donde()
        if self._tomar_si("LIMIT"):
            orden["limite"] = self._entero()
        return orden

    def _asignacion(self):
        campo = self._nombre("un campo")
        self._simbolo("=")
        return (campo, self._valor())

    def _donde(self):
        # [WHERE campo operador valor | WHERE campo BETWEEN a AND b]
        if not self._tomar_si("WHERE"):
            return None
        campo = self._nombre("un campo")
        if self._tomar_si("BETWEEN"):
            desde = self._valor()
            self._exigir("AND")
            return Condicion(campo, "BETWEEN", desde, self._valor())
        tipo, operador = self._ver()
        if tipo != "simbolo" or operador not in ("=", "!=", "<>", "<", "<=", ">", ">="):
            raise ErrorBD("se esperaba un operador (=, !=, <, <=, >, >=, BETWEEN)")
        self.i = self.i + 1
        if operador == "<>":
            operador = "!="
        return Condicion(campo, operador, self._valor())

    def _arbol(self):
        # TREE t [campo] [niveles]
        orden = {"accion": "dibujar", "tabla": self._nombre("la tabla"),
                 "campo": None, "niveles": None}
        if self._ver()[0] == "palabra":
            orden["campo"] = self._nombre()
        if self._ver()[0] == "numero":
            orden["niveles"] = self._entero()
        return orden
