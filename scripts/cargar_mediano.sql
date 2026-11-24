-- Dataset mediano: 3000 productos sobre un arbol Rojo-Negro.
--   python main.py scripts/cargar_mediano.sql

DROP TABLE IF EXISTS productos
CREATE TABLE productos (id int PRIMARY KEY, nombre text, categoria text, precio real, stock int, disponible bool) USING RB
LOAD 'datasets/productos_mediano.csv' INTO productos
CREATE INDEX ON productos (precio)
CREATE INDEX ON productos (categoria)
DESCRIBE productos
TREE productos 4
