-- Dataset pequeno: 25 estudiantes sobre un arbol AVL.
--   python main.py scripts/cargar_pequeno.sql

DROP TABLE IF EXISTS estudiantes
CREATE TABLE estudiantes (codigo int PRIMARY KEY, nombre text, carrera text, semestre int, promedio real, activo bool) USING AVL
LOAD 'datasets/estudiantes_pequeno.csv' INTO estudiantes
CREATE INDEX ON estudiantes (promedio)
DESCRIBE estudiantes
TREE estudiantes
