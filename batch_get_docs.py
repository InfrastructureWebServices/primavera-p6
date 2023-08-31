from itwocxapi import api
import datetime as datetime
import math

def batch_get_docs(ids, progress):

    doc_list = list(map(lambda id: str(id), ids))
    n = len(doc_list)
    print(n)
    batch_size = 100
    batches =  math.ceil(n/batch_size)
    docs = list()
    for i in range(0, batches):
        print(i+1, 'of', batches)
        start = i*batch_size
        progress["i"] = start
        end = min(n, i*batch_size + batch_size)
        print(start, end)
        request_ids = doc_list[start:end]
        print('requesting', len(request_ids))
        docs_part = api.request_docs(request_ids)
        print('received', len(docs_part))
        docs = [*docs, *docs_part]
    print(n, len(docs), n==len(docs))

    return docs