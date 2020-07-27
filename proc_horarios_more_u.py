import mysql.connector
import sys
import json


# SETUP
if len(sys.argv) < 2:
    print('Debe entragar los argumentos AÑO y SEMESTRE')
    print('ej: python proc_horarios.py 2020 1')
    exit()
ANO = sys.argv[1]
SEMESTRE = sys.argv[2]
print('Processing horarios on', ANO, SEMESTRE)

settings = None
with open('settings.json') as file:
    settings = json.load(file)

cursos_db = mysql.connector.connect(
  host=settings['db_host'],
  user=settings['db_user'],
  password=settings['db_passwd'],
  database=settings['db_name']
)
db_cursor = cursos_db.cursor()
BATCH_SIZE = settings['batch_size']
INSERT = 'INSERT INTO horarios_info (id, total, AYU, CLAS, LAB, PRA, SUP, TAL, TER, TES) ' +\
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'


def process_course(id):
    db_cursor.execute('SELECT * FROM horarios WHERE id = %s;', (id,))
    horario = db_cursor.fetchone()[1:]
    data = {'id': id, 'total': 0}
    total = 0
    for type in ['AYU', 'CLAS', 'LAB', 'PRA', 'SUP', 'TAL', 'TER', 'TES']:
        data[type] = horario.count(type)
        total += data[type]
    data['total'] = total
    print(list(data.values()))
    try:
        db_cursor.execute('DELETE FROM horarios_info WHERE id=%s;', (id,))
        cursos_db.commit()
        db_cursor.execute(INSERT, list(data.values()))
        cursos_db.commit()
        print(db_cursor.rowcount, "horario procesed.", id)
    except Exception as err:
        print(err)
        with open('error.log', 'a+') as log:
            log.write('Error: ' + str(err) + '\n')
            log.write('Context: ' + str(id) + '\n')


# START
db_cursor.execute(f'SELECT count(nrc) FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE};')
total = int(db_cursor.fetchone()[0])
print(total, 'courses found.')

offset = 0
while offset < total:
    # Process by batches
    print('Processing from', offset, 'to', offset + BATCH_SIZE)
    db_cursor.execute(f'SELECT id FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE} ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset};')
    ramos = db_cursor.fetchall()
    for ramo in ramos:
        process_course(ramo[0])
    offset += BATCH_SIZE
