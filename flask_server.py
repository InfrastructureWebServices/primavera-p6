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
import xml.etree.ElementTree as ET

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

base_url = "/private/rpv/"


# flask app
app = Flask(__name__)

DEBUG = os.environ.get('DEBUG') != None and os.environ.get('DEBUG') == 'true'
if DEBUG:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    base_url = "/"

def auth(request):
    request.session = engine.SessionStore(request.cookies.get(settings.SESSION_COOKIE_NAME))
    user = get_user(request)
    user_groups = list(user.groups.values_list('name', flat=True))
    return ((user.is_authenticated and "rpv" in user_groups) or DEBUG)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/public/<path:path>')
def send_report(path):
    return send_from_directory('public', path)

def sync_plans_data():
    with open(os.path.join(app.root_path, 'plans.json'), 'r') as f:
        plans = json.loads(f.read())
    return plans

def save_plans_data(plans):
    with open(os.path.join(app.root_path, 'plans.json'), 'w') as f:
        f.write(json.dumps(plans, indent="\t"))

@app.route('/p6')
def p6_dashboard():
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    return render_template('p6-dashboard.html', base_url=base_url, plans=plans)

@app.route('/p6/plan/<int:plan_id>')
def p6_plan_list(plan_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.json" % plan['id'])
        if path.exists(plan_data_path):
            with open(plan_data_path, 'r') as f:
                plan = json.loads(f.read())
            return render_template('p6-project-list.html', plan_id=plan_id, plan=plan, base_url=base_url)
    return render_template('403.html', base_url=base_url) # send a message that there are no resources

def render_resource_tree(resource_tree, project_id):
    def recurse(parent_node, route):
        ul = ET.Element('ul', { 'class': 'collapsible popout'})
        node_index = 0
        for child_node in parent_node['resources']:
            if len(route) == 0:
                branch = "%s" % (node_index)
            else:
                branch = "%s,%s" % (route, node_index)
            li = ET.Element('li')
            href = "./%s/view?route=%s" % (project_id, branch)
            header = ET.Element('div', { 'class': 'collapsible-header'})
            if 'activity_ids' in child_node or 'wbs_ids' in child_node:
                anchor = ET.Element('a', { 'href': href})
                anchor.text = child_node['rsrc_name']
                header.append(anchor)
            else:
                p = ET.Element('p')
                p.text = child_node['rsrc_name']
                header.append(p)
            if 'resources' in child_node:
                body = ET.Element('div', { 'class': 'collapsible-body'})
                child_ul = recurse(child_node, branch)
                body.append(child_ul)
                li.append(header)
                li.append(body)
            else:
                li.append(header)
            ul.append(li)
            node_index += 1
        return ul
    ul = recurse(resource_tree, '')
    resource_list = ET.tostring(ul, 'unicode')
    return resource_list
            

@app.route('/p6/plan/<int:plan_id>/project/<project_id>')
def p6_project_list(plan_id, project_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.json" % plan['id'])
        if path.exists(plan_data_path):
            with open(plan_data_path, 'r') as f:
                plan = json.loads(f.read())
            if project_id in plan['project_index']:
                project = plan['projects'][plan['project_index'].index(project_id)]
                # resource_tree = {'resources': plan['resource_tree']}
                resource_tree = render_resource_tree(plan, project_id)
                return render_template('p6-project.html', plan_id=plan_id, project_id=project_id, project=project, resource_tree=resource_tree, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/activity-code-types')
def p6_activity_types(plan_id, project_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.xer" % plan['id'])
        if path.exists(plan_data_path):
            plan = P6Reader(plan_data_path)
            activity_types = plan.get_activity_types(project_id)
            return render_template('p6-activity-code-types.html', plan_id=plan_id, project_id=project_id, activity_types=activity_types, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/activity-code-type/<activity_code_type_id>')
def p6_activity_codes(plan_id, project_id, activity_code_type_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.xer" % plan['id'])
        if path.exists(plan_data_path):
            plan = P6Reader(plan_data_path)
            activity_code_type = plan.get_activity_code_type(activity_code_type_id)
            activity_codes = plan.get_activity_codes(activity_code_type_id)
            return render_template('p6-activity-codes.html', plan_id=plan_id, project_id=project_id, activity_code_type=activity_code_type, activity_codes=activity_codes, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/activity-code/<activity_code_id>')
def p6_activity_code(plan_id, project_id, activity_code_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.xer" % plan['id'])
        if path.exists(plan_data_path):
            plan = P6Reader(plan_data_path)
            activity_code = plan.get_activity_code(activity_code_id)
            activity_code_tasks = plan.get_activity_code_tasks(activity_code_id)
            return render_template('p6-activity-code.html', plan_id=plan_id, project_id=project_id, activity_code=activity_code, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/activity-code/<activity_code_id>/gantt-chart')
def p6_activity_code_gantt_chart(plan_id, project_id, activity_code_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.xer" % plan['id'])
        if path.exists(plan_data_path):
            plan = P6Reader(plan_data_path)
            activity_code = plan.get_activity_code(activity_code_id)
            activity_code_tasks = plan.get_activity_code_tasks(activity_code_id)
            return render_template('p6-viewer.html', plan_id=plan_id, project_id=project_id, activity_code_id=activity_code_id, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/task/<task_id>')
def p6_task(plan_id, project_id, task_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    plans = sync_plans_data()
    plan_ids = list(map(lambda o: o['id'], plans))
    if plan_id in plan_ids:
        plan_index = plan_ids.index(plan_id)
        plan = plans[plan_index]
        plan_data_path = path.join(app.root_path, 'data', "%s.xer" % plan['id'])
        if path.exists(plan_data_path):
            plan = P6Reader(plan_data_path)
            task = plan.get_task(task_id)
            return render_template('p6-task.html', plan_id=plan_id, project_id=project_id, task=task, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/view')
def p6_resource_reader(plan_id, project_id):
    if not auth(request): return render_template('403.html', base_url=base_url)
    route = request.args.get('route')
    if route:
        plans = sync_plans_data()
        plan_ids = list(map(lambda o: o['id'], plans))
        if plan_id in plan_ids:
            plan_index = plan_ids.index(plan_id)
            plan = plans[plan_index]
            plan_data_path = path.join(app.root_path, 'data', "%s.json" % plan['id'])
            if path.exists(plan_data_path):
                with open(plan_data_path, 'r') as f:
                    plan = json.loads(f.read())
                    activities = plan['activities']
                    activity_index = plan['activity_index']
                    wbs = plan['wbs']
                    wbs_index = plan['wbs_index']
                if project_id in plan['project_index']:
                    project = plan['projects'][plan['project_index'].index(project_id)] # needs a better handling
                    route_array = list(map(lambda r: int(r), route.split(',')))
                    resource = plan
                    for step in route_array:
                        resource = resource['resources'][step]
                    resource['activities'] = []
                    for activity_id in resource['activity_ids']:
                        activity = activities[activity_index.index(activity_id)]
                        resource['activities'].append(activity)
                    for wbs_id in resource['wbs_ids']:
                        wb = wbs[wbs_index.index(wbs_id)]
                        resource['activities'].append(wb)
                    resource_id = resource['rsrc_id']
                    return render_template('p6-viewer.html', plan_id=plan_id, project_id=project_id, route=route, base_url=base_url)
    return render_template('403.html', base_url=base_url)

@app.route('/p6/plan/<int:plan_id>/project/<project_id>/get')
def get_p6_data(plan_id, project_id):
    if not auth(request): return Response(status=403)
    route = request.args.get('route')
    if route:
        plans = sync_plans_data()
        plan_ids = list(map(lambda o: o['id'], plans))
        if plan_id in plan_ids:
            plan_index = plan_ids.index(plan_id)
            plan = plans[plan_index]
            plan_data_path = path.join(app.root_path, 'data', "%s.json" % plan['id'])
            if path.exists(plan_data_path):
                with open(plan_data_path, 'r') as f:
                    plan = json.loads(f.read())
                    activities = plan['activities']
                    activity_index = plan['activity_index']
                    wbs = plan['wbs']
                    wbs_index = plan['wbs_index']
                if project_id in plan['project_index']:
                    project = plan['projects'][plan['project_index'].index(project_id)] # needs a better handling
                    route_array = list(map(lambda r: int(r), route.split(',')))
                    resource = plan
                    for step in route_array:
                        resource = resource['resources'][step]
                    resource['activities'] = []
                    resource['parent'] = None
                    for activity_id in resource['activity_ids']:
                        activity = activities[activity_index.index(activity_id)]
                        resource['activities'].append(activity)
                    for wbs_id in resource['wbs_ids']:
                        wb = wbs[wbs_index.index(wbs_id)]
                        resource['activities'].append(wb)
                    if 'resources' in resource: del resource['resources']
                    if 'activity_ids' in resource: del resource['activity_ids']
                    if 'wbs_ids' in resource: del resource['wbs_ids']
                    return jsonify(resource)
    if not auth(request): return Response(status=400)

@app.route('/p6/plan/upload', methods=['GET', 'POST'])
def upload_new_plan():
    if not auth(request): return render_template('403.html', base_url=base_url)
    if request.method == 'POST':
        if 'file' in request.files:
            plans = sync_plans_data()
            plan_ids = list(map(lambda o: int(o['id']), plans))
            if len(plan_ids) > 0:
                next_id = max(plan_ids) + 1
            else:
                next_id = 1
            project_path = path.join(app.root_path, 'data', '%s.xer' % next_id)
            processed_data_path = path.join(app.root_path, 'data', '%s.json' % next_id)
            name = request.form['project_name']
            user = get_user(request)
            user_id = user.id
            plans.append({"id": next_id, "name": name, "created_by": user_id })
            save_plans_data(plans)
            file = request.files['file']
            file.save(project_path)
            p6_reader = P6Reader(project_path)
            processed_data = p6_reader.get_schedule_data()
            with open(processed_data_path, 'w') as f:
                f.write(json.dumps(processed_data, indent='\t'))
            return render_template('message.html', message="Thank you, your plan has been uploaded", next="p6", base_url=base_url)
        else:
            return render_template('message.html', message="Something went wrong!", base_url=base_url)
    else:
        return render_template('upload-plan.html', base_url=base_url)
