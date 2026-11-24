class Rotaciones:
    """Rotaciones simples, compartidas por el AVL y el Rojo-Negro.

    Notacion:
        A  = nodo sobre el que se rota      B  = hijo que sube
        P  = padre de A                     hi / hd = hijo izquierdo / derecho
    """

    def _rotar_izquierda(self, a):
        """B = A.hd        A.hd = B.hi        B.hi = A"""
        b = a.derecha
        p = a.padre

        a.derecha = b.izquierda                 # A.hd = B.hi
        if b.izquierda is not None:
            b.izquierda.padre = a

        b.izquierda = a                         # B.hi = A
        a.padre = b

        self._colgar_de(p, a, b)                # B ocupa el lugar de A
        self._despues_de_rotar(a, b)
        self.rotaciones.append("simple izquierda sobre " + str(a.clave))
        return b

    def _rotar_derecha(self, a):
        """B = A.hi        A.hi = B.hd        B.hd = A"""
        b = a.izquierda
        p = a.padre

        a.izquierda = b.derecha                 # A.hi = B.hd
        if b.derecha is not None:
            b.derecha.padre = a

        b.derecha = a                           # B.hd = A
        a.padre = b

        self._colgar_de(p, a, b)                # B ocupa el lugar de A
        self._despues_de_rotar(a, b)
        self.rotaciones.append("simple derecha sobre " + str(a.clave))
        return b

    def _colgar_de(self, p, viejo, nuevo):
        # enlaza 'nuevo' con P en el lado donde estaba 'viejo'
        nuevo.padre = p
        if p is None:
            self.raiz = nuevo
        elif p.izquierda is viejo:
            p.izquierda = nuevo
        else:
            p.derecha = nuevo

    def _despues_de_rotar(self, a, b):
        # gancho: el AVL lo usa para recalcular alturas
        pass
