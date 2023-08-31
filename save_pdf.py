import json
from os import path
import base64
import io
import PyPDF2
from urllib.parse import urlparse, parse_qs

def get_query_params(url):
    return parse_qs(urlparse(url).query)

def save_pdf(response, filepath, linked_documents):
    data = json.loads(response.content)
    data = data.get('Content').encode('ascii')
    pdf_bytes = base64.decodebytes(data)
    pdf_stream = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_stream)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        if "/Annots" in page:
            for annot in page["/Annots"]:
                obj = annot.get_object()
                if '/A' not in obj: continue  # not a link
                key = PyPDF2.generic.TextStringObject("/URI")
                current_link = obj['/A'][key]
                linked_to_worklot = True
                params = get_query_params(current_link)
                if len(params) == 0: continue
                if params.get('page')[0] != None:
                    if params.get('page')[0] == "docs/docdet0":
                        doc_type = params.get('t')[0]
                        id = params.get('i')[0]
                        found = False
                        if doc_type == "AP":
                            for linked_document in linked_documents:
                                if linked_document.get('DocumentId') == int(id):
                                    found = True
                                    if linked_document.get('document') != None:
                                        doc_type = linked_document.get('document').get('DocCode')
                                        reference = linked_document.get('document').get('Reference')
                                    else: 
                                        linked_to_worklot = False
                                    break
                            if not found:
                                raise LookupError('Could not find document code!')
                        if found and linked_to_worklot:
                            new_link = "../%s/%s - %s.pdf" % (doc_type, id, reference)
                        else:
                            new_link = "#"
                    elif params.get('page')[0] == "DOCS/GODOWNLOAD":
                        log_id = params.get('logId')[0]
                        file_type = params.get('s')[0]
                        file_type = file_type.lower()
                        new_link = "../attachments/%s%s" % (log_id, file_type)
                    else:
                        raise LookupError('Unexpected page value %s!' % params.get('page')[0])
                obj['/A'][key] = PyPDF2.generic.TextStringObject(new_link)
        writer.add_page(page)
    with open(filepath, 'wb') as f:
        writer.write(f)