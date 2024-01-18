from os import path
from xer_reader import XerReader
from datetime import datetime
import json
class P6Reader:
    def __init__(self, filepath):
        self.xer = XerReader(filepath).parse_tables()
        self.projects = self.xer.get('PROJECT').entries
        self.project_index = list(map(lambda project: project.get('proj_id'), self.projects))
        self.activities = self.xer.get('TASK').entries
        self.activity_index = list(map(lambda activity: activity.get('task_id'), self.activities))
        self.wbs = self.xer.get('PROJWBS').entries
        self.wbs_index = list(map(lambda wbs: wbs.get('wbs_id'), self.wbs))
        self.resources = self.xer.get('RSRC').entries
        self.resource_index = list(map(lambda resource: resource.get('rsrc_id'), self.resources))
        self.precedents = self.xer.get('TASKPRED').entries
        self.precedent_index = list(map(lambda precedent: precedent.get('task_pred_id'), self.precedents))
        # self.resource_roles = self.xer.get('RSRCROLE')
        # self.calendars = self.xer.get('CALENDAR')
    def convert_date(self, date):
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M")
        dt = dt.timestamp()*1000
        return int(dt)
    def map_precedent(self, precedent):
        if precedent == "PR_SS": return 0
        if precedent == "PR_SF": return 2
        if precedent == "PR_FS": return 1
        if precedent == "PR_FF": return 3
        raise LookupError('Precendent code %s was not configured!' % precedent)
    # def get_precedent(self, index):
    #     precedent = self.precedents.entries[index]
    #     if precedent['proj_id'] != '451413':
    #         return None
    #     pred_task_id = precedent['pred_task_id']
    #     if not pred_task_id in self.activities_task_ids:
    #         return None
    #     task_id = precedent['task_id']
    #     if not task_id in self.activities_task_ids:
    #         return None
    #     pred_task_id = self.activities_task_ids.index(pred_task_id)
    #     task_id = self.activities_task_ids.index(task_id)

    #     return {
    #         "from": self.clean_activities[task_id]['id'],
    #         "to": self.clean_activities[pred_task_id]['id'],
    #         "type": self.map_precedent(precedent.get('pred_type'))
    #     }
    # def get_precedents(self):
    #     precedents = []
    #     for index in range(len(self.precedents.entries)-1):
    #         precedent = self.get_precedent(index)
    #         if precedent == None:
    #             continue
    #         precedents.append(self.get_precedent(index))
    #     return precedents
    # def get_activity(self, index): # change this name
    #     activity = self.activities.entries[index]
    #     # if activity.get('proj_id') != '451413': # HARD CODE TO BE REPLACED
    #     #     return None
    #     resource_id = activity.get('rsrc_id')
    #     if resource_id != '':
    #         if not resource_id in self.used_resources:
    #             index = self.resource_index.index(resource_id)
    #             resource = self.resources.entries[index]
    #             if resource.get('rsrc_id') != resource_id:
    #                 raise LookupError('Getting resource failed!')
    #         self.used_resources.append(resource)
    #     project_id = activity.get('proj_id')
    #     if project_id != '':
    #         if not project_id in self.used_projects:
    #             index = self.pr
        # wbs_id = activity.get('wbs_id')
        # wbs_index = self.project_wbs_ids.index(wbs_id)
        # wb = self.project_wbs.entries[wbs_index]
        # return {
        #     "id": "%s [%s]" % (activity.get('task_name'), activity.get('task_id')),
        #     "task_id": activity.get('task_id'),
        #     "name": activity.get('task_name'),
        #     "start": self.convert_date(activity.get('target_start_date')),
        #     "end": self.convert_date(activity.get('target_end_date')),
        #     "parent": "%s [%s]" % (wb.get('wbs_name'), wb.get('wbs_id')),
        #     # "id": activity.get('task_id'),
        #     # "parent": wbs_id,
        #     "type": "activity"
        # }
    # def get_activites(self, start=None, end=None):
        # activities = []
        # ids = []
        # parent_ids = []
        # for index in range(len(self.activities.entries)-1):
        #     activity = self.get_activity(index)
            # if start != None and end != None:
                # if activity.get('start') < start or activity.get('start') > end:
                #     continue
            # if activity == None:
            #     continue
            # ids.append(activity.get('id'))
            # parent_ids.append(activity.get('parent'))
            # activities.append(activity)
        # for index in range(len(self.project_wbs.entries)-1):
        #     wb = self.get_wbs(index)
        #     if wb == None:
        #         continue
        #     ids.append(wb.get('id'))
        #     parent_ids.append(wb.get('parent'))
        #     activities.append(wb)
        # none_parents = 0
        # clean_activities = []
        # for activity in activities:
        #     # check for children with no parents
        #     parent = activity.get('parent')
        #     # matches = list(filter(lambda id: id == parent, ids)) # this is really inefficient
        #     # if len(matches) < 1 and not activity.get('id') == "RRR - GLU Master Program - v3.3.4 - live program [18096545]": #HARD CODE TO BE REPLACED
        #     if not parent in ids and not activity.get('id') == "RRR - GLU Master Program - v3.3.4 - live program [18096545]": #HARD CODE TO BE REPLACED
        #         continue
        #     # check there is only 1 original ancestor
        #     if parent == None:
        #         none_parents += 1

        #     # check for parents with no children when start and end is None
        #     if activity.get('start') == None or activity.get('end') == None:
        #         id = activity.get('id')
        #         # matches = list(filter(lambda parent_id: parent_id == id, parent_ids)) # this is really inefficient
        #         # if len(matches) < 1:
        #         if not id in parent_ids:
        #             continue # no children
        #     clean_activities.append(activity)
        # print('None parents', none_parents)
        # return clean_activities
    # def get_wbs(self, index):
    #     wb = self.project_wbs.entries[index]
    #     if wb.get('proj_id') != '451413':
    #         return None
    #     # if wb.get('rsrc_id') != '4848084':
    #     #     return None
    #     parent_wbs_id = wb.get('parent_wbs_id')
    #     if not parent_wbs_id in self.project_wbs_ids:
    #         parent = None
    #     else:
    #         parent_wb_index = self.project_wbs_ids.index(parent_wbs_id)
    #         parent_wb = self.project_wbs.entries[parent_wb_index]
    #         parent = "%s [%s]" % (parent_wb.get('wbs_name'), parent_wb.get('wbs_id'))
    #         # parent = parent_wb.get('wbs_id')
    #     return {
    #         "id": "%s [%s]" % (wb.get('wbs_name'), wb.get('wbs_id')),
    #         "task_id": wb.get('wbs_id'),
    #         "name": wb.get('wbs_name'),
    #         "start": None,
    #         "end": None,
    #         "parent": parent,
    #         # "id": wb.get('wbs_id'),
    #         "type": "wbs"
    #     }        
    def get_schedule_data(self):
        used_resources = []
        used_wbs_ids = []
        used_wbs = []
        for activity in self.activities:
            # get used resources
            activity['id'] = activity['task_id']
            activity['target_start_date'] = self.convert_date(activity['target_start_date'])
            activity['target_end_date'] = self.convert_date(activity['target_end_date'])
            activity['name'] = activity['task_name']
            activity['parent'] = activity['wbs_id']
            resource_id = activity['rsrc_id']
            if resource_id == '': continue
            resource_index = self.resource_index.index(resource_id)
            if resource_index == None: continue
            resource = self.resources[resource_index]
            if not 'activities' in resource:
                resource['activities'] = []
            resource['activities'].append(activity)
            # get used wbs
            if not 'wbs_ids' in resource:
                resource['wbs_ids'] = []
            if not 'wbs' in resource:
                resource['wbs'] = []
            wbs_id = activity['wbs_id']
            wbs_node_index = self.wbs_index.index(wbs_id)
            wbs_node = self.wbs[wbs_node_index]
            wbs_node['id'] = wbs_node['wbs_id']
            wbs_node['target_start_date'] = None
            wbs_node['target_end_date'] = None
            wbs_node['name'] = wbs_node['wbs_name']
            wbs_node['parent'] = wbs_node['parent_wbs_id']
            if not wbs_node['parent_wbs_id'] in self.wbs_index:
                wbs_node['parent'] = None
            if not wbs_id in resource['wbs_ids']:
                resource['wbs_ids'].append(wbs_id)
                resource['wbs'].append(wbs_node)
            parent = wbs_node['wbs_id']
            # and any parents
            while parent in self.wbs_index:
                parent_node_index = self.wbs_index.index(parent)
                parent_node = self.wbs[parent_node_index]
                parent_node['id'] = parent_node['wbs_id']
                parent_node['target_start_date'] = None
                parent_node['target_end_date'] = None
                parent_node['name'] = parent_node['wbs_name']
                parent_node['parent'] = parent_node['parent_wbs_id']
                parent = parent_node['parent_wbs_id']
                if not parent in self.wbs_index:
                    parent_node['parent'] = None
                if parent_node['wbs_id'] not in resource['wbs_ids']:
                    resource['wbs_ids'].append(parent_node['wbs_id'])
                    resource['wbs'].append(parent_node)
            
        # def get_wbs_entry_by_id(id):
        #     index = self.wbs_index.index(id)
        #     return self.wbs[index]
        # used_wbs = list(map(get_wbs_entry_by_id, used_wbs_ids))
        resources_with_activities = []
        for resource in self.resources:
            if 'activities' in resource:
                resource['parent'] = None
                resource['activities'] += resource['wbs']
                resources_with_activities.append(resource)
        resources_with_activities_index = list(map(lambda resource: resource.get('rsrc_id'), resources_with_activities))

        # get all projects
        # get 

        # self.clean_activities = self.get_activites()
        # self.activities_ids = list(map(lambda activity: activity.get('id'), self.clean_activities))
        # self.activities_task_ids = list(map(lambda activity: activity.get('task_id'), self.clean_activities))
        # dependencies = self.get_precedents()
                 
        


        return {
            # "activities": self.activities,
            # "activity_index": self.activity_index,
            # "precedents": self.precedents,
            # "precedent_index": self.precedent_index,
            "projects": self.projects,
            "project_index": self.project_index,
            "resources": resources_with_activities,
            "resource_index": resources_with_activities_index,
            # "wbs": self.wbs,
            # "wbs_index": self.wbs_index,
        }
if __name__ == "__main__":
    p6_reader = P6Reader(path.join(path.dirname(__file__), 'data', '231201 GLU Program v2.xer'))
    test_data = p6_reader.get_schedule_data()
    with open(path.join(path.dirname(__file__), 'data', 'output.json'), 'w') as f:
        f.write(json.dumps(test_data, indent='\t'))