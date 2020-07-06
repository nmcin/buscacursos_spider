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
INSERT = f'INSERT INTO cursos (ano, semestre, nrc, sigla, seccion,' +\
                             f'nombre, profesor, retirable, en_ingles,' +\
                             f'aprob_especial, area, formato, categoria,' +\
                             f'campus, creditos, cupos_total, cupos_disp,' +\
                             f'horario) VALUES ({ANO}, {SEMESTRE},' +\
                             f'%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'


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
        for index in range(len(data)):
            # data[index] = data[index][4:-5] # strip <td> </td>
            data[index] = data[index].replace('<td>', '').replace('</td>', '')
            data[index] = data[index].replace('<br>', '').replace('</br>', '')
        course = {
            'nrc': data[0],
            'sigla': data[1][data[1].index('</img>') + 6 : data[1].index('</div>')],
            'retirable': True if data[2] == 'SI' else False,
            'en_ingles': True if data[3] == 'SI' else False,
            'seccion': int(data[4]),
            'aprob_especial': True if data[5] == 'SI' else False,
            'area': data[6],
            'formato': data[7],
            'categoria': data[8],
            'nombre': data[9],
            'profesor': data[10].replace('<a>', '').replace('</a>', ''),
            'campus': data[11],
            'creditos': int(data[12]),
            'cupos_total': int(data[13]),
            'cupos_disp': int(data[14]),
            'horario': '<>'.join(data[16:]).replace('<tr>', '\nROW: ')
        }
        course['horario'] = course['horario'].replace('<a>', '').replace('</a>', '')
        course['horario'] = course['horario'].replace('<table>', '').replace('</table>', '')
        course['horario'] = course['horario'].replace('<img>', '').replace('</img>', '')
        print(json.dumps(course, indent=4))
        try:
            db_cursor.execute(INSERT, (
                course['nrc'],
                course['sigla'],
                course['seccion'],
                course['nombre'],
                course['profesor'],
                course['retirable'],
                course['en_ingles'],
                course['aprob_especial'],
                course['area'],
                course['formato'],
                course['categoria'],
                course['campus'],
                course['creditos'],
                course['cupos_total'],
                course['cupos_disp'],
                course['horario']
            ))
            cursos_db.commit()
            print(db_cursor.rowcount, "record inserted. Course", self.counter)
        except Exception as err:
            print(err)


parser = BCParser()
# Search in every possible 3 letter combination
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for l1 in LETTERS:
    for l2 in LETTERS:
        for l3 in LETTERS:
            comb = l1 + l2 + l3
            print('Search', comb)
            query = f'http://buscacursos.uc.cl/?cxml_semestre={ANO}-{SEMESTRE}&cxml_sigla={comb}'
            resp = requests.get(query)
            parser.feed(resp.text)
print(parser.counter, 'courses found.')
