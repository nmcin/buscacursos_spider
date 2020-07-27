import requests
from html.parser import HTMLParser
import json
import mysql.connector
import sys


# SETUP
if len(sys.argv) < 2:
    print('Debe entragar los argumentos AÑO y SEMESTRE')
    print('ej: python spider.py 2020 1')
    exit()
ANO = sys.argv[1]
SEMESTRE = sys.argv[2]

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
DELETE = f'DELETE FROM cursos WHERE nrc=%s and ano={ANO} and semestre={SEMESTRE};'


class BCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.toogle = False
        self.nested = 0
        self.text = ''
        self.current_escuela = ''
    
    def get_nrcs(self, html):
        self.nrcs = []
        self.feed(html)
        return self.nrcs

    def handle_starttag(self, tag, attrs):
        if tag == 'tr' and (\
                ('class', 'resultadosRowPar') in attrs \
                or ('class', 'resultadosRowImpar') in attrs):
            self.counter += 1
            self.toogle = True
        elif tag == 'tr' and self.toogle:
            self.nested += 1
            self.text += f'<{tag}>'
        elif self.toogle:
            self.text += f'<{tag}>'
        
        if tag == 'td' and ('colspan', '18') in attrs:
            self.current_escuela = '*'

    def handle_endtag(self, tag):
        if tag == 'tr' and self.toogle:
            if self.nested:
                self.nested -= 1
            else:
                self.toogle = False
                self.process_course()
                self.text = ''
        elif self.toogle:
            self.text += f'</{tag}>'
            if tag == 'td':
                self.text += '\n'

    def handle_data(self, data):
        if self.toogle:
            data = data.strip()
            self.text += data
        
        if self.current_escuela == '*':
            self.current_escuela = data

    def process_course(self):
        data = self.text.strip().split('\n')
        for index in range(len(data)):
            # data[index] = data[index][4:-5] # strip <td> </td>
            data[index] = data[index].replace('<td>', '').replace('</td>', '')
            data[index] = data[index].replace('<br>', '').replace('</br>', '')
        nrc = data[0]
        self.nrcs.append(nrc)

parser = BCParser()
total_del = 0
db_cursor.execute('SELECT DISTINCT LEFT(sigla,3) FROM cursos;')
for row in db_cursor.fetchall():
    comb = row[0]
    query = f'http://buscacursos.uc.cl/?cxml_semestre={ANO}-{SEMESTRE}&cxml_sigla={comb}'
    resp = requests.get(query)
    bc_nrcs = set(parser.get_nrcs(resp.text))
    db_cursor.execute(f'SELECT nrc FROM cursos where sigla like "{comb}%" and ano={ANO} and semestre={SEMESTRE};')
    db_nrcs = db_cursor.fetchall()
    db_nrcs = set(map(lambda x: x[0], db_nrcs))
    deleted = db_nrcs - bc_nrcs
    del_count = 0
    for nrc in deleted:
        print('del', nrc)
        db_cursor.execute(DELETE, (nrc,))
        cursos_db.commit()
        del_count += db_cursor.rowcount
    print(comb, ': deleted ->', del_count)
    total_del += del_count

print(total_del, 'courses deleted.')
