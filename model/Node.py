class Nodo:
    """Nodo enlazado: conoce a sus dos hijos y a su padre."""

    def __init__(self, clave, dato=None):
        self.clave = clave          # valor por el que se ordena el arbol
        self.dato = dato            # informacion asociada a la clave
        self.izquierda = None
        self.derecha = None
        self.padre = None

    @property
    def es_hoja(self):
        return self.izquierda is None and self.derecha is None

    @property
    def tiene_dos_hijos(self):
        return self.izquierda is not None and self.derecha is not None

    @property
    def hijo_unico(self):
        # devuelve el hijo que exista (None si es hoja)
        if self.izquierda is not None:
            return self.izquierda
        return self.derecha

    def __repr__(self):
        return str(self.clave)
