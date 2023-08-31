import openpyxl as xl
import json
from os import path

def generate_template():
    directory = path.dirname(__file__)
    f = open(path.join(directory, "output", "worklot_documents.json"), "r")
    worklots = json.loads(f.read())
    f.close()


    wb = xl.Workbook()
    ws = wb.active
    ws.title = 'data upload'
    ws.append(['Reference', 'Id', 'Handover Package', 'Design Package'])

    for worklot in worklots:
        worklot = worklots[worklot]
        reference = worklot.get('Reference')
        id = worklot.get('Id')
        ws.append([reference, id])

    for row in ws.iter_rows(min_row=2):
        id = row[1].value
        reference = row[0]
        reference.hyperlink = "https://auweb06.au.itwocx.com/cxR/cx.aspx?j=GLU-VCA&t=LOT&i=%s&mdu=COR" % id
        reference.style = 'Hyperlink'

    wb.save('template.xlsx')
    wb.close()

if __name__ == '__main__':
    generate_template()