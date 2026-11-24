# Documentación técnica

**Motor de base de datos con árboles autobalanceados (AVL y Rojo-Negro)**

## 1. Diseño arquitectónico

El gestor es relacional: cada tabla tiene un esquema fijo de campos con tipo (`int`, `text`, `real`, `bool`) y una clave primaria. Está escrito en Python y solo usa la librería estándar, más `rich` para dibujar en la terminal. Se organiza en cinco módulos que se comunican en una sola dirección:

```
Usuario ─► REPL ─► Parser ─► Tabla / BaseDatos ─► Árbol AVL o Rojo-Negro
                                    │
                                    └─► AlmacenTabla ─► data/<tabla>.json
```

| Módulo | Archivos | Responsabilidad |
|---|---|---|
| CLI | `repl/REPL.py`, `main.py` | Lee comandos, los ejecuta y muestra tablas, mensajes y el dibujo del árbol. |
| Parser | `repl/Parser.py` | Convierte el texto en una orden (un diccionario con la acción y sus datos). |
| Almacenamiento | `model/Table.py`, `Database.py`, `Schema.py`, `Condition.py`, `Dataloader.py` | Valida tipos, ejecuta el CRUD, elige cómo resolver cada consulta y garantiza la atomicidad. |
| Índice | `model/Node.py`, `AVLNode.py`, `RBNode.py`, `Rotations.py`, `BST.py`, `AVLTree.py`, `RBTree.py`, `TreePrinter.py` | Árboles autobalanceados propios. |
| Persistencia | `storage/TableStorage.py` | Escribe y lee cada tabla en un archivo JSON. |

**El árbol es la tabla.** El índice primario asocia cada clave primaria con su registro completo, de modo que no existe una copia aparte de los datos. Cada índice secundario (`CREATE INDEX`) es otro árbol del mismo tipo que asocia cada valor del campo con el conjunto de claves primarias que lo tienen.

**Código compartido.** `ArbolBinario` (`BST.py`) contiene lo que no depende del balanceo: búsqueda, mínimo, sucesor, inserción como hoja, retiro de un nodo, recorrido inorden y rango. Las rotaciones están en `Rotations.py` y las usan los dos árboles. `ArbolAVL` y `ArbolRojoNegro` solo agregan su forma de reparar el invariante, por lo que la tabla trabaja igual con cualquiera de los dos.

## 2. Lenguaje de comandos

Las palabras clave y los nombres no distinguen mayúsculas. Varias órdenes en una línea se separan con `;`. Las líneas que empiezan con `--` son comentarios.

```
CREATE TABLE tabla (campo tipo [PRIMARY KEY], ...) [USING AVL | RB]
DROP TABLE [IF EXISTS] tabla
CREATE INDEX ON tabla (campo)
INSERT INTO tabla VALUES (valor, ...)
SELECT * | campo, ... FROM tabla [WHERE condición] [LIMIT n]
UPDATE tabla SET campo = valor, ... [WHERE condición]
DELETE FROM tabla [WHERE condición]
LOAD 'archivo.csv' INTO tabla
TREE tabla [campo] [niveles]
SHOW TABLES | DESCRIBE tabla | SOURCE 'archivo' | HELP | EXIT

condición :=  campo (= | != | < | <= | > | >=) valor
           |  campo BETWEEN valor AND valor
valor     :=  entero | decimal | 'texto' | true | false
tipo      :=  int | text | real | bool
```

Reglas del lenguaje:

- Si ningún campo lleva `PRIMARY KEY`, la clave primaria es el primer campo. Sin `USING`, el árbol es AVL.
- Todos los campos son obligatorios y se validan contra el esquema. Un entero en un campo `real` se convierte a real; cualquier otro cruce de tipos se rechaza.
- La clave primaria es única y no se puede modificar con `UPDATE`.
- `LOAD` inserta el CSV completo o nada: si una fila tiene un tipo inválido o una clave repetida, no entra ninguna.
- `TREE` dibuja el árbol con `rich.tree`. Si tiene más de 63 nodos muestra los primeros 5 niveles, o los que se indiquen.

**Cómo se resuelve una consulta.** Cada `SELECT` informa el camino que usó:

| Condición | Camino | Costo |
|---|---|---|
| `=` o rango sobre la clave primaria | Índice primario | O(log n + k) |
| `=` o rango sobre un campo con índice | Índice secundario y luego el primario | O(log n + k log n) |
| Campo sin índice, o `!=` | Recorrido completo | O(n) |

## 3. Diseño de los árboles

Los dos árboles son binarios de búsqueda con nodos enlazados: cada nodo guarda `clave`, `dato`, hijo izquierdo, hijo derecho y padre. Las hojas vacías son `None`. El enlace al padre permite subir desde un nodo sin recursión ni pila.

**Regla del sucesor.** El sucesor de un nodo es el siguiente de su inorden: el mínimo de su subárbol derecho o, si no tiene, el primer ancestro al que se llega subiendo desde un hijo izquierdo. Todo el proyecto se apoya en esa regla:

