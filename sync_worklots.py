import json
import openpyxl as xl
import datetime as datetime
from os import path, makedirs

# local modules
from itwocxapi import api
from batch_get_docs import batch_get_docs

directory = path.dirname(__file__)

class Sync:
    def __init__(self):
        self.last_updated = None
        self.progress = { "stage": "Starting"}

    def get_worklot_documents(self):
        doc_list = api.request_doc_list(
            {    
                "CriterionList": {
                "cx_scope": "ALL",
                "cx_regtype": "LOT",
                "cx_projects": "GLU-VCA"
                }
            }
        )
        self.progress = { "stage": "Getting worklot documents", "i": 0, "n": len(doc_list) }
        docs = batch_get_docs(doc_list, self.progress)
        self.progress = { "stage": "Getting linked documents", "i": len(doc_list), "n": len(doc_list) }
        library = {}
        for doc in docs:
            id = doc.get('Id')
            library[id] = doc

        f = open(path.join(directory, "output", "worklot_documents.json"), "w")
        f.write(json.dumps(library, indent="\t"))
        f.close()

    def get_linked_documents(self):

        with open(path.join(directory, 'output', 'worklot_documents.json'), 'r') as f:
            lot_library = json.loads(f.read())

        ids = []
        for id in lot_library:
            worklot = lot_library[id]
            linked_documents = worklot.get('LinkedDocuments')
            for linked_document in linked_documents:
                linked_id = linked_document.get('DocumentId')
                if not linked_id in ids:
                    ids.append(linked_id)
        
        self.progress = { "stage": "Getting linked documents", "i": 0, "n": len(ids) }
        docs = batch_get_docs(ids, self.progress)
        self.progress = { "stage": "Getting linked documents", "i": len(ids), "n": len(ids) }

        library = {}
        for doc in docs:
            id = doc.get('Id')
            library[id] = doc

        with open(path.join(directory, 'output', 'linked_documents.json'), 'w') as f:
            f.write(json.dumps(library, indent="\t"))

        for id in lot_library:
            worklot = lot_library[id]
            linked_documents = worklot.get('LinkedDocuments')
            for linked_document in linked_documents:
                linked_id = linked_document.get('DocumentId')
                linked_document["document"] = library[linked_id]

        with open(path.join(directory, 'output', 'worklot_documents_with_linked_documents.json'), 'w') as f:
            f.write(json.dumps(lot_library, indent="\t"))

    def extract_packages(self):
        self.progress = { "stage": "Extracting packages" }
        wb = xl.load_workbook(path.join(directory, 'worklots_by_packages.xlsx'), data_only=True)
        ws_worklots = wb['data upload']
        worklots = {}
        worklots_headers = ["Reference", "ID", "HP", "DP"] 
        for row in ws_worklots.iter_rows(min_row=2):
            entry = {}
            for cell in row:
                index = cell.column - 1
                entry[worklots_headers[index]] = cell.value
            worklots[entry.get('ID')] = entry
        wb.close()

        with open(path.join(directory, 'output', 'worklots_by_packages.json'), 'w') as f:
            f.write(json.dumps(worklots, indent="\t"))


    def compile_packages(self):
        self.progress = { "stage": "Compiling" }
        with open(path.join(directory, 'output', 'worklots_by_packages.json'), 'r') as f:
            worklots_by_packages = json.loads(f.read())

        with open(path.join(directory, 'output', 'worklot_documents_with_linked_documents.json'), 'r') as f:
            worklots = json.loads(f.read())

        handover_packages = {}
        design_packages = {}
        for id in worklots_by_packages:
            worklot = worklots_by_packages[id]
            document = worklots.get(id)
            worklot["document"] = document
            status = document.get('StatusName')

            # handover packages
            handover_package = worklot.get('HP')
            if not handover_package in handover_packages:
                handover_packages[handover_package] = { "stats": {}, "name": handover_package, "worklots": [worklot] }
            else:
                handover_packages[handover_package]["worklots"].append(worklot)
            if status in handover_packages[handover_package]["stats"]:
                handover_packages[handover_package]["stats"][status] += 1
            else:
                handover_packages[handover_package]["stats"][status] = 1

            # design packages
            design_package = worklot.get('DP')
            if not design_package in design_packages:
                design_packages[design_package] = { "stats": {}, "name": design_package, "worklots": [worklot] }
            else:
                design_packages[design_package]["worklots"].append(worklot)
            if status in design_packages[design_package]["stats"]:
                design_packages[design_package]["stats"][status] += 1
            else:
                design_packages[design_package]["stats"][status] = 1

        handover_package_folder = path.join(directory, 'output', 'handover_packages')
        if not path.exists(handover_package_folder):
            makedirs(handover_package_folder)
        for handover_package in handover_packages:
            handover_package = handover_packages[handover_package]
            name = handover_package.get('name')
            with open(path.join(directory, 'output', 'handover_packages', '%s.json' % name), 'w') as f:
                f.write(json.dumps(handover_package, indent="\t"))
            del handover_package["worklots"]

        status_columns = ['OPEN', 'FOR APPROVAL', 'CLOSED', 'APPROVED', 'WITHDRAWN']
        handover_packages_table = []
        for handover_package in handover_packages:
            handover_package = handover_packages[handover_package]
            row = [handover_package.get('name')]
            stats = handover_package.get('stats')
            for column in status_columns:
                if stats.get(column) != None:
                    row.append(stats.get(column))
                else:
                    row.append(0)
            handover_packages_table.append(row)
        handover_packages_table = sorted(handover_packages_table, key=lambda x: x[0])

        with open(path.join(directory, 'output', 'handover_packages.json'), 'w') as f:
            f.write(json.dumps(handover_packages_table, indent="\t"))

        design_package_folder = path.join(directory, 'output', 'design_packages')
        if not path.exists(design_package_folder):
            makedirs(design_package_folder)
        for design_package in design_packages:
            design_package = design_packages[design_package]
            name = design_package.get('name')
            with open(path.join(directory, 'output', 'design_packages', '%s.json' % name), 'w') as f:
                f.write(json.dumps(design_package, indent="\t"))
            del design_package["worklots"]

        design_packages_table = []
        for design_package in design_packages:
            design_package = design_packages[design_package]
            row = [design_package.get('name')]
            stats = design_package.get('stats')
            for column in status_columns:
                if stats.get(column) != None:
                    row.append(stats.get(column))
                else:
                    row.append(0)
            design_packages_table.append(row)

        design_packages_table = sorted(design_packages_table, key=lambda x: x[0])

        with open(path.join(directory, 'output', 'design_packages.json'), 'w') as f:
            f.write(json.dumps(design_packages_table, indent="\t"))

    def sync(self):
        self.get_worklot_documents()
        self.get_linked_documents()
        self.extract_packages()
        self.compile_packages()
        self.progress = { "stage": "Done" }
        with open(path.join(directory, 'last_synced.txt'), 'w') as f:
            f.write(datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
