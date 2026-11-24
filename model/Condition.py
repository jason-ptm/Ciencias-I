OPERADORES = ("=", "!=", "<", "<=", ">", ">=", "BETWEEN")


class Condicion:
    """Criterio simple de un WHERE: campo operador valor."""

    def __init__(self, campo, operador, valor, valor_hasta=None):
        self.campo = campo
        self.operador = operador
        self.valor = valor
        self.valor_hasta = valor_hasta          # solo para BETWEEN

    def cumple(self, registro):
        actual = registro[self.campo]
        if self.operador == "=":
            return actual == self.valor
        if self.operador == "!=":
            return actual != self.valor
        if self.operador == "<":
            return actual < self.valor
        if self.operador == "<=":
            return actual <= self.valor
        if self.operador == ">":
            return actual > self.valor
        if self.operador == ">=":
            return actual >= self.valor
        return self.valor <= actual <= self.valor_hasta

    def consultar(self, arbol):
        """Resuelve la condicion sobre un arbol que indexa este campo.
        Devuelve pares (clave, dato) en O(log n + k)."""
        if self.operador == "=":
            nodo = arbol.buscar(self.valor)
            if nodo is None:
                return []
            return [(nodo.clave, nodo.dato)]
        if self.operador == "<":
            return arbol.rango(None, self.valor, incluir_maximo=False)
        if self.operador == "<=":
            return arbol.rango(None, self.valor)
        if self.operador == ">":
            return arbol.rango(self.valor, None, incluir_minimo=False)
        if self.operador == ">=":
            return arbol.rango(self.valor, None)
        return arbol.rango(self.valor, self.valor_hasta)

    @property
    def usa_indice(self):
        # "distinto de" no acota un rango: obliga a recorrer todo
        return self.operador != "!="

    def __repr__(self):
        if self.operador == "BETWEEN":
            return (self.campo + " BETWEEN " + repr(self.valor) +
                    " AND " + repr(self.valor_hasta))
        return self.campo + " " + self.operador + " " + repr(self.valor)
