import mysql.connector
import sys


if len(sys.argv) < 2:
    print('Debe entragar los argumentos AÑO y SEMESTRE')
    print('ej: python proc_horarios.py 2020 1')
    exit()
ANO = sys.argv[1]
SEMESTRE = sys.argv[2]
print('Processing horarios on', ANO, SEMESTRE)

BATCH_SIZE = 100


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
    INSERT = f'INSERT INTO horarios ({cols}) VALUES ({values})'
    try:
        db_cursor.execute(INSERT)
        cursos_db.commit()
        print(db_cursor.rowcount, "horario procesed.", id)
    except Exception as err:
        print(err)
        with open('error.log', 'a+') as log:
            log.write('Error: ' + str(err) + '\n')
            log.write('Context: ' + str(id) + '\n')


cursos_db = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="admin",
  database="cursos"
)
db_cursor = cursos_db.cursor()

db_cursor.execute(f'SELECT count(nrc) FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE};')
total = int(db_cursor.fetchone()[0])
print(total, 'courses found.')

offset = 0
while offset < total:
    # Process by batches
    print('Processing from', offset, 'to', offset + BATCH_SIZE)
    db_cursor.execute(f'SELECT id, horario FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE} LIMIT {BATCH_SIZE} OFFSET {offset};')
    ramos = db_cursor.fetchall()
    for ramo in ramos:
        process_course(ramo[0], ramo[1])
    offset += BATCH_SIZE
