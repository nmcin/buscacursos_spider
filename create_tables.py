import mysql.connector


cursos_db = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="admin",
  database="cursos"
)
db_cursor = cursos_db.cursor()

CURSOS = """CREATE TABLE `cursos` (
    `ano` int(11) DEFAULT NULL,
    `semestre` int(11) DEFAULT NULL,
    `nrc` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `sigla` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `seccion` int(11) DEFAULT NULL,
    `nombre` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `profesor` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `retirable` tinyint(1) DEFAULT NULL,
    `en_ingles` tinyint(1) DEFAULT NULL,
    `aprob_especial` tinyint(1) DEFAULT NULL,
    `area` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `formato` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `categoria` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `campus` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `creditos` int(11) DEFAULT NULL,
    `cupos_total` int(11) DEFAULT NULL,
    `cupos_disp` int(11) DEFAULT NULL,
    `horario` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `id` int(11) NOT NULL AUTO_INCREMENT,
    PRIMARY KEY (`id`),
    UNIQUE KEY `duplicates` (`nrc`,`ano`,`semestre`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""
print(CURSOS)

HORARIOS = """CREATE TABLE `horarios` (
    `id` int(11) NOT NULL,
    """
for day in 'LMWJVS':
    for mod in range(1, 9):
        HORARIOS += '`' + day + str(mod) + """` varchar(4) DEFAULT 'FREE',
    """

HORARIOS += """PRIMARY KEY (`id`));"""
print(HORARIOS)

HORARIOS_INFO = """CREATE TABLE `horarios_info` (
    `id` int(11) NOT NULL,
    `total` int(11) DEFAULT 0,
    """
mod_types = set()
for day in 'LMWJVS':
    for mod in range(1, 9):
        db_cursor.execute(f'SELECT distinct {day + str(mod)} FROM horarios;')
        res = db_cursor.fetchall()
        for mod_type in res:
            mod_types.add(mod_type[0])
mod_types.remove('FREE')
mod_types = list(mod_types)
mod_types.sort()
for mod_type in mod_types:
    HORARIOS_INFO += f'`{mod_type}` ' + """int(11) DEFAULT 0,
    """
HORARIOS_INFO += """PRIMARY KEY (`id`));"""
print(HORARIOS_INFO)