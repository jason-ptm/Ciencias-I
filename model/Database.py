import os

from model.Errors import ErrorBD
from model.Schema import Esquema, NOMBRE_VALIDO
from model.Table import Tabla
from storage.TableStorage import AlmacenTabla


class BaseDatos:
    """Gestor de tablas. Al crearse restaura todo lo que haya en disco."""

    def __init__(self, directorio="data"):
        self.directorio = directorio
        self.tablas = {}
        self.avisos = []                        # lo que paso durante la recuperacion
        self._recuperar()

    # =========================================================
    # RECUPERACION AL INICIAR
    # =========================================================

    def _recuperar(self):
        os.makedirs(self.directorio, exist_ok=True)
        for archivo in sorted(os.listdir(self.directorio)):
            ruta = os.path.join(self.directorio, archivo)

            if archivo.endswith(".tmp"):
                # escritura que no alcanzo a confirmarse: el .json sigue valido
                os.remove(ruta)
                self.avisos.append("se descarto una escritura incompleta: " + archivo)
                continue
            if not archivo.endswith(".json"):
                continue

            nombre = archivo[:-len(".json")]
            almacen = AlmacenTabla(nombre, self.directorio)
            try:
                tabla = Tabla.desde_dict(almacen.cargar(), almacen)
            except (ValueError, KeyError, TypeError, ErrorBD) as error:
                # un archivo danado no debe tumbar el resto de la base
                self.avisos.append("no se pudo cargar " + archivo + ": " + str(error))
                continue
            self.tablas[tabla.nombre] = tabla

    # =========================================================
    # GESTION DE ESQUEMAS
    # =========================================================

    def crear_tabla(self, nombre, campos, clave_primaria=None, tipo_arbol="AVL"):
        if not NOMBRE_VALIDO.match(nombre):
            raise ErrorBD("nombre de tabla no valido: '" + nombre + "'")
        if nombre in self.tablas:
            raise ErrorBD("la tabla '" + nombre + "' ya existe")

        esquema = Esquema(campos, clave_primaria)
        almacen = AlmacenTabla(nombre, self.directorio)
        tabla = Tabla(nombre, esquema, tipo_arbol, almacen)
        try:
            almacen.guardar(tabla.a_dict())     # la tabla existe desde que esta en disco
        except OSError as error:
            raise ErrorBD("no se pudo crear la tabla en disco (" + str(error) + ")")
        self.tablas[nombre] = tabla
        return tabla

    def borrar_tabla(self, nombre):
        tabla = self.tabla(nombre)
        try:
            tabla.almacen.borrar()
        except OSError as error:
            raise ErrorBD("no se pudo borrar el archivo de la tabla (" + str(error) + ")")
        del self.tablas[nombre]

    def tabla(self, nombre):
        if nombre not in self.tablas:
            raise ErrorBD("la tabla '" + nombre + "' no existe")
        return self.tablas[nombre]

    def nombres(self):
        return sorted(self.tablas)
