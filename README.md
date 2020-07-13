# BuscaCursosUC Spider
Python scripts that retrieve courses data from BuscaCursos UC and save it to 
a MySQL database.

## ```spider.py```
For a given Year-Semester scrapes all siglas and inserts courses data from 
the results table to a database. 
Ejecutar ```python spider.py AÑO SEMESTRE [-f start_comb]```.

## ```proc_horarios.py```
For a given Year-Semester reads all horarios column from cursos and process 
them to a new table, in the form of a matrix with the type of module for all 
modules from monday to saturday. 
Ejecutar ```python proc_horarios.py AÑO SEMESTRE```.
