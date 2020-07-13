import mysql.connector
import requests
from html.parser import HTMLParser
import sys


class ProgramParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.toogle = False
        self.text = ''

    def process(self, text):
        self.toogle = False
        self.text = ''
        self.feed(text)
        return self.text

    def handle_starttag(self, tag, attrs):
        if tag == 'pre' and not self.toogle:
            self.toogle = True
            self.text = ''
        elif self.toogle:
            self.text += f'<{tag}>'

    def handle_endtag(self, tag):
        if tag == 'pre' and self.toogle:
            self.toogle = False
        elif self.toogle:
            self.text += f'</{tag}>'

    def handle_data(self, data):
        if self.toogle:
            self.text += data


# Configurartions
BATCH_SIZE = 100
INSERT = 'INSERT INTO cursos_info (sigla, raw) VALUES (%s, %s)'
UPDATE = 'UPDATE cursos_info SET raw = %s WHERE sigla = %s'

cursos_db = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="admin",
  database="cursos"
)
db_cursor = cursos_db.cursor()

updating = ('-u' in sys.argv) or ('--update' in sys.argv)

db_cursor.execute('SELECT count(distinct sigla) FROM cursos;')
total = int(db_cursor.fetchone()[0])
print(total, 'courses found.')

offset = 0
parser = ProgramParser()
while offset < total:
    # Process by batches
    print('Processing from', offset, 'to', offset + BATCH_SIZE)
    db_cursor.execute(f'SELECT distinct sigla FROM cursos ORDER BY sigla LIMIT {BATCH_SIZE} OFFSET {offset};')
    siglas = db_cursor.fetchall()
    for sigla in siglas:
        sigla = sigla[0]
        print('Processing', sigla)
        query = f'http://catalogo.uc.cl/index.php?tmpl=component&view=programa&sigla={sigla}'
        db_cursor.execute('SELECT count(sigla) FROM cursos_info WHERE sigla = %s;', (sigla,))
        exists = bool(db_cursor.fetchone()[0])
        if not exists:
            print('Inserting', sigla)
            text = requests.get(query).text
            raw = parser.process(text)
            try:
                db_cursor.execute(INSERT, (sigla, raw))
                cursos_db.commit()
                print(db_cursor.rowcount, "sigla scrapped:", sigla)
            except Exception as err:
                print(err)
                with open('error.log', 'a+') as log:
                    log.write('Error: ' + str(err) + '\n')
                    log.write('Context: ' + str(sigla) + '\n')
        elif updating:
            print('Updating', sigla)
            text = requests.get(query).text
            raw = parser.process(text)
            try:
                db_cursor.execute(UPDATE, (raw, sigla))
                cursos_db.commit()
                print(db_cursor.rowcount, "sigla scrapped:", sigla)
            except Exception as err:
                print(err)
                with open('error.log', 'a+') as log:
                    log.write('Error: ' + str(err) + '\n')
                    log.write('Context: ' + str(sigla) + '\n')
        else:
            print('Skipping', sigla)

    offset += BATCH_SIZE
