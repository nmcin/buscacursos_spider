import mysql.connector
import requests
from html.parser import HTMLParser
import sys
import json


# SETUP
updating = ('-u' in sys.argv) or ('--update' in sys.argv)

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
INSERT = 'INSERT INTO cursos_info (sigla, requisitos, con, restricciones) VALUES (%s, %s, %s, %s);'
UPDATE = 'UPDATE cursos_info SET requisitos = %s, con = %s, restricciones = %s WHERE sigla = %s;'


class RequisitosParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.toogle = False
        self.values = []

    def process(self, text):
        self.toogle = False
        self.values = []
        self.feed(text)
        return self.values[0], self.values[1], self.values[2]

    def handle_starttag(self, tag, attrs):
        if tag == 'span' and not self.toogle:
            self.toogle = True

    def handle_endtag(self, tag):
        if tag == 'span' and self.toogle:
            self.toogle = False

    def handle_data(self, data):
        if self.toogle and data:
            self.values.append(data)


# START
db_cursor.execute('SELECT count(distinct sigla) FROM cursos_info;')
total = int(db_cursor.fetchone()[0])
print(total, 'courses found.')

offset = 0
parser = RequisitosParser()
while offset < total:
    # Process by batches
    print('Processing from', offset, 'to', offset + BATCH_SIZE)
    db_cursor.execute(f'SELECT distinct sigla FROM cursos_info ORDER BY sigla LIMIT {BATCH_SIZE} OFFSET {offset};')
    siglas = db_cursor.fetchall()
    for sigla in siglas:
        sigla = sigla[0]
        query = f'http://catalogo.uc.cl/index.php?tmpl=component&view=requisitos&sigla={sigla}'
        db_cursor.execute('SELECT count(*),count(con) FROM cursos_info WHERE sigla = %s;', (sigla,))
        existance = db_cursor.fetchone()
        exists = bool(existance[0])
        has_req = bool(existance[1])
        if not exists:
            print('Inserting', sigla)
            text = requests.get(query).text
            req, con, restr = parser.process(text)
            try:
                db_cursor.execute(INSERT, (sigla, req, con, restr))
                cursos_db.commit()
                print(db_cursor.rowcount, "sigla scrapped:", sigla)
            except Exception as err:
                print(err)
                with open('error.log', 'a+') as log:
                    log.write('Error: ' + str(err) + '\n')
                    log.write('Context: ' + str([sigla, req, con, restr]) + '\n')
        elif updating:
            print('Updating', sigla)
            text = requests.get(query).text
            req, con, restr = parser.process(text)
            try:
                db_cursor.execute(UPDATE, (req, con, restr, sigla))
                cursos_db.commit()
                print(db_cursor.rowcount, "sigla scrapped:", sigla)
            except Exception as err:
                print(err)
                with open('error.log', 'a+') as log:
                    log.write('Error: ' + str(err) + '\n')
                    log.write('Context: ' + str([sigla, req, con, restr]) + '\n')
        elif not has_req:
            print('Inserting requisitos', sigla)
            text = requests.get(query).text
            req, con, restr = parser.process(text)
            try:
                db_cursor.execute(UPDATE, (req, con, restr, sigla))
                cursos_db.commit()
                print(db_cursor.rowcount, "sigla scrapped:", sigla)
            except Exception as err:
                print(err)
                with open('error.log', 'a+') as log:
                    log.write('Error: ' + str(err) + '\n')
                    log.write('Context: ' + str([sigla, req, con, restr]) + '\n')

    offset += BATCH_SIZE
