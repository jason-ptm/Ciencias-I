"""Verificadores independientes: no confian en lo que el arbol dice de si mismo."""
from model.RBNode import es_rojo


def altura_real(nodo):
    if nodo is None:
        return 0
    return 1 + max(altura_real(nodo.izquierda), altura_real(nodo.derecha))


def verificar_bst(arbol):
    """Revisa orden, enlaces al padre y conteo. Devuelve cuantos nodos hay."""
    assert arbol.raiz is None or arbol.raiz.padre is None

    def revisar(nodo, minimo, maximo):
        if nodo is None:
            return 0
        assert minimo is None or nodo.clave > minimo
        assert maximo is None or nodo.clave < maximo
        for hijo in (nodo.izquierda, nodo.derecha):
            assert hijo is None or hijo.padre is nodo
        return (1 + revisar(nodo.izquierda, minimo, nodo.clave)
                + revisar(nodo.derecha, nodo.clave, maximo))

    total = revisar(arbol.raiz, None, None)
    assert total == arbol.total_nodos
    return total


def verificar_avl(arbol):
    verificar_bst(arbol)

    def revisar(nodo):
        if nodo is None:
            return
        izquierda = altura_real(nodo.izquierda)
        derecha = altura_real(nodo.derecha)
        assert nodo.altura == 1 + max(izquierda, derecha)       # altura guardada correcta
        assert abs(izquierda - derecha) <= 1                    # invariante AVL
        revisar(nodo.izquierda)
        revisar(nodo.derecha)

    revisar(arbol.raiz)


def verificar_rojinegro(arbol):
    verificar_bst(arbol)
    assert not es_rojo(arbol.raiz)                              # raiz negra

    def altura_negra(nodo):
        if nodo is None:
            return 1
        if es_rojo(nodo):
            assert not es_rojo(nodo.izquierda)                  # sin rojo-rojo
            assert not es_rojo(nodo.derecha)
        izquierda = altura_negra(nodo.izquierda)
        derecha = altura_negra(nodo.derecha)
        assert izquierda == derecha                             # misma altura negra
        return izquierda + (0 if es_rojo(nodo) else 1)

    altura_negra(arbol.raiz)
