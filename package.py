# modules
from os import path, makedirs
import json
from shutil import make_archive, rmtree
from uuid import uuid4
import openpyxl as xl

# local modules
from itwocxapi import api
from save_pdf import save_pdf

class Package:
    def __init__(self, package, safe_filename):
        self.package = package
        self.safe_filename = safe_filename
        self.uuid = uuid4().hex
        self.status = 'waiting'
        self.progress = {"stage": "queued"}
    def process(self):
        self.status = 'started'
        try:
            
            wb = xl.Workbook()
            ws = wb.active
            ws.title = 'data upload'
            ws.append(['Reference', 'Id', 'Title', 'Status', 'Handover Package', 'Design Package'])
            
            dirname = path.dirname(__file__)
            output_folder = path.join(dirname, 'output')
            self.download_folder = path.join(output_folder, 'download')
            if path.exists(self.download_folder):
                rmtree(self.download_folder)
            makedirs(self.download_folder)
            self.complete_folder = path.join(output_folder, 'complete')
            if not path.exists(self.complete_folder):
                makedirs(self.complete_folder)
            
            # set up folders
            package_name = self.package.get('name')
            self.package_folder = path.join(self.download_folder, package_name)
            if path.exists(self.package_folder):
                rmtree(self.package_folder)
            makedirs(self.package_folder)
            self.complete_package_folder = path.join(self.complete_folder, package_name)
            if path.exists(self.complete_package_folder):
                rmtree(self.complete_package_folder)
            makedirs(self.complete_package_folder)
            
            worklots = self.package.get('worklots')
            total_worklots = len(worklots)
            worklot_count = 0
            self.progress = {"stage": "processing worklots", "i": worklot_count, "n": total_worklots}
            for worklot in worklots:

                # unpack worklot
                handover_package = worklot.get('HP')
                design_pacakge = worklot.get('DP')
                document = worklot.get('document')
                id = document.get('Id')
                title = document.get('Title')
                status = document.get('StatusName')
                reference = document.get('Reference')
                doc_code = document.get('DocCode')
                ws.append([reference, id, title, status, handover_package, design_pacakge])
                        
                # clean up folder space
                folder_name = '%s - %s' % (str(id), reference)
                folder_name = self.safe_filename(folder_name)
                worklot_folder = path.join(self.package_folder, folder_name)
                if path.exists(worklot_folder):
                    rmtree(worklot_folder)
                makedirs(worklot_folder)

                
                # prepare file paths and folder
                doc_code_folder = path.join(worklot_folder, doc_code)
                if not path.exists(doc_code_folder):
                    makedirs(doc_code_folder)
                filename = '%s - %s.pdf' % (str(id), reference)
                filename = self.safe_filename(filename)
                filepath = path.join(worklot_folder, doc_code, filename)

                # download pdf and save
                response = api.request_doc_as_pdf(id)
                linked_documents = document.get('LinkedDocuments')
                save_pdf(response, filepath, linked_documents)

                # attachments
                attachments_folder = path.join(worklot_folder,'Attachments')
                makedirs(attachments_folder)
                attachments = document.get('Attachments')
                for attachment in attachments:
                    attachment_id = attachment.get('Id')
                    format = attachment.get('Format')
                    format = format.lower()
                    filename = '%s.%s' % (attachment_id, format)
                    filename = self.safe_filename(filename)
                    filepath = path.join(attachments_folder, filename)
                    response = api.request_attachment(attachment_id)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                
                # linked documents
                if linked_documents != None:
                    for linked_document in linked_documents:
                        linked_id = linked_document.get('DocumentId')

                        # unpack linked document
                        document = linked_document.get('document')
                        id = document.get('Id')
                        reference = document.get('Reference')
                        doc_code = document.get('DocCode')
                        linked_linked_documents = document.get('LinkedDocuments')
                        
                        # prepare file paths and folder
                        doc_code_folder = path.join(worklot_folder, doc_code)
                        if not path.exists(doc_code_folder):
                            makedirs(doc_code_folder)
                        filename = '%s - %s.pdf' % (str(id), reference)
                        filename = self.safe_filename(filename)
                        filepath = path.join(worklot_folder, doc_code, filename)
                        
                        # download pdf and save
                        response = api.request_doc_as_pdf(linked_id)
                        save_pdf(response, filepath, linked_linked_documents)

                        # attachments
                        attachments = document.get('Attachments')
                        for attachment in attachments:
                            attachment_id = attachment.get('Id')
                            format = attachment.get('Format')
                            format = format.lower()
                            filename = '%s.%s' % (attachment_id, format)
                            filepath = path.join(attachments_folder, filename)
                            response = api.request_attachment(attachment_id)
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                
                # zip up worklot
                make_archive(path.join(self.complete_package_folder, folder_name), 'zip', worklot_folder)

                # return progress
                worklot_count += 1
                self.progress = {"stage": "processing worklots", "i": worklot_count, "n": total_worklots}

            # zip up folder
            self.progress = {"stage": "creating zip" }
            wb.save(path.join(self.complete_folder, package_name, 'worklots.xlsx'))
            wb.close()
            make_archive(path.join(self.complete_folder, package_name), 'zip', self.complete_package_folder)
            self.clean()
        except:
            self.progress = {"stage": "error" }
            self.status = 'error'
    def cancel(self):
            self.status == 'cancelling'
            self.progress = {"stage": "cancelling" }
            self.clean()
    def cancel_signal_received(self):
        if self.status == 'cancelling':
            return True
        else:
            return False
    def clean(self):
        rmtree(self.complete_package_folder)
        rmtree(self.package_folder)
        if self.status == 'cancelling':
            self.progress = {"stage": "cancelled" }
            self.status = 'cancelled'
        else:
            self.progress = {"stage": "ready for download" }
            self.status = 'success'
        