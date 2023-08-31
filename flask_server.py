# modules
from flask import Flask, request, Response, redirect, send_from_directory, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from time import sleep
import threading
import queue
import sys
import os
from os import path
import json
import re

# local modules
from package import Package
from sync_worklots import Sync
sync = Sync()
from template import generate_template
from p6_reader import P6Reader

# django authentication
from importlib import import_module
sys.path.insert(0, os.environ.get('IMPORT_DJANGO'))
import django
django.setup()
from django.conf import settings
from django.contrib.auth.middleware import get_user
engine = import_module(settings.SESSION_ENGINE)

base_url = "/index/services/rpv/"

# flask app
app = Flask(__name__)

@app.before_request
def auth():
    request.session = engine.SessionStore(request.cookies.get(settings.SESSION_COOKIE_NAME))
    user = get_user(request)
    if not user.is_authenticated:
        return redirect('/index/signin')



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/public/<path:path>')
def send_report(path):
    return send_from_directory('public', path)

@app.route('/')
def dashboard():
    if path.exists(path.join(app.root_path, 'last_synced.txt')):
        with open(path.join(app.root_path, 'last_synced.txt')) as f:
            last_synced = f.read()
    else:
        last_synced = 'Never'
    return render_template('dashboard.html', last_synced=last_synced, base_url=base_url)

@app.route('/instructions')
def instructions():
    return render_template('instructions.html', base_url=base_url)

@app.route('/template')
def get_template():
    generate_template()
    return send_file(path.join(app.root_path, 'template.xlsx'))

@app.route('/download')
def export_worklots_by_pacakges():
    return send_file(path.join(app.root_path, 'worklots_by_packages.xlsx'))

@app.route('/upload', methods=["POST"])
def import_worklots_by_packages():
    if 'file' in request.files:
        save_path = path.join(app.root_path, 'worklots_by_packages.xlsx')
        file = request.files['file']
        file.save(save_path)
        return render_template('message.html', message="Thank you, please return to the dashboard", base_url=base_url)
    else:
        return render_template('message.html', message="Something went wrong!", base_url=base_url)

@app.route('/sync')
def sync_worklots():
    if sync_queue.unfinished_tasks == 0:
        sync_queue.put(sync)
    return render_template('sync.html', base_url=base_url)

@app.route('/handover-packages/', defaults={"code": None, "name": "Handover"})
@app.route('/handover-packages/<code>', defaults={"name": "Handover"})
@app.route('/design-packages/', defaults={"code": None, "name": "Design"})
@app.route('/design-packages/<code>', defaults={"name": "Design"})
def packages(code, name):
    if code == None:
        headers = [
            ['%s Package' % name, 'Open', 'For Approval', 'Closed', 'Approved', 'Withdrawn']
        ]
        with open(path.join(app.root_path, 'output', '%s_packages.json' % name.lower()), 'r') as f:
            data = json.loads(f.read())
        return render_template('package-table.html', name=name, headers=headers, data=data, base_url=base_url)
    else:
        filepath = path.join(app.root_path, 'output', '%s_packages' % name.lower(), "%s.json" % code)
        if path.exists(filepath):
            with open(filepath, 'r') as f:
                package = json.loads(f.read())
            return render_template('package-contents.html', package=package, base_url=base_url)
        else:
            return render_template('404.html', base_url=base_url)

@app.route('/design-packages/<code>/prepare-download', defaults={"sub_path": "design_packages"})
@app.route('/handover-packages/<code>/prepare-download', defaults={"sub_path": "handover_packages"})
def prepare_download_packages(code, sub_path):
    filepath = path.join(app.root_path, 'output', sub_path, "%s.json" % code)
    if path.exists(filepath):
        with open(filepath, 'r') as f:
            package = json.loads(f.read())
        package = Package(package, safe_filename)
        package_tasks[package.uuid] = package
        packaging_queue.put(package)
        return render_template('download-package.html', package=package, base_url=base_url)
    else:
        return render_template('404.html', base_url=base_url)

@app.route('/handover-packages/<code>/download')
@app.route('/design-packages/<code>/download')
def download_package(code):
    directory = path.join(app.root_path, 'output', 'complete')
    filename = "%s.zip" % code
    filepath = path.join(directory, filename)
    if path.exists(path.join(directory, filename)):
        return send_file(filepath)
    else:
        return render_template('404.html', base_url=base_url)

@app.route('/cancel')
def cancel():
    package = request.args.get('package', None)
    if package == None or not package in package_tasks:
        return render_template('404.html')
    else:
        package_tasks[package].cancel()
        return render_template('message.html', message="Cancelled", base_url=base_url)

@app.route('/status')
def get_status():
    package = request.args.get('package', None)
    if package != None and package in package_tasks:
        return jsonify(package_tasks[package].progress)
    sync_parameter = request.args.get('sync', None)
    if sync_parameter != None:
        return jsonify(sync.progress)
    return Response(status=403)

@app.route('/p6/get-data')
def get_p6_data():
    test_data_path = path.join(app.root_path, 'data', 'test.json')
    if path.exists(test_data_path):
        with open(test_data_path, 'r') as f:
            test_data = json.loads(f.read())
    else:
        p6_reader = P6Reader(path.join(app.root_path, 'data', 'example.xer'))
        test_data = p6_reader.get_schedule_data()
        with open(test_data_path, 'w') as f:
            json.dumps(test_data, index='\t')
    return jsonify(test_data) 

@app.route('/p6/')
def p6_reader():
    return render_template('p6.html', base_url=base_url)

# helper functions
def format_sse(data: str, event=None) -> str:
    message = f'data: {data}\n\n'
    if event is not None:
        message = f'event: {event}\n{message}'
    return message

def safe_filename(filename): # needs to be valid name for windows OS
    filename = re.sub(r"[<>:\"\/\\|?*\n\r\t]","", filename)
    return filename

# workers
package_tasks = {}
packaging_queue = queue.Queue()
def package_process_worker():
    while True:
        package = packaging_queue.get()
        uuid = package.uuid
        package_tasks[uuid].process()
        while uuid in package_tasks and not (package_tasks[uuid].status == 'success' or not package_tasks[uuid].status == 'cancelled'):
            sleep(1)
        packaging_queue.task_done()

threading.Thread(target=package_process_worker, daemon=True).start()

# workers
sync_queue = queue.Queue(maxsize=1)
def sync_process_worker():
    while True:
        sync = sync_queue.get()
        sync.sync()
        sync_queue.task_done()

threading.Thread(target=sync_process_worker, daemon=True).start()
