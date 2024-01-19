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

    def get_schedule_data(self):
        
        # get resources where activities exist
        for activity in self.activities:
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
            if not 'activity_ids' in resource:
                resource['activity_ids'] = []
            resource['activities'].append(activity)
            resource['activity_ids'].append(activity['id'])
            # get wbs as activity
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
            # and any parent wbs
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
        

       
        # apply inheritance
        resource_tree = []
        for resource in self.resources:
            parent = resource['parent_rsrc_id']
            if not parent in self.resource_index or parent == '':
                resource_tree.append(resource)
                parent = None
                resource['parent'] = None
            if parent != None:
                parent_index = self.resource_index.index(parent)
                parent_node = self.resources[parent_index]
                if not 'resources' in parent_node:
                    parent_node['resources'] = []
                parent_node['resources'].append(resource)
                if 'activities' in resource and not 'activities' in parent_node:
                    parent_node['activities'] = []
                    parent_node['activity_ids'] = []
                    parent_node['wbs'] = []
                    parent_node['wbs_ids'] = []
                if 'activities' in resource:
                    for activity_id in resource['activity_ids']:
                        if not activity_id in parent_node['activity_ids']:
                            parent_node['activity_ids'].append(activity_id)
                            activity_index = resource['activity_ids'].index(activity_id)
                            parent_node['activities'].append(resource['activities'][activity_index])
                if 'wbs' in resource:
                    for wbs_id in resource['wbs_ids']:
                        if not wbs_id in parent_node['wbs_ids']:
                            parent_node['wbs_ids'].append(wbs_id)
                            wbs_index = resource['wbs_ids'].index(wbs_id)
                            parent_node['wbs'].append(resource['wbs'][wbs_index])
                
        # combine activites with wbs
        resources_with_activities = []
        for resource in self.resources:
            if 'activities' in resource and 'wbs' in resource:
                resource['activities'] += resource['wbs']
                resources_with_activities.append(resource)
            elif 'wbs' in resource and not 'activities' in resource:
                resource['activities'] = resource['wbs']
        resources_with_activities_index = list(map(lambda resource: resource.get('rsrc_id'), resources_with_activities))


        return {
            # "activities": self.activities,
            # "activity_index": self.activity_index,
            # "precedents": self.precedents,
            # "precedent_index": self.precedent_index,
            "projects": self.projects,
            "project_index": self.project_index,
            "resources": resources_with_activities,
            "resource_index": resources_with_activities_index,
            "resource_tree": resource_tree
            # "wbs": self.wbs,
            # "wbs_index": self.wbs_index,
        }
    

if __name__ == "__main__":
    p6_reader = P6Reader(path.join(path.dirname(__file__), 'data', 'example.xer'))
    test_data = p6_reader.get_schedule_data()
    with open(path.join(path.dirname(__file__), 'data', 'output.json'), 'w') as f:
        f.write(json.dumps(test_data, indent='\t'))
