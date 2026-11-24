from model.AVLTree import ArbolAVL
from model.Condition import Condicion
from model.Errors import ErrorBD
from model.RBTree import ArbolRojoNegro
from model.Schema import Esquema

ARBOLES = {"AVL": ArbolAVL, "RB": ArbolRojoNegro}


def orden_por_medianas(ordenados):
    """Reordena una lista ya ordenada: primero el del medio, despues los
    medios de cada mitad y asi nivel por nivel. Insertada en ese orden,
    el arbol queda con la altura minima y sin necesitar rotaciones."""
    salida = []
    tramos = [(0, len(ordenados) - 1)]
    i = 0
    while i < len(tramos):
        desde, hasta = tramos[i]
        i = i + 1
        if desde > hasta:
            continue
        medio = (desde + hasta) // 2
        salida.append(ordenados[medio])
        tramos.append((desde, medio - 1))
        tramos.append((medio + 1, hasta))
    return salida


class Tabla:
    """Espacio de almacenamiento respaldado por arboles autobalanceados.

    primario:     clave primaria -> registro completo (el arbol ES la tabla)
    secundarios:  por cada campo indexado, valor -> conjunto de claves primarias
    """

    def __init__(self, nombre, esquema, tipo_arbol="AVL", almacen=None):
        if tipo_arbol not in ARBOLES:
            raise ErrorBD("tipo de arbol desconocido '" + tipo_arbol + "' (use AVL o RB)")
        self.nombre = nombre
        self.esquema = esquema
        self.tipo_arbol = tipo_arbol
        self.almacen = almacen                  # None = solo en memoria
        self.primario = ARBOLES[tipo_arbol]()
        self.secundarios = {}

    @property
    def total(self):
        return self.primario.total_nodos

    def arbol_de(self, campo=None):
        """Arbol que indexa un campo (la clave primaria si no se indica)."""
        if campo is None or campo == self.esquema.clave_primaria:
            return self.primario
        self.esquema.exigir_campo(campo)
        if campo not in self.secundarios:
            raise ErrorBD("el campo '" + campo + "' no tiene indice")
        return self.secundarios[campo]

    # =========================================================
    # PASOS INTERNOS (solo memoria, sin validar ni guardar)
    # =========================================================

    def _indexar(self, arbol, valor, clave):
        nodo = arbol.buscar(valor)
        if nodo is None:
            arbol.insertar(valor, {clave})
        else:
            nodo.dato.add(clave)                # valor repetido: se suma al conjunto

    def _desindexar(self, arbol, valor, clave):
        nodo = arbol.buscar(valor)
        nodo.dato.discard(clave)
        if len(nodo.dato) == 0:
            arbol.eliminar(valor)               # ya nadie tiene ese valor

    def _poner(self, registro):
        clave = registro[self.esquema.clave_primaria]
        self.primario.insertar(clave, registro)
        for campo, arbol in self.secundarios.items():
            self._indexar(arbol, registro[campo], clave)

    def _quitar(self, clave):
        registro = self.primario.buscar(clave).dato
        self.primario.eliminar(clave)
        for campo, arbol in self.secundarios.items():
            self._desindexar(arbol, registro[campo], clave)

    def _cambiar(self, clave, nuevo):
        nodo = self.primario.buscar(clave)
        viejo = nodo.dato
        nodo.dato = nuevo
        for campo, arbol in self.secundarios.items():
            if viejo[campo] != nuevo[campo]:
                self._desindexar(arbol, viejo[campo], clave)
                self._indexar(arbol, nuevo[campo], clave)

    def _limpiar_rotaciones(self):
        self.primario.limpiar_rotaciones()
        for arbol in self.secundarios.values():
            arbol.limpiar_rotaciones()

    # =========================================================
    # ATOMICIDAD
    # Todo se valida antes de tocar los arboles, asi que lo unico
    # que puede fallar despues es el disco. Si falla, se deshace
    # el cambio en memoria y el archivo queda como estaba.
    # =========================================================

    def _confirmar(self, deshacer):
        if self.almacen is None:
            return
        try:
            self.almacen.guardar(self.a_dict())
        except OSError as error:
            deshacer()
            raise ErrorBD("no se pudo guardar en disco, la operacion se revirtio (" +
                          str(error) + ")")

    # =========================================================
    # INSERT
    # =========================================================

    def insertar(self, valores):
        return self.insertar_varios([valores])

    def insertar_varios(self, filas):
        """Inserta todas las filas o ninguna."""
        pk = self.esquema.clave_primaria
        registros = []
        vistas = set()
        for numero, valores in enumerate(filas, start=1):
            try:
                registro = self.esquema.armar_registro(valores)
                clave = registro[pk]
                if clave in vistas or self.primario.contiene(clave):
                    raise ErrorBD("clave primaria repetida: " + repr(clave))
            except ErrorBD as error:
                if len(filas) == 1:
                    raise
                raise ErrorBD("fila " + str(numero) + ": " + str(error))
            vistas.add(clave)
            registros.append(registro)

        self._limpiar_rotaciones()
        for registro in registros:
            self._poner(registro)

        def deshacer():
            for registro in registros:
                self._quitar(registro[pk])

        self._confirmar(deshacer)
        return len(registros)

    # =========================================================
    # SELECT
    # =========================================================

    def _normalizar(self, condicion):
        # lleva los valores del WHERE al tipo del campo (ej. 4 -> 4.0)
        esquema = self.esquema
        valor = esquema.convertir(condicion.campo, condicion.valor)
        hasta = None
        if condicion.operador == "BETWEEN":
            hasta = esquema.convertir(condicion.campo, condicion.valor_hasta)
        return Condicion(condicion.campo, condicion.operador, valor, hasta)

    def seleccionar(self, condicion=None):
        """Devuelve (registros, plan). El plan dice como se resolvio."""
        if condicion is None:
            registros = [dato for clave, dato in self.primario.inorden()]
            return registros, "recorrido inorden completo"

        condicion = self._normalizar(condicion)
        campo = condicion.campo

        if condicion.usa_indice and campo == self.esquema.clave_primaria:
            registros = [dato for clave, dato in condicion.consultar(self.primario)]
            return registros, "indice " + self.tipo_arbol + " de la clave primaria '" + campo + "'"

        if condicion.usa_indice and campo in self.secundarios:
            registros = []
            for valor, claves in condicion.consultar(self.secundarios[campo]):
                for clave in sorted(claves):
                    registros.append(self.primario.buscar(clave).dato)
            return registros, "indice " + self.tipo_arbol + " sobre '" + campo + "'"

        # sin indice util: se revisan todos los registros
        registros = [dato for clave, dato in self.primario.inorden()
                     if condicion.cumple(dato)]
        return registros, "recorrido completo (sin indice para esta consulta)"

    def buscar(self, clave):
        """Registro con esa clave primaria, o None."""
        clave = self.esquema.convertir(self.esquema.clave_primaria, clave)
        nodo = self.primario.buscar(clave)
        if nodo is None:
            return None
        return nodo.dato

    # =========================================================
    # UPDATE
    # =========================================================

    def actualizar(self, cambios, condicion=None):
        """Aplica {campo: valor} a los registros que cumplan. Devuelve cuantos."""
        pk = self.esquema.clave_primaria
        convertidos = {}
        for campo, valor in cambios.items():
            if campo == pk:
                raise ErrorBD("la clave primaria no se puede actualizar")
            convertidos[campo] = self.esquema.convertir(campo, valor)

        viejos, plan = self.seleccionar(condicion)
        nuevos = []
        for viejo in viejos:
            nuevo = dict(viejo)
            nuevo.update(convertidos)
            nuevos.append(nuevo)

        self._limpiar_rotaciones()
        for nuevo in nuevos:
            self._cambiar(nuevo[pk], nuevo)

        def deshacer():
            for viejo in viejos:
                self._cambiar(viejo[pk], viejo)

        self._confirmar(deshacer)
        return len(nuevos)

    # =========================================================
    # DELETE
    # =========================================================

    def eliminar(self, condicion=None):
        """Elimina los registros que cumplan. Devuelve cuantos."""
        pk = self.esquema.clave_primaria
        registros, plan = self.seleccionar(condicion)

        self._limpiar_rotaciones()
        for registro in registros:
            self._quitar(registro[pk])

        def deshacer():
            for registro in registros:
                self._poner(registro)

        self._confirmar(deshacer)
        return len(registros)

    # =========================================================
    # INDICES SECUNDARIOS
    # =========================================================

    def _construir_indice(self, campo):
        arbol = ARBOLES[self.tipo_arbol]()
        for clave, registro in self.primario.inorden():
            self._indexar(arbol, registro[campo], clave)
        self.secundarios[campo] = arbol

    def crear_indice(self, campo):
        self.esquema.exigir_campo(campo)
        if campo == self.esquema.clave_primaria:
            raise ErrorBD("la clave primaria ya esta indexada")
        if campo in self.secundarios:
            raise ErrorBD("el campo '" + campo + "' ya tiene indice")

        self._construir_indice(campo)

        def deshacer():
            del self.secundarios[campo]

        self._confirmar(deshacer)

    # =========================================================
    # PERSISTENCIA
    # Solo se guardan los registros (ordenados por clave); los
    # arboles se reconstruyen al cargar.
    # =========================================================

    def a_dict(self):
        campos = self.esquema.campos
        return {
            "tabla": self.nombre,
            "arbol": self.tipo_arbol,
            "esquema": self.esquema.a_dict(),
            "indices": sorted(self.secundarios),
            "registros": [[registro[c] for c in campos]
                          for clave, registro in self.primario.inorden()],
        }

    @staticmethod
    def desde_dict(datos, almacen=None):
        esquema = Esquema.desde_dict(datos["esquema"])
        tabla = Tabla(datos["tabla"], esquema, datos["arbol"], almacen)
        for valores in orden_por_medianas(datos["registros"]):
            tabla._poner(esquema.armar_registro(valores))
        if tabla.total != len(datos["registros"]):
            raise ErrorBD("el archivo trae claves primarias repetidas")
        for campo in datos["indices"]:
            esquema.exigir_campo(campo)
            tabla._construir_indice(campo)
        tabla._limpiar_rotaciones()
        return tabla
