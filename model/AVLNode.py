from model.Node import Nodo


class NodoAVL(Nodo):
    """Nodo AVL: agrega la altura para calcular el factor de equilibrio."""

    def __init__(self, clave, dato=None):
        super().__init__(clave, dato)
        self.altura = 1             # un nodo nuevo siempre entra como hoja

    @property
    def altura_izquierda(self):
        if self.izquierda is None:
            return 0
        return self.izquierda.altura

    @property
    def altura_derecha(self):
        if self.derecha is None:
            return 0
        return self.derecha.altura

    @property
    def factor_equilibrio(self):
        # convenio: altura(hi) - altura(hd)
        # positivo = pesa la izquierda, negativo = pesa la derecha
        return self.altura_izquierda - self.altura_derecha

    @property
    def esta_desbalanceado(self):
        return abs(self.factor_equilibrio) > 1

    def actualizar_altura(self):
        self.altura = 1 + max(self.altura_izquierda, self.altura_derecha)
