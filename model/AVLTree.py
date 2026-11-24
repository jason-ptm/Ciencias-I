from model.AVLNode import NodoAVL
from model.BST import ArbolBinario
from model.TreePrinter import texto_clave


class ArbolAVL(ArbolBinario):
    """Invariante: en todo nodo, |altura(hi) - altura(hd)| <= 1."""

    def _crear_nodo(self, clave, dato):
        return NodoAVL(clave, dato)

    def _despues_de_rotar(self, a, b):
        # primero A, que quedo abajo; despues B, que quedo arriba
        a.actualizar_altura()
        b.actualizar_altura()

    # =========================================================
    # REEQUILIBRIO
    # Sube desde el nodo afectado hasta la raiz actualizando
    # alturas y rotando donde el factor se sale de [-1, 1]
    # =========================================================

    def _rebalancear(self, nodo):
        while nodo is not None:
            nodo.actualizar_altura()
            factor = nodo.factor_equilibrio

            if factor > 1:
                if nodo.izquierda.factor_equilibrio < 0:
                    # caso izquierda-derecha: primero se endereza
                    self._rotar_izquierda(nodo.izquierda)
                nodo = self._rotar_derecha(nodo)

            elif factor < -1:
                if nodo.derecha.factor_equilibrio > 0:
                    # caso derecha-izquierda: primero se endereza
                    self._rotar_derecha(nodo.derecha)
                nodo = self._rotar_izquierda(nodo)

            nodo = nodo.padre

    # =========================================================
    # INSERCION Y ELIMINACION
    # =========================================================

    def insertar(self, clave, dato=None):
        nuevo = self._insertar_como_bst(clave, dato)
        if nuevo is None:
            return False                        # clave repetida
        self._rebalancear(nuevo.padre)
        return True

    def eliminar(self, clave):
        nodo = self.buscar(clave)
        if nodo is None:
            return False
        retirado, hijo, padre = self._retirar(nodo)     # regla del sucesor
        self._rebalancear(padre)
        return True

    # =========================================================
    # METRICAS Y VISTA
    # =========================================================

    @property
    def altura(self):
        if self.raiz is None:
            return 0
        return self.raiz.altura

    @property
    def esta_equilibrado(self):
        pendientes = []
        if self.raiz is not None:
            pendientes.append(self.raiz)
        while len(pendientes) > 0:
            nodo = pendientes.pop()
            if nodo.esta_desbalanceado:
                return False
            if nodo.izquierda is not None:
                pendientes.append(nodo.izquierda)
            if nodo.derecha is not None:
                pendientes.append(nodo.derecha)
        return True

    def etiqueta(self, nodo, lado):
        return ("[bold cyan]" + texto_clave(nodo) + "[/bold cyan]" +
                " [dim](" + lado +
                ", h=" + str(nodo.altura) +
                ", fe=" + str(nodo.factor_equilibrio) + ")[/dim]")
