import math
import re

from model.Errors import ErrorBD

TIPOS = ("int", "text", "real", "bool")
NOMBRE_VALIDO = re.compile(r"^[a-z_][a-z0-9_]*$")


class Esquema:
    """Lista de campos con su tipo y cual de ellos es la clave primaria."""

    def __init__(self, campos, clave_primaria=None):
        if len(campos) == 0:
            raise ErrorBD("la tabla necesita al menos un campo")

        self.campos = []                        # nombres en orden
        self.tipos = {}                         # nombre -> tipo
        for nombre, tipo in campos:
            if not NOMBRE_VALIDO.match(nombre):
                raise ErrorBD("nombre de campo no valido: '" + nombre + "'")
            if nombre in self.tipos:
                raise ErrorBD("campo repetido: '" + nombre + "'")
            if tipo not in TIPOS:
                raise ErrorBD("tipo desconocido '" + tipo + "' (use int, text, real o bool)")
            self.campos.append(nombre)
            self.tipos[nombre] = tipo

        # si no se indica, la clave primaria es el primer campo
        if clave_primaria is None:
            clave_primaria = self.campos[0]
        self.exigir_campo(clave_primaria)
        if self.tipos[clave_primaria] == "bool":
            raise ErrorBD("la clave primaria no puede ser bool")
        self.clave_primaria = clave_primaria

    def exigir_campo(self, campo):
        if campo not in self.tipos:
            raise ErrorBD("el campo '" + campo + "' no existe")

    # =========================================================
    # VALIDACION DE TIPOS
    # =========================================================

    def convertir(self, campo, valor):
        """Devuelve el valor con el tipo del campo o lanza ErrorBD."""
        self.exigir_campo(campo)
        tipo = self.tipos[campo]
        es_bool = isinstance(valor, bool)       # en Python bool tambien es int

        if tipo == "int" and isinstance(valor, int) and not es_bool:
            return valor
        if tipo == "real" and isinstance(valor, (int, float)) and not es_bool:
            if math.isfinite(valor):
                return float(valor)
        if tipo == "text" and isinstance(valor, str):
            return valor
        if tipo == "bool" and es_bool:
            return valor
        raise ErrorBD("el campo '" + campo + "' es de tipo " + tipo +
                      " y recibio " + repr(valor))

    def desde_texto(self, campo, texto):
        """Convierte una celda de CSV al tipo del campo."""
        tipo = self.tipos[campo]
        texto = texto.strip()
        try:
            if tipo == "int":
                return int(texto)
            if tipo == "real":
                return self.convertir(campo, float(texto))
            if tipo == "bool":
                if texto.lower() in ("true", "1", "si", "verdadero"):
                    return True
                if texto.lower() in ("false", "0", "no", "falso"):
                    return False
                raise ValueError
            return texto
        except ValueError:
            raise ErrorBD("el campo '" + campo + "' es de tipo " + tipo +
                          " y recibio '" + texto + "'")

    def armar_registro(self, valores):
        """Lista de valores en orden -> registro {campo: valor} validado."""
        if len(valores) != len(self.campos):
            raise ErrorBD("se esperaban " + str(len(self.campos)) + " valores (" +
                          ", ".join(self.campos) + ") y llegaron " + str(len(valores)))
        registro = {}
        for campo, valor in zip(self.campos, valores):
            registro[campo] = self.convertir(campo, valor)
        return registro

    # =========================================================
    # PERSISTENCIA
    # =========================================================

    def a_dict(self):
        return {
            "clave_primaria": self.clave_primaria,
            "campos": [{"nombre": c, "tipo": self.tipos[c]} for c in self.campos],
        }

    @staticmethod
    def desde_dict(datos):
        campos = [(c["nombre"], c["tipo"]) for c in datos["campos"]]
        return Esquema(campos, datos["clave_primaria"])
