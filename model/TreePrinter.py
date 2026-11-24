from rich.console import Console
from rich.markup import escape
from rich.tree import Tree

consola = Console()


def texto_clave(nodo):
    # escape evita que una clave con corchetes se lea como formato de rich
    return escape(str(nodo.clave))


def _ramificar(arbol, rama, nodo, nivel, max_niveles):
    if max_niveles is not None and nivel >= max_niveles:
        if not nodo.es_hoja:
            rama.add("[dim]...[/dim]")          # el arbol sigue, no se dibuja
        return
    if nodo.izquierda is not None:
        hija = rama.add(arbol.etiqueta(nodo.izquierda, "izq"))
        _ramificar(arbol, hija, nodo.izquierda, nivel + 1, max_niveles)
    if nodo.derecha is not None:
        hija = rama.add(arbol.etiqueta(nodo.derecha, "der"))
        _ramificar(arbol, hija, nodo.derecha, nivel + 1, max_niveles)


def dibujar_arbol(arbol, titulo=None, max_niveles=None, salida=None):
    """Imprime el arbol con rich.tree. max_niveles recorta arboles grandes."""
    if salida is None:
        salida = consola
    if titulo is not None:
        salida.print("[bold]" + titulo + "[/bold]")
    if arbol.raiz is None:
        salida.print("[italic]arbol vacio[/italic]")
        return
    vista = Tree(arbol.etiqueta(arbol.raiz, "raiz"))
    _ramificar(arbol, vista, arbol.raiz, 1, max_niveles)
    salida.print(vista)
