import requests
from html.parser import HTMLParser
import json
import mysql.connector


cursos_db = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="admin",
  database="cursos"
)

ANO = '2019'
SEMESTRE = '2'

db_cursor = cursos_db.cursor()
UPDATE = f'UPDATE cursos SET horario = %s' +\
            f'WHERE nrc= %s AND ano = {ANO} AND semestre = {SEMESTRE}'


class BCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.toogle = False
        self.nested = 0
        self.text = ''

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

    def process_course(self):
        data = self.text.strip().split('\n')
        nrc = data[0].replace('<td>', '').replace('</td>', '')
        horario = '<>'.join(data[16:]).replace('<tr>', '\nROW: ')
        horario = horario.replace('<td>', '').replace('</td>', '')
        horario = horario.replace('<a>', '').replace('</a>', '')
        horario = horario.replace('<table>', '').replace('</table>', '')
        horario = horario.replace('<img>', '').replace('</img>', '')
        try:
            db_cursor.execute(UPDATE, (horario, nrc))
            cursos_db.commit()
            print(db_cursor.rowcount, "record updated. Course", self.counter)
        except Exception as err:
            print(err)


parser = BCParser()
db_cursor.execute(f'SELECT DISTINCT sigla FROM cursos WHERE ano = {ANO} AND semestre = {SEMESTRE};')
ramos = db_cursor.fetchall()
for ramo in ramos:
    ramo = ramo[0]
    print('Search', ramo)
    query = f'http://buscacursos.uc.cl/?cxml_semestre={ANO}-{SEMESTRE}&cxml_sigla={ramo}'
    resp = requests.get(query)
    parser.feed(resp.text)
print(parser.counter, 'courses found.')