- *Eliminación.* Un nodo con dos hijos no se desenlaza: recibe la clave y el dato de su sucesor, y el que sale físicamente es el sucesor, que tiene como máximo un hijo. Así los dos árboles solo reparan el caso de un nodo con cero o un hijo.
- *Recorridos.* El inorden y las consultas por rango ubican el primer nodo y avanzan de sucesor en sucesor, por lo que entregan las claves ya ordenadas.

**Rotaciones.** Una rotación simple a la izquierda sobre A sube a su hijo derecho B: `A.hd = B.hi`, `B.hi = A`, y B ocupa el lugar de A bajo su padre. La rotación a la derecha es el espejo. Cada una cambia un número fijo de enlaces, cuesta O(1) y conserva el orden del inorden.

### 3.1 Árbol AVL

**Invariante.** En todo nodo, el factor de equilibrio `fe = altura(hi) − altura(hd)` está en {−1, 0, 1}. Cada nodo guarda su altura.

**Cómo se mantiene.** Después de insertar o eliminar, `_rebalancear` sube desde el padre del nodo afectado hasta la raíz. En cada nodo recalcula la altura y, si `|fe| > 1`, rota:

| Caso | Condición (hi, hd: hijo izquierdo y derecho) | Reparación |
|---|---|---|
| Izquierda-izquierda | `fe > 1` y `fe(hi) ≥ 0` | Rotación simple a la derecha |
| Izquierda-derecha | `fe > 1` y `fe(hi) < 0` | Izquierda sobre el hijo y derecha sobre el nodo |
| Derecha-derecha | `fe < −1` y `fe(hd) ≤ 0` | Rotación simple a la izquierda |
| Derecha-izquierda | `fe < −1` y `fe(hd) > 0` | Derecha sobre el hijo e izquierda sobre el nodo |

Una inserción se corrige con una sola rotación, simple o doble. Una eliminación puede necesitar una por nivel. La altura queda acotada por 1,44·log₂(n + 2).

### 3.2 Árbol Rojo-Negro

**Invariantes.** (1) Cada nodo es rojo o negro. (2) La raíz es negra. (3) Las hojas vacías cuentan como negras. (4) Un nodo rojo no tiene hijos rojos. (5) Todo camino de un nodo a sus hojas vacías pasa por la misma cantidad de nodos negros. De (4) y (5) se deduce que el camino más largo mide a lo sumo el doble del más corto, y que la altura no supera 2·log₂(n + 1).

**Inserción.** El nodo entra rojo, así que no altera la regla 5 y solo puede romper la 4. Mientras su padre sea rojo:

| Caso | Situación | Reparación |
|---|---|---|
| 1 | Tío rojo | Padre y tío pasan a negro, el abuelo a rojo, y se repite desde el abuelo |
| 2 | Tío negro, nodo y padre en triángulo | Rotación sobre el padre, que lo lleva al caso 3 |
| 3 | Tío negro, nodo y padre en línea | Padre negro, abuelo rojo y rotación sobre el abuelo |

Al terminar, la raíz se pinta de negro. Se hacen como máximo dos rotaciones.

**Eliminación.** Si el nodo retirado era rojo no hay nada que reparar. Si era negro, a ese camino le falta un negro. Sea `x` el nodo que quedó en su lugar (puede ser `None`, por eso se lleva también su padre). Mientras `x` sea negro y no sea la raíz:

| Caso | Situación | Reparación |
|---|---|---|
| 1 | Hermano rojo | Recolorear y rotar el padre; queda un hermano negro |
| 2 | Hermano negro con dos hijos negros | Hermano a rojo; el problema sube al padre |
| 3 | Hermano negro, sobrino cercano rojo | Recolorear y rotar el hermano, que lo lleva al caso 4 |
| 4 | Hermano negro, sobrino lejano rojo | Recolorear, rotar el padre y terminar |

Al final `x` se pinta de negro. Se hacen como máximo tres rotaciones.

**Comparación.** El AVL es más estricto: queda más bajo y busca un poco más rápido. El Rojo-Negro rota menos al modificar. Con 3000 claves insertadas en orden aleatorio ambos quedaron con altura 14; con claves ya ordenadas, el AVL quedó en 12 y el Rojo-Negro en 20.

## 4. Persistencia y recuperación

**Formato.** Cada tabla se guarda en `data/<tabla>.json` con su esquema, el tipo de árbol, los campos con índice secundario y los registros como listas en el orden del esquema, ordenados por clave primaria:

```json
{
  "tabla": "estudiantes",
  "arbol": "AVL",
  "esquema": {"clave_primaria": "codigo",
              "campos": [{"nombre": "codigo", "tipo": "int"},
                         {"nombre": "nombre", "tipo": "text"},
                         {"nombre": "promedio", "tipo": "real"}]},
  "indices": ["promedio"],
  "registros": [
    [2024001, "Santiago Suarez", 3.7],
    [2024002, "Mariana Martinez", 4.7]
  ]
}
```

