from model.BST import ArbolBinario
from model.RBNode import NodoRN, ROJO, NEGRO, es_rojo, es_negro
from model.TreePrinter import texto_clave


class ArbolRojoNegro(ArbolBinario):
    """Invariantes:
        1. Cada nodo es rojo o negro.
        2. La raiz es negra.
        3. Las hojas vacias (None) cuentan como negras.
        4. Un nodo rojo no tiene hijos rojos.
        5. Todo camino de un nodo a sus hojas vacias pasa por la misma
           cantidad de nodos negros (altura negra).
    """

    def _crear_nodo(self, clave, dato):
        return NodoRN(clave, dato)

    # =========================================================
    # INSERCION
    # El nodo entra rojo; solo puede romper la regla 4 (rojo-rojo).
    # =========================================================

    def insertar(self, clave, dato=None):
        nuevo = self._insertar_como_bst(clave, dato)
        if nuevo is None:
            return False                        # clave repetida
        self._corregir_insercion(nuevo)
        return True

    def _corregir_insercion(self, nodo):
        while es_rojo(nodo.padre):
            padre = nodo.padre
            abuelo = padre.padre                # existe: un rojo nunca es raiz

            if padre is abuelo.izquierda:
                tio = abuelo.derecha
                if es_rojo(tio):
                    # caso 1, tio rojo: recolorear y subir el problema
                    padre.color = NEGRO
                    tio.color = NEGRO
                    abuelo.color = ROJO
                    nodo = abuelo
                else:
                    if nodo is padre.derecha:
                        # caso 2, triangulo: se endereza a una linea
                        self._rotar_izquierda(padre)
                        nodo, padre = padre, nodo
                    # caso 3, linea: rotar el abuelo y recolorear
                    padre.color = NEGRO
                    abuelo.color = ROJO
                    self._rotar_derecha(abuelo)
            else:
                # espejo de lo anterior
                tio = abuelo.izquierda
                if es_rojo(tio):
                    padre.color = NEGRO
                    tio.color = NEGRO
                    abuelo.color = ROJO
                    nodo = abuelo
                else:
                    if nodo is padre.izquierda:
                        self._rotar_derecha(padre)
                        nodo, padre = padre, nodo
                    padre.color = NEGRO
                    abuelo.color = ROJO
                    self._rotar_izquierda(abuelo)

        self.raiz.color = NEGRO                 # regla 2

    # =========================================================
    # ELIMINACION
    # Si sale un nodo negro, a ese camino le falta un negro
    # (regla 5) y hay que repararlo.
    # =========================================================

    def eliminar(self, clave):
        nodo = self.buscar(clave)
        if nodo is None:
            return False
        retirado, hijo, padre = self._retirar(nodo)     # regla del sucesor
        if retirado.color == NEGRO:
            self._corregir_eliminacion(hijo, padre)
        return True

    def _corregir_eliminacion(self, x, padre):
        # x carga el "negro que falta"; puede ser None, por eso viaja su padre
        while x is not self.raiz and es_negro(x):

            if x is padre.izquierda:
                hermano = padre.derecha
                if es_rojo(hermano):
                    # caso 1, hermano rojo: se convierte en un caso de hermano negro
                    hermano.color = NEGRO
                    padre.color = ROJO
                    self._rotar_izquierda(padre)
                    hermano = padre.derecha

                if es_negro(hermano.izquierda) and es_negro(hermano.derecha):
                    # caso 2, sobrinos negros: recolorear y subir el problema
                    hermano.color = ROJO
                    x = padre
                    padre = x.padre
                else:
                    if es_negro(hermano.derecha):
                        # caso 3, sobrino cercano rojo: se lleva al caso 4
                        hermano.izquierda.color = NEGRO
                        hermano.color = ROJO
                        self._rotar_derecha(hermano)
                        hermano = padre.derecha
                    # caso 4, sobrino lejano rojo: rotar y terminar
                    hermano.color = padre.color
                    padre.color = NEGRO
                    hermano.derecha.color = NEGRO
                    self._rotar_izquierda(padre)
                    x = self.raiz
            else:
                # espejo de lo anterior
                hermano = padre.izquierda
                if es_rojo(hermano):
                    hermano.color = NEGRO
                    padre.color = ROJO
                    self._rotar_derecha(padre)
                    hermano = padre.izquierda

                if es_negro(hermano.izquierda) and es_negro(hermano.derecha):
                    hermano.color = ROJO
                    x = padre
                    padre = x.padre
                else:
                    if es_negro(hermano.izquierda):
                        hermano.derecha.color = NEGRO
                        hermano.color = ROJO
                        self._rotar_izquierda(hermano)
                        hermano = padre.izquierda
                    hermano.color = padre.color
                    padre.color = NEGRO
                    hermano.izquierda.color = NEGRO
                    self._rotar_derecha(padre)
                    x = self.raiz

        if x is not None:
            x.color = NEGRO                     # absorbe el negro que faltaba

    # =========================================================
    # METRICAS Y VISTA
    # =========================================================

    def _altura_negra(self, nodo):
        """Altura negra del subarbol, o -1 si rompe la regla 4 o la 5."""
        if nodo is None:
            return 1
        if es_rojo(nodo) and (es_rojo(nodo.izquierda) or es_rojo(nodo.derecha)):
            return -1
        izquierda = self._altura_negra(nodo.izquierda)
        derecha = self._altura_negra(nodo.derecha)
        if izquierda == -1 or derecha == -1 or izquierda != derecha:
            return -1
        if es_negro(nodo):
            return izquierda + 1
        return izquierda

    @property
    def esta_equilibrado(self):
        if es_rojo(self.raiz):
            return False
        return self._altura_negra(self.raiz) != -1

    def etiqueta(self, nodo, lado):
        if es_rojo(nodo):
            clave = "[bold red]" + texto_clave(nodo) + "[/bold red]"
        else:
            clave = "[bold]" + texto_clave(nodo) + "[/bold]"
        return clave + " [dim](" + lado + ", " + nodo.color.lower() + ")[/dim]"
