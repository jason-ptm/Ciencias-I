import json
import os


class AlmacenTabla:
    """Guarda y lee una tabla en un archivo JSON.

    La escritura es atomica: se escribe completo en un .tmp y despues se
    renombra sobre el archivo real. Si el programa se cae a mitad de camino,
    el archivo real sigue intacto con el ultimo estado valido.
    """

    def __init__(self, nombre, directorio="data"):
        self.directorio = directorio
        self.ruta = os.path.join(directorio, nombre + ".json")
        self.ruta_temporal = self.ruta + ".tmp"

    def guardar(self, datos):
        os.makedirs(self.directorio, exist_ok=True)
        with open(self.ruta_temporal, "w", encoding="utf-8") as archivo:
            archivo.write(self._serializar(datos))
            archivo.flush()
            os.fsync(archivo.fileno())          # que llegue al disco de verdad
        os.replace(self.ruta_temporal, self.ruta)   # paso atomico

    def cargar(self):
        with open(self.ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def borrar(self):
        for ruta in (self.ruta, self.ruta_temporal):
            if os.path.exists(ruta):
                os.remove(ruta)

    def _serializar(self, datos):
        # cabecera con sangria y un registro por linea, para poder leerlo
        cabecera = {k: v for k, v in datos.items() if k != "registros"}
        texto = json.dumps(cabecera, ensure_ascii=False, indent=2)
        filas = ",\n".join("    " + json.dumps(fila, ensure_ascii=False)
                           for fila in datos["registros"])
        return texto[:-2] + ',\n  "registros": [\n' + filas + "\n  ]\n}\n"