Los árboles no se guardan: se reconstruyen a partir de los registros.

**Atomicidad por operación.** Cada comando que modifica datos sigue cuatro pasos:

1. **Validar todo antes de tocar nada:** tipos, cantidad de valores, existencia de campos y claves repetidas. Un comando inválido termina aquí sin cambiar la memoria ni el disco.
2. **Aplicar en memoria** sobre el árbol primario y los secundarios.
3. **Escribir en disco de forma atómica:** el archivo completo se escribe en `<tabla>.json.tmp`, se fuerza al disco con `fsync` y se renombra sobre el archivo real con `os.replace`, que el sistema operativo ejecuta como un solo paso.
4. **Si la escritura falla, deshacer** el cambio en memoria con la operación inversa e informar el error.

El archivo real siempre contiene un estado completo: el anterior o el nuevo, nunca uno a medias. Un `INSERT`, `UPDATE`, `DELETE` o `LOAD` que afecta muchos registros se guarda una sola vez, así que entra completo o no entra.

**Política de recuperación.** Al iniciar, `BaseDatos` recorre la carpeta `data/`:

- Un archivo `.tmp` es una escritura que no alcanzó a confirmarse. Se descarta, porque el `.json` conserva el último estado válido.
- Cada `.json` se carga y sus registros se validan otra vez contra el esquema.
- Si un archivo está dañado, se omite esa tabla, se avisa y las demás se cargan normalmente.

**Reconstrucción del índice.** Como los registros están ordenados en el archivo, se insertan *por medianas*: primero el del medio, después los medios de cada mitad, y así nivel por nivel. Con ese orden el árbol queda con la altura mínima, ⌈log₂(n + 1)⌉, y en las pruebas no necesitó ninguna rotación, ni en AVL ni en Rojo-Negro. Cuesta O(n log n). En el equipo de pruebas, 3000 registros con dos índices se recuperaron en 20 a 30 ms.

**Concurrencia.** No se implementó. El gestor atiende a un solo usuario y un solo proceso a la vez.

## 5. Análisis de complejidad

Sea *n* el número de registros, *k* el de resultados y *h* la altura del árbol. Los dos árboles garantizan h = O(log n).

**Operaciones del árbol**

| Operación | Tiempo | Espacio extra | Por qué |
|---|---|---|---|
| Buscar | O(log n) | O(1) | Baja un nivel por comparación |
| Insertar | O(log n) | O(1) | Baja hasta una hoja y repara subiendo |
| Eliminar | O(log n) | O(1) | Busca, toma el sucesor y repara subiendo |
| Rotación | O(1) | O(1) | Cambia un número fijo de enlaces |
| Sucesor | O(log n) | O(1) | Baja o sube a lo sumo *h* niveles |
| Inorden | O(n) | O(n) | Cada enlace se recorre dos veces como máximo |
| Rango | O(log n + k) | O(k) | Ubica el primero y avanza por sucesores |

Todas son iterativas. Cada árbol ocupa O(n): un nodo por clave con tres enlaces y la altura o el color.

**Operaciones del gestor** (con *m* índices secundarios)

| Comando | En memoria | Observación |
|---|---|---|
| `INSERT` | O((1 + m) log n) | Una inserción por árbol |
| `SELECT` por clave primaria | O(log n + k) | Igualdad o rango |
| `SELECT` por índice secundario | O(log n + k log n) | Cada resultado se busca en el primario |
| `SELECT` sin índice | O(n) | Recorrido completo |
| `UPDATE` / `DELETE` | selección + O(k (1 + m) log n) | Actualiza cada árbol afectado |
| `CREATE INDEX` | O(n log n) | Inserta todos los valores |
| `LOAD` de *r* filas | O(r (1 + m) log n) | Un solo guardado |
| Recuperación al iniciar | O((1 + m) n log n) | Sin rotaciones |

**Costo de la persistencia.** Cada comando que modifica una tabla reescribe su archivo completo, lo que cuesta O(n) en disco. Es el precio de un formato simple y de la escritura atómica, y es adecuado para los tamaños del proyecto. El costo O(log n) corresponde a las operaciones sobre el índice. Para tablas mucho más grandes, el paso siguiente sería un registro de cambios al que solo se le agregan líneas.

**Mediciones de referencia** (3000 productos; los tiempos varían según el equipo)

| Consulta | Camino | Tiempo |
|---|---|---|
| `WHERE id = 1500` | Índice primario | 0,002 ms |
| `WHERE precio BETWEEN 100000 AND 101500` (7 resultados) | Índice secundario | 0,006 ms |
| `WHERE stock > 498` (15 resultados) | Recorrido completo | 0,6 ms |

Con 100 000 claves insertadas en orden, el AVL quedó con altura 17 y el Rojo-Negro con 31, frente a los 100 000 niveles de un árbol binario sin balanceo.
