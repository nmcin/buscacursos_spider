# BuscaCursosUC Scrapper
Python scripts that retrieve courses data from BuscaCursosUC and Catálogo UC 
and save it to a MySQL database.

## ```scrape_banner.py```
For a given Year-Semester scrapes all siglas and inserts courses data from 
the results table to a database. 
Run ```python scrape_banner.py YEAR SEMESTER [-f start_comb]```.

## ```scrape_programas.py```
Scrapes all programas for siglas present in the cursos table. In standard 
mode, checks if a programa already exists and skips if one is found. In 
update mode, retrieves all programas and update them in the database.
Run ```python scrape_programas.py [-u | --update]```.

## ```scrape_requisitos.py```
Scrapes all requisitos for siglas present in the cursos table. In standard 
mode, checks if a requisito already exists and skips if one is found. In 
update mode, retrieves all requisitos and update them in the database.
Run ```python scrape_requisitos.py [-u | --update]```.

## ```scrape_banner.py```
Scrapes available cupos for all courses in a given YEAR SEMESTER. Accepts a 
banner name parameter that adds to the database. Saves the cupos by category 
and with a retrieval datetime.
Run ```python scrape_requisitos.py YEAR SEMESTER```.

## ```proc_horarios.py```
For a given Year-Semester reads all horarios column from cursos and process 
them to a new table, in the form of a matrix with the type of module for all 
modules from monday to saturday. 
Run ```python proc_horarios.py YEAR SEMESTER```.

## ```proc_horarios_more.py```
For a given Year-Semester reads all horarios column from horarios and process 
them to a new table, with the sum of modules of each type and total.
Run ```python proc_horarios_more.py YEAR SEMESTER```.
