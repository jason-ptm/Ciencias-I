import argparse
import sys

from model.Errors import ErrorBD
from repl.REPL import REPL


def main():
    opciones = argparse.ArgumentParser(
        description="Motor de base de datos con arboles autobalanceados (AVL y Rojo-Negro)")
    opciones.add_argument("script", nargs="?",
                          help="archivo de comandos a ejecutar; sin el, abre el REPL")
    opciones.add_argument("--data", default="data",
                          help="carpeta donde se guardan las tablas (por defecto: data)")
    argumentos = opciones.parse_args()

    repl = REPL(argumentos.data)
    if argumentos.script is None:
        repl.iniciar()
        return

    try:
        repl.ejecutar_script(argumentos.script)
    except ErrorBD as error:
        print("Error: " + str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
