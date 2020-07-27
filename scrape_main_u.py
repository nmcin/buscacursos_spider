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

if '-f' in sys.argv:
    FROM = sys.argv[sys.argv.index('-f') + 1]
else:
    FROM = 'AAA'
print('Running spider on', ANO, SEMESTRE)

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


class BCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.toogle = False
        self.nested = 0
        self.text = ''
        self.current_escuela = ''

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
        course = {
            'nrc': data[0],
            'sigla': data[1][data[1].index('</img>') + 6 : data[1].index('</div>')],
            'retirable': False if data[2] == 'NO' else True,
            'en_ingles': False if data[3] == 'NO' else True,
            'seccion': int(data[4]),
            'aprob_especial': False if data[5] == 'NO' else True,
            'area': data[6],
            'formato': data[7],
            'categoria': data[8],
            'nombre': data[9],
            'profesor': data[10].replace('<a>', '').replace('</a>', ''),
            'campus': data[11],
            'creditos': int(data[12]),
            'cupos_total': int(data[13]),
            'cupos_disp': int(data[14]),
            'horario': '<>'.join(data[16:]).replace('<tr>', '\nROW: '),
            'escuela': self.current_escuela
        }
        # Quick horario processing
        course['horario'] = course['horario'].replace('<a>', '').replace('</a>', '')
        course['horario'] = course['horario'].replace('<table>', '').replace('</table>', '')
        course['horario'] = course['horario'].replace('<img>', '').replace('</img>', '')
        # Turn profesor Apellido Nombre to Nombre Apellido
        course['profesor'] = ','.join([prof.split(' ')[-1] + ' ' + ' '.join(prof.split(' ')[:-1]) for prof in course['profesor'].split(',')])

        try:
            UPSERT = f'IF EXISTS (SELECT * FROM cursos WHERE ano={ANO} AND semestre={SEMESTRE} AND nrc=\'{course["nrc"]}\')' +\
                f' THEN UPDATE cursos SET profesor="{course["profesor"]}", retirable={int(course["retirable"])}, en_ingles={int(course["en_ingles"])},' +\
                f'        aprob_especial={int(course["aprob_especial"])}, area="{course["area"]}", formato="{course["formato"]}", categoria="{course["categoria"]}",' +\
                f'        cupos_total={course["cupos_total"]}, cupos_disp={course["cupos_disp"]}, horario=\'{course["horario"]}\'' +\
                f' WHERE ano={ANO} AND semestre={SEMESTRE} AND nrc=\'{course["nrc"]}\';' +\
                f'ELSE' +\
                f'    INSERT INTO cursos (ano, semestre, nrc, sigla, seccion,' +\
                                    f'nombre, profesor, retirable, en_ingles,' +\
                                    f'aprob_especial, area, formato, categoria,' +\
                                    f'campus, creditos, cupos_total, cupos_disp,' +\
                                    f'horario, escuela) VALUES ({ANO}, {SEMESTRE},' +\
                                    f'%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s); END IF;'
            db_cursor.execute(UPSERT, (
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
                course['horario'],
                course['escuela']
            ))
            cursos_db.commit()
            print(db_cursor.rowcount, "record upserted. Course", self.counter)
        except Exception as err:
            print(err)
            with open('error.log', 'a+') as log:
                log.write('Error: ' + str(err) + '\n')
                log.write('Context: ' + json.dumps(course, indent=4) + '\n')


parser = BCParser()
db_cursor.execute('SELECT DISTINCT LEFT(sigla,3) FROM cursos;')
for row in db_cursor.fetchall():
    comb = row[0]
    print('Searching', comb)
    query = f'http://buscacursos.uc.cl/?cxml_semestre={ANO}-{SEMESTRE}&cxml_sigla={comb}'
    resp = requests.get(query)
    parser.feed(resp.text)

print(parser.counter, 'courses found.')
