import requests
import json
from datetime import datetime
from os import path
import urllib.parse
dir = path.dirname(__file__)
api_version = "23.12"
project = "GLU-VCA"

def get_cookies():
    with open(path.join(dir, "..", 'cookie.txt')) as f:
        cookies = f.read()
        f.close()
    return cookies

def get_json_headers():
    headers = {
        "Host": "au.itwocx.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Origin": "https://au.itwocx.com",
        "Referer": "https://au.itwocx.com/api/"+api_version+"/api/help/index",
        "Cookie": get_cookies(),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    return headers

def get_api_request_url(data): 
    url = "https://au.itwocx.com/api/%s/Api/Login/GetUrl" % api_version # initial value of api version
    headers = get_json_headers()
    r = requests.post(url=url, headers=headers, json=data)
      
    try:
        return r.text
    except:
        on_error(r.text)

def encrypt_password(data): 
    url = "https://au.itwocx.com/api/"+api_version+"/Api/Login/EncryptPassword"
    headers = get_json_headers()
    
    r = requests.post(url=url, headers=headers, json=data)
        
    try:
        return r.text
    except:
        on_error(r.text)

def login(data): 
    url = "https://au.itwocx.com/api/"+api_version+"/Api/Login/ByEmail"
    headers = get_json_headers()
    
    r = requests.post(url=url, headers=headers, json=data)
        
    try:
        return r.text
    except:
        on_error(r.text)

def update_doc(data): 
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/Update?sendNotification=false"
    headers = get_json_headers()
    
    r = requests.put(url=url, headers=headers, json=data)
    # test
    # with open("output/document.json", "w", encoding="utf-8") as f:
    #     f.write(r.text)
        
    try:
        return json.loads(r.text)
    except:
        on_error(r.text)

def create_doc(data): 
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/Create?sendNotification=false"
    headers = get_json_headers()
    
    r = requests.post(url=url, headers=headers, json=data)
    # test
    # with open("output/document.json", "w", encoding="utf-8") as f:
    #     f.write(r.text)
        
    try:
        return json.loads(r.text)
    except:
        on_error(r.text)



def request_doc(id):
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/GetById/" + str(id) + "?includeComments=true"
    headers = get_json_headers()

    r = requests.get(url=url, headers=headers)
    # test
    # with open("output/document.json", "w", encoding="utf-8") as f:
    #     f.write(r.text)
        
    try:
        return json.loads(r.text)
    except:
        on_error(r.text)

def request_docs(ids):
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/GetByIds?includeComments=false&includeUserFields=false"
    ids_params = urllib.parse.urlencode({"ids": ids}, doseq=True)
    url = "%s&%s" % (url, ids_params)
    headers = get_json_headers()

    r = requests.get(url=url, headers=headers)

    try:
        return json.loads(r.text)
    except:
        on_error(r.text)

def request_doc_as_pdf(id):
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/GetDocumentAsPdf/" + str(id) + "?includeComments=true&showHistory=true"
    headers = get_json_headers()

    r = requests.get(url=url, headers=headers)
    
    return r
    

def request_doc_list(options):
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/Document/Search"
    headers = get_json_headers()
    headers["Content-Type"] = "application/json"

    r = requests.post(url=url, headers=headers, json=options)

    try:
        return json.loads(r.text)
    except:
        on_error(r.text)

def request_attachment(id):
    url = "https://au.itwocx.com/api/"+api_version+"/Api/GLU-VCA/Attachment/DownloadFile/" + str(id)
    headers = get_json_headers()

    r = requests.get(url=url, headers=headers)
    # test
    # with open("output/document.json", "w", encoding="utf-8") as f:
    #     f.write(r.text)
        
    try:
        return r
    except:
        on_error(r.text)

def get_user(code): 
    url = "https://au.itwocx.com/api/"+api_version+"/Api/"+project+"/User/GetByCode?code=" + code
    headers = get_json_headers()

    r = requests.get(url=url, headers=headers)
    # with open("output/document_id_list.json", "w") as f:
    #     f.write(r.text)
    try:
        return json.loads(r.text)
    except:
        on_error(r.text)


def ticks(dt):
    return int((dt - datetime(1, 1, 1)).total_seconds() * 10000000)

def on_error(text):
    with open(path.join(dir, "..", 'output/errors.html'), 'w') as f:
        f.write(text)
        f.close()
    print('Script finalised with errors!')