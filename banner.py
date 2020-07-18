import mysql.connector
import requests
from html.parser import HTMLParser
import sys
from datetime import datetime
# from time import sleep


class BannerParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.toogle = False
        self.values = {}
        self.col = 0
        self.cupos = None

    def process(self, text):
        self.toogle = False
        self.values = {}
        self.col = 0
        self.name = None
        self.feed(text)
        return self.values

    def handle_starttag(self, tag, attrs):
        if not self.toogle and tag == 'tr' \
                and ('class', 'resultadosRowImpar') in attrs:
            self.toogle = True
        if tag == 'td' and self.toogle:
            self.col += 1

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.col = 0

    def handle_data(self, data):
        data = data.strip()
        if data == '&nbsp;':
            self.toogle = False
        if self.toogle and data:
            if self.col < 5:
                self.name = data
            elif self.col < 7:
                self.name += ' - ' + data
            elif self.col == 9:
                self.values[self.name] = int(data)
                self.name = 0


class BannerBCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.toogle = False
        self.col = 0
        self.cupos = None

    def process(self, text):
        self.toogle = False
        self.col = 0
        self.cupos = None
        self.feed(text)
        return self.cupos

    def handle_starttag(self, tag, attrs):
        if not self.toogle and tag == 'tr' \
                and ('class', 'resultadosRowPar') in attrs:
            self.toogle = True
        if tag == 'td' and self.toogle:
            self.col += 1

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.col = 0

    def handle_data(self, data):
        if self.col == 15 and self.toogle:
            self.cupos = int(data.strip())
            self.toogle = False


# Configurations
if len(sys.argv) < 2:
    print('Debe entragar los argumentos AÑO y SEMESTRE')
    print('ej: python proc_horarios.py 2020 1')
    exit()
ANO = sys.argv[1]
SEMESTRE = sys.argv[2]
print('Processing horarios on', ANO, SEMESTRE)

BANNER = '0'
if '-b' in sys.argv:
    BANNER = sys.argv[sys.argv.index('-b') + 1]

BATCH_SIZE = 100
INSERT = f'INSERT INTO banner (id, date, categoria, cupos, banner) VALUES (%s, %s, %s, %s, "{BANNER}");'

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
count = 0
parser = BannerParser()
parser_bc = BannerBCParser()
while offset < total:
    # Process by batches
    print('Processing from', offset, 'to', offset + BATCH_SIZE)
    db_cursor.execute(f'SELECT id, nrc FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE} ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset};')
    cursos = db_cursor.fetchall()
    for curso in cursos:
        id = int(curso[0])
        nrc = curso[1]
        query = f'http://buscacursos.uc.cl/informacionVacReserva.ajax.php?nrc={nrc}&termcode={ANO}-{SEMESTRE}'
        text = requests.get(query).text
        # sleep(0.1)
        date = str(datetime.now())
        cupos_dict = parser.process(text)
        if not len(cupos_dict):
            # Solo vacantes libres, buscar en página principal
            query = f'http://buscacursos.uc.cl/?cxml_semestre={ANO}-{SEMESTRE}&cxml_nrc={nrc}'
            text = requests.get(query).text
            cupos_dict = {
                'Total': parser_bc.process(text)
            }
        try:
            values = []
            for categoria, cupos in cupos_dict.items():
                values.append((id, date, categoria, cupos))
            db_cursor.executemany(INSERT, values)
            cursos_db.commit()
            print(db_cursor.rowcount, "id scrapped:", id)
        except Exception as err:
            print(err)
            with open('error.log', 'a+') as log:
                log.write('Error: ' + str(err) + '\n')
                log.write('Context: ' + str([id, date, BANNER, cupos_dict]) + '\n')
    print('BATCH ENDED')
    offset += BATCH_SIZE
