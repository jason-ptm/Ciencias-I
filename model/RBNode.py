from model.Node import Nodo

ROJO = "ROJO"
NEGRO = "NEGRO"


class NodoRN(Nodo):
    """Nodo Rojo-Negro: agrega el color."""

    def __init__(self, clave, dato=None):
        super().__init__(clave, dato)
        self.color = ROJO           # un nodo nuevo siempre entra rojo


def es_rojo(nodo):
    # las hojas vacias (None) cuentan como negras
    return nodo is not None and nodo.color == ROJO


def es_negro(nodo):
    return not es_rojo(nodo)
