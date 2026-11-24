from model.Rotations import Rotaciones
from model.TreePrinter import dibujar_arbol


class ArbolBinario(Rotaciones):
    """Arbol binario de busqueda base. Aqui vive todo lo que el AVL y el
    Rojo-Negro comparten; cada uno solo agrega su forma de balancear."""

    def __init__(self):
        self.raiz = None
        self.total_nodos = 0
        self.rotaciones = []        # bitacora de rotaciones

    # =========================================================
    # LO QUE DEFINE CADA ARBOL
    # =========================================================

    def _crear_nodo(self, clave, dato):
        raise NotImplementedError

    def insertar(self, clave, dato=None):
        raise NotImplementedError

    def eliminar(self, clave):
        raise NotImplementedError

    def etiqueta(self, nodo, lado):
        raise NotImplementedError

    # =========================================================
    # BUSQUEDA
    # =========================================================

    def buscar(self, clave):
        actual = self.raiz
        while actual is not None:
            if clave == actual.clave:
                return actual
            if clave < actual.clave:
                actual = actual.izquierda
            else:
                actual = actual.derecha
        return None

    def contiene(self, clave):
        return self.buscar(clave) is not None

    def _nodo_minimo(self, nodo):
        while nodo.izquierda is not None:
            nodo = nodo.izquierda
        return nodo

    def minimo(self):
        if self.raiz is None:
            return None
        return self._nodo_minimo(self.raiz).clave

    # =========================================================
    # SUCESOR
    # Es el siguiente nodo del inorden: el minimo del subarbol
    # derecho o, si no hay, el primer ancestro al que se llega
    # subiendo desde un hijo izquierdo.
    # =========================================================

    def _nodo_sucesor(self, nodo):
        if nodo.derecha is not None:
            return self._nodo_minimo(nodo.derecha)
        p = nodo.padre
        while p is not None and nodo is p.derecha:
            nodo = p
            p = p.padre
        return p

    def sucesor(self, clave):
        nodo = self.buscar(clave)
        if nodo is None:
            return None
        s = self._nodo_sucesor(nodo)
        if s is None:
            return None
        return s.clave

    # =========================================================
    # INSERCION Y ELIMINACION SIN BALANCEAR
    # Cada arbol llama a estos pasos y luego repara su invariante.
    # =========================================================

    def _insertar_como_bst(self, clave, dato):
        """Cuelga el nodo como hoja. Devuelve None si la clave ya existe."""
        nuevo = self._crear_nodo(clave, dato)

        if self.raiz is None:
            self.raiz = nuevo
            self.total_nodos = 1
            return nuevo

        actual = self.raiz
        while True:
            if clave == actual.clave:
                return None
            if clave < actual.clave:
                if actual.izquierda is None:
                    actual.izquierda = nuevo
                    break
                actual = actual.izquierda
            else:
                if actual.derecha is None:
                    actual.derecha = nuevo
                    break
                actual = actual.derecha

        nuevo.padre = actual
        self.total_nodos = self.total_nodos + 1
        return nuevo

    def _trasplantar(self, viejo, nuevo):
        """Cuelga a 'nuevo' en el lugar que ocupaba 'viejo'."""
        p = viejo.padre
        if p is None:
            self.raiz = nuevo
        elif p.izquierda is viejo:
            p.izquierda = nuevo
        else:
            p.derecha = nuevo
        if nuevo is not None:
            nuevo.padre = p

    def _retirar(self, nodo):
        """Saca un nodo del arbol aplicando la regla del sucesor.

        Devuelve (retirado, hijo, padre): el nodo que salio fisicamente,
        el hijo que subio a su lugar y el padre desde donde se repara.
        """
        # dos hijos: el sucesor presta su contenido y es el que sale
        if nodo.tiene_dos_hijos:
            s = self._nodo_sucesor(nodo)
            nodo.clave = s.clave
            nodo.dato = s.dato
            nodo = s

        # aqui el nodo es hoja o tiene un solo hijo
        hijo = nodo.hijo_unico
        padre = nodo.padre
        self._trasplantar(nodo, hijo)
        nodo.izquierda = None
        nodo.derecha = None
        nodo.padre = None

        self.total_nodos = self.total_nodos - 1
        return nodo, hijo, padre

    # =========================================================
    # RECORRIDOS
    # Se avanza de sucesor en sucesor, asi que salen ordenados.
    # =========================================================

    def _primer_nodo(self, minimo, incluir):
        """Primer nodo del inorden con clave >= minimo (> si no se incluye)."""
        if self.raiz is None:
            return None
        if minimo is None:
            return self._nodo_minimo(self.raiz)

        candidato = None
        actual = self.raiz
        while actual is not None:
            if actual.clave > minimo or (incluir and actual.clave == minimo):
                candidato = actual              # sirve; se busca uno menor
                actual = actual.izquierda
            else:
                actual = actual.derecha
        return candidato

    def rango(self, minimo=None, maximo=None,
              incluir_minimo=True, incluir_maximo=True):
        """Pares (clave, dato) entre minimo y maximo. None = sin limite."""
        salida = []
        nodo = self._primer_nodo(minimo, incluir_minimo)
        while nodo is not None:
            if maximo is not None:
                if nodo.clave > maximo:
                    break
                if nodo.clave == maximo and not incluir_maximo:
                    break
            salida.append((nodo.clave, nodo.dato))
            nodo = self._nodo_sucesor(nodo)
        return salida

    def inorden(self):
        return self.rango()

    def claves(self):
        return [clave for clave, dato in self.rango()]

    # =========================================================
    # METRICAS Y VISTA
    # =========================================================

    @property
    def altura(self):
        # version generica O(n); el AVL la responde en O(1)
        maxima = 0
        pendientes = []
        if self.raiz is not None:
            pendientes.append((self.raiz, 1))
        while len(pendientes) > 0:
            nodo, nivel = pendientes.pop()
            if nivel > maxima:
                maxima = nivel
            if nodo.izquierda is not None:
                pendientes.append((nodo.izquierda, nivel + 1))
            if nodo.derecha is not None:
                pendientes.append((nodo.derecha, nivel + 1))
        return maxima

    def dibujar(self, titulo=None, max_niveles=None, salida=None):
        dibujar_arbol(self, titulo, max_niveles, salida)

    def limpiar_rotaciones(self):
        self.rotaciones = []

    def reporte_rotaciones(self):
        if len(self.rotaciones) == 0:
            print("  (sin rotaciones)")
            return
        for r in self.rotaciones:
            print("  rotacion " + r)
