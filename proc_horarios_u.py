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


def process_course(id, data):
    data = data.split('\nROW: ')[1:]
    # data rows -> day-day:module,module <> type <> room <><>
    cols = ['id']
    values = [str(id)]
    for row in data:
        row = row.split('<>')[:2]
        horario = row[0].split(':')
        days = horario[0].split('-')
        modules = horario[1].split(',')
        for day in days:
            for mod in modules:
                if day and mod and (day + mod) not in cols:
                    cols.append(day + mod)
                    values.append("'" + row[1] + "'")
    cols = ','.join(cols)
    values = ','.join(values)
    INSERT = f'DELETE FROM horarios WHERE id={id}; INSERT INTO horarios ({cols}) VALUES ({values});'
    try:
        db_cursor.execute(f'DELETE FROM horarios WHERE id={id};')
        cursos_db.commit()
        db_cursor.execute(f'INSERT INTO horarios ({cols}) VALUES ({values});')
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
    db_cursor.execute(f'SELECT id, horario FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE} ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset};')
    ramos = db_cursor.fetchall()
    for ramo in ramos:
        process_course(ramo[0], ramo[1])
    offset += BATCH_SIZE
