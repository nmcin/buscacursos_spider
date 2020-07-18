# BuscaCursosUC Spider
Python scripts that retrieve courses data from BuscaCursos UC and save it to 
a MySQL database.

## ```spider.py```
For a given Year-Semester scrapes all siglas and inserts courses data from 
the results table to a database. 
Run ```python spider.py AÑO SEMESTRE [-f start_comb]```.

## ```proc_horarios.py```
For a given Year-Semester reads all horarios column from cursos and process 
them to a new table, in the form of a matrix with the type of module for all 
modules from monday to saturday. 
Run ```python proc_horarios.py AÑO SEMESTRE```.

## ```proc_horarios_more.py```
For a given Year-Semester reads all horarios column from horarios and process 
them to a new table, with the sum of modules of each type and total.
Run ```python proc_horarios_more.py AÑO SEMESTRE```.

## ```get_programa.py```
Scrapes all programas for siglas present in the cursos table. In standard 
mode, checks if a programa already exists and skips if one is found. In 
update mode, retrieves all programas and update them in the database.
Run ```python get_programa.py [-u | --update]```.

## ```get_requisitos.py```
Scrapes all requisitos for siglas present in the cursos table. In standard 
mode, checks if a requisito already exists and skips if one is found. In 
update mode, retrieves all requisitos and update them in the database.
Run ```python get_requisitos.py [-u | --update]```.