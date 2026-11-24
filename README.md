# Motor de base de datos con árboles autobalanceados

Gestor de base de datos relacional en Python que guarda e indexa sus tablas con árboles **AVL** y **Rojo-Negro** implementados desde cero. Tiene esquemas con tipos, operaciones CRUD con un lenguaje tipo SQL, consultas por igualdad y por rango en O(log n), persistencia en JSON con escritura atómica y una línea de comandos (REPL) que dibuja el árbol balanceado.

## Requisitos e instalación

- Python 3.8 o superior
- La librería `rich` (para dibujar los árboles y las tablas en la terminal)

```bash
pip install -r requirements.txt
```

## Cómo ejecutar

Todos los comandos se corren desde la carpeta del proyecto.

```bash
python main.py                              # abre el REPL
python main.py scripts/cargar_pequeno.sql   # carga 25 estudiantes en un AVL
python main.py scripts/cargar_mediano.sql   # carga 3000 productos en un Rojo-Negro
python scripts/demo_arboles.py              # los dos árboles paso a paso
python -m unittest discover -s tests -t .   # corre las 73 pruebas
```

Las tablas se guardan en `data/`. Con `python main.py --data otra_carpeta` se usa otra ubicación.

## Comandos

| Comando | Qué hace |
|---|---|
| `CREATE TABLE t (campo tipo [PRIMARY KEY], ...) [USING AVL\|RB]` | Crea una tabla. Sin `PRIMARY KEY`, la clave es el primer campo. Sin `USING`, el árbol es AVL. |
| `DROP TABLE [IF EXISTS] t` | Borra la tabla y su archivo. |
| `CREATE INDEX ON t (campo)` | Crea un índice secundario sobre un campo. |
| `INSERT INTO t VALUES (v1, v2, ...)` | Inserta un registro (valores en el orden del esquema). |
| `SELECT * \| campo, ... FROM t [WHERE condición] [LIMIT n]` | Consulta registros. |
| `UPDATE t SET campo = valor, ... [WHERE condición]` | Actualiza los registros que cumplan. |
| `DELETE FROM t [WHERE condición]` | Elimina los registros que cumplan. |
| `LOAD 'archivo.csv' INTO t` | Carga un CSV completo, o nada si alguna fila falla. |
| `TREE t [campo] [niveles]` | Dibuja el árbol del índice. |
| `SHOW TABLES`, `DESCRIBE t` | Lista las tablas o describe una. |
| `SOURCE 'archivo.sql'` | Ejecuta un archivo de comandos. |
| `HELP`, `EXIT` | Ayuda y salida. |

- **Tipos:** `int`, `text`, `real`, `bool`.
- **Valores:** `12`, `-3.5`, `'texto'`, `true`, `false`.
- **Condiciones:** `=`, `!=`, `<`, `<=`, `>`, `>=` y `BETWEEN a AND b`, sobre un campo.
- Las palabras clave y los nombres no distinguen mayúsculas. Las líneas que empiezan con `--` son comentarios.

## Ejemplo de sesión

```text
bd> CREATE TABLE estudiantes (codigo int PRIMARY KEY, nombre text, promedio real, activo bool) USING AVL
Tabla 'estudiantes' creada (arbol AVL, clave primaria 'codigo').

bd> INSERT INTO estudiantes VALUES (10, 'Ana', 4.5, true)
bd> INSERT INTO estudiantes VALUES (20, 'Luis', 3.1, true)
bd> INSERT INTO estudiantes VALUES (30, 'Sofia', 3.9, false)
1 registro insertado.
  balanceo AVL: rotacion simple izquierda sobre 10

bd> SELECT * FROM estudiantes WHERE codigo BETWEEN 10 AND 20
2 registro(s) · indice AVL de la clave primaria 'codigo' · 0.006 ms

bd> CREATE INDEX ON estudiantes (promedio)
bd> SELECT nombre, promedio FROM estudiantes WHERE promedio >= 3.5
2 registro(s) · indice AVL sobre 'promedio' · 0.009 ms

bd> UPDATE estudiantes SET promedio = 4.0 WHERE codigo = 20
bd> DELETE FROM estudiantes WHERE activo = false

bd> TREE estudiantes
Indice AVL sobre 'codigo' · 2 nodos · altura 2
20 (raiz, h=2, fe=1)
└── 10 (izq, h=1, fe=0)
equilibrado: True
```

Cada `SELECT` informa cómo se resolvió: por índice (árbol) o recorriendo toda la tabla. Al cerrar y volver a abrir, las tablas se restauran solas.

## Estructura del proyecto

```
├── main.py                  punto de entrada (REPL o archivo de comandos)
├── model/
│   ├── Node.py              nodo base: clave, dato, hijos y padre
│   ├── AVLNode.py           nodo AVL: altura y factor de equilibrio
│   ├── RBNode.py            nodo Rojo-Negro: color
│   ├── Rotations.py         rotaciones simples, comunes a los dos árboles
│   ├── BST.py               árbol base: búsqueda, sucesor, inorden, rango
│   ├── AVLTree.py           balanceo por alturas
│   ├── RBTree.py            balanceo por colores
│   ├── TreePrinter.py       dibujo del árbol con rich.tree
│   ├── Schema.py            esquema: campos, tipos y validación
│   ├── Condition.py         condición de un WHERE
│   ├── Table.py             tabla: CRUD, índices y atomicidad
│   ├── Database.py          gestor de tablas y recuperación al iniciar
│   ├── Dataloader.py        carga de CSV
│   └── Errors.py            error del motor
├── storage/
│   └── TableStorage.py      persistencia JSON con escritura atómica
├── repl/
│   ├── Parser.py            lenguaje de comandos
│   └── REPL.py              línea de comandos
├── datasets/                dataset pequeño (25) y mediano (3000)
├── scripts/                 generador de datasets, scripts de carga y demo
├── tests/                   pruebas unitarias
└── docs/                    documentación técnica
```

## Datasets

| Archivo | Registros | Script de carga | Árbol |
|---|---|---|---|
| `datasets/estudiantes_pequeno.csv` | 25 | `scripts/cargar_pequeno.sql` | AVL |
| `datasets/productos_mediano.csv` | 3000 | `scripts/cargar_mediano.sql` | Rojo-Negro |

`python scripts/generar_datasets.py` los vuelve a generar (siempre con los mismos datos).

## Pruebas

| Archivo | Qué demuestra |
|---|---|
| `tests/test_avl.py` | Las cuatro rotaciones, inserción, búsqueda, sucesor, eliminación, rango y altura O(log n). |
| `tests/test_rb.py` | Casos de inserción, eliminación hasta vaciar, invariantes de color y altura O(log n). |
| `tests/test_tabla.py` | Esquemas y CRUD completo, con índice AVL y con índice Rojo-Negro. |
| `tests/test_persistencia.py` | Recuperación tras reinicio, reversión si falla el disco y archivos dañados. |
| `tests/test_parser.py` | Sintaxis de todos los comandos y sus errores. |
| `tests/test_repl.py` | Flujo completo con los dos datasets. |

## Complejidad

| Operación | Tiempo |
|---|---|
| Buscar, insertar o eliminar en el árbol | O(log n) |
| Sucesor | O(log n) |
| Recorrido inorden | O(n) |
| Rango con k resultados | O(log n + k) |
| Consulta sobre un campo sin índice | O(n) |

El detalle, junto con el diseño de los árboles y de la persistencia, está en [docs/DOCUMENTACION_TECNICA.md](docs/DOCUMENTACION_TECNICA.md).
