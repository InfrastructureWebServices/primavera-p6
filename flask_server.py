# modules
from flask import Flask, request, Response, redirect, send_from_directory, render_template, send_file, jsonify
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

# # django authentication
# from importlib import import_module
# sys.path.insert(0, os.environ.get('IMPORT_DJANGO'))
# import django
# django.setup()
# from django.conf import settings
# from django.contrib.auth.middleware import get_user
# engine = import_module(settings.SESSION_ENGINE)

base_url = "/index/services/rpv/"

# DEBUG = os.environ.get('DEBUG') != None and os.environ.get('DEBUG') == 'true'
# if DEBUG:
#     base_url = ""

# flask app
app = Flask(__name__)

def auth(request):
    # request.session = engine.SessionStore(request.cookies.get(settings.SESSION_COOKIE_NAME))
    # user = get_user(request)
    # user_groups = list(user.groups.values_list('name', flat=True))
    # return (user.is_authenticated and "rpv" in user_groups) or DEBUG
    return True


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/public/<path:path>')
def send_report(path):
    return send_from_directory('public', path)

@app.route('/itwocx')
def dashboard():
    if not auth(request): return render_template('403.html', base_url=base_url)
    if path.exists(path.join(app.root_path, 'last_synced.txt')):
        with open(path.join(app.root_path, 'last_synced.txt')) as f:
            last_synced = f.read()
    else:
        last_synced = 'Never'
    return render_template('dashboard.html', last_synced=last_synced, base_url=base_url)

@app.route('/itwocx/instructions')
def instructions():
    if not auth(request): return render_template('403.html', base_url=base_url)
    return render_template('instructions.html', base_url=base_url)

@app.route('/itwocx/template')
def get_template():
    if not auth(request): return Response(status=403)
    generate_template()
    return send_file(path.join(app.root_path, 'template.xlsx'))

@app.route('/itwocx/download')
def export_worklots_by_pacakges():
    if not auth(request): return Response(status=403)
    return send_file(path.join(app.root_path, 'worklots_by_packages.xlsx'))

@app.route('/itwocx/upload', methods=["POST"])
def import_worklots_by_packages():
    if not auth(request): return render_template('403.html', base_url=base_url)
    if 'file' in request.files:
        save_path = path.join(app.root_path, 'worklots_by_packages.xlsx')
        file = request.files['file']
        file.save(save_path)
        return render_template('message.html', message="Thank you, please return to the dashboard", base_url=base_url)
    else:
        return render_template('message.html', message="Something went wrong!", base_url=base_url)

@app.route('/itwocx/sync')
def sync_worklots():
    if not auth(request): return render_template('403.html', base_url=base_url)
    if sync_queue.unfinished_tasks == 0:
        sync_queue.put(sync)
    return render_template('sync.html', base_url=base_url)

@app.route('/itwocx/handover-packages/', defaults={"code": None, "name": "Handover"})
@app.route('/itwocx/handover-packages/<code>', defaults={"name": "Handover"})
@app.route('/itwocx/design-packages/', defaults={"code": None, "name": "Design"})
@app.route('/itwocx/design-packages/<code>', defaults={"name": "Design"})
def packages(code, name):
    if not auth(request): return render_template('403.html', base_url=base_url)
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

@app.route('/itwocx/design-packages/<code>/prepare-download', defaults={"sub_path": "design_packages"})
@app.route('/itwocx/handover-packages/<code>/prepare-download', defaults={"sub_path": "handover_packages"})
def prepare_download_packages(code, sub_path):
    if not auth(request): return render_template('403.html', base_url=base_url)
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

@app.route('/itwocx/handover-packages/<code>/download')
@app.route('/itwocx/design-packages/<code>/download')
def download_package(code):
    if not auth(request): return render_template('403.html', base_url=base_url)
    directory = path.join(app.root_path, 'output', 'complete')
    filename = "%s.zip" % code
    filepath = path.join(directory, filename)
    if path.exists(path.join(directory, filename)):
        return send_file(filepath)
    else:
        return render_template('404.html', base_url=base_url)

@app.route('/itwocx/cancel')
def cancel():
    if not auth(request): return render_template('403.html', base_url=base_url)
    package = request.args.get('package', None)
    if package == None or not package in package_tasks:
        return render_template('404.html')
    else:
        package_tasks[package].cancel()
        return render_template('message.html', message="Cancelled", base_url=base_url)

@app.route('/itwocx/status')
def get_status():
    if not auth(request): return Response(status=403)
    package = request.args.get('package', None)
    if package != None and package in package_tasks:
        return jsonify(package_tasks[package].progress)
    sync_parameter = request.args.get('sync', None)
    if sync_parameter != None:
        return jsonify(sync.progress)
    return Response(status=403)

@app.route('/p6')
def p6_dashboard():
    if not auth(request): return render_template('403.html', base_url=base_url)
    return render_template('p6-dashboard.html', base_url=base_url)

@app.route('/p6/plan/<plan_id>')
def p6_reader(plan_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    return render_template('p6-viewer.html', plan_id=plan_id, base_url=base_url)

@app.route('/p6/plan/<plan_id>/get')
def get_p6_data(plan_id):
    if not auth(request): return Response(status=403)
    test_data_path = path.join(app.root_path, 'data', 'output.json')
    if False and path.exists(test_data_path):
    # if path.exists(test_data_path) and not DEBUG:
        with open(test_data_path, 'r') as f:
            test_data = json.loads(f.read())
    elif True:
        p6_reader = P6Reader(path.join(app.root_path, 'data', '231201 GLU Program v2.xer'))
        test_data = p6_reader.get_schedule_data()
        with open(test_data_path, 'w') as f:
            f.write(json.dumps(test_data, indent='\t'))
    return jsonify(test_data) 

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
