from os import path
from xer_reader import XerReader
from datetime import datetime
import json
class P6Reader:
    def __init__(self, filepath):
        self.xer = XerReader(filepath).parse_tables()
        self.activities = self.xer.get('TASK')
        self.calendars = self.xer.get('CALENDAR')
        self.project_wbs = self.xer.get('PROJWBS')
        self.resources = self.xer.get('RSRC')
        self.resource_roles = self.xer.get('RSRCROLE')
        self.precedents = self.xer.get('TASKPRED')
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
    def get_precedent(self, index):
        precedent = self.precedents.entries[index]
        return {
            "from": precedent.get('pred_task_id'),
            "to": precedent.get('task_id'),
            "type": self.map_precedent(precedent.get('pred_type'))
        }
    def get_precedents(self, activity_ids):
        precedents = []
        # for index in range(len(self.precedents.entries)-1):
        #     precedent = self.get_precedent(index)
        #     if not precedent.get('from') in activity_ids or not precedent.get('to') in activity_ids:
        #         continue
        #     precedents.append(self.get_precedent(index))
        return precedents
    def get_activity(self, index):
        activity = self.activities.entries[index]
        if activity.get('proj_id') != '451413': # HARD CODE TO BE REPLACED
            return None
        wbs_id = activity.get('wbs_id')
        wbs_index = self.project_wbs_ids.index(wbs_id)
        wb = self.project_wbs.entries[wbs_index]
        return {
            "id": "%s [%s]" % (activity.get('task_name'), activity.get('task_id')),
            "name": activity.get('task_name'),
            "start": self.convert_date(activity.get('target_start_date')),
            "end": self.convert_date(activity.get('target_end_date')),
            "parent": "%s [%s]" % (wb.get('wbs_name'), wb.get('wbs_id')),
            "type": "activity"
        }
    def get_activites(self, start=None, end=None):
        activities = []
        ids = []
        parent_ids = []
        for index in range(len(self.activities.entries)-1):
            activity = self.get_activity(index)
            # if start != None and end != None:
                # if activity.get('start') < start or activity.get('start') > end:
                #     continue
            if activity == None:
                continue
            ids.append(activity.get('id'))
            parent_ids.append(activity.get('parent'))
            activities.append(activity)
        for index in range(len(self.project_wbs.entries)-1):
            wb = self.get_wbs(index)
            if wb == None:
                continue
            ids.append(wb.get('id'))
            parent_ids.append(wb.get('parent'))
            activities.append(wb)
        none_parents = 0
        clean_activities = []
        for activity in activities:
            # check for children with no parents
            parent = activity.get('parent')
            # matches = list(filter(lambda id: id == parent, ids)) # this is really inefficient
            # if len(matches) < 1 and not activity.get('id') == "RRR - GLU Master Program - v3.3.4 - live program [18096545]": #HARD CODE TO BE REPLACED
            if not parent in ids and not activity.get('id') == "RRR - GLU Master Program - v3.3.4 - live program [18096545]": #HARD CODE TO BE REPLACED
                continue
            # check there is only 1 original ancestor
            if parent == None:
                none_parents += 1

            # check for parents with no children when start and end is None
            if activity.get('start') == None or activity.get('end') == None:
                id = activity.get('id')
                # matches = list(filter(lambda parent_id: parent_id == id, parent_ids)) # this is really inefficient
                # if len(matches) < 1:
                if not id in parent_ids:
                    continue # no children
            clean_activities.append(activity)
        print('None parents', none_parents)
        return clean_activities
    def get_wbs(self, index):
        wb = self.project_wbs.entries[index]
        if wb.get('proj_id') != '451413':
            return None
        parent_wbs_id = wb.get('parent_wbs_id')
        if not parent_wbs_id in self.project_wbs_ids:
            parent = None
        else:
            parent_wb_index = self.project_wbs_ids.index(parent_wbs_id)
            parent_wb = self.project_wbs.entries[parent_wb_index]
            parent = "%s [%s]" % (parent_wb.get('wbs_name'), parent_wb.get('wbs_id'))
        return {
            "id": "%s [%s]" % (wb.get('wbs_name'), wb.get('wbs_id')),
            "name": wb.get('wbs_name'),
            "start": None,
            "end": None,
            "parent": parent,
            "type": "wbs"
        }        
    # def map_to_wbs(self):
    #     wbs = {}
    #     for wb in self.project_wbs.entries:
    #         wbs[wb.get('wbs_id')] = wb
    #     # activities = {}
    #     for activity in self.activities.entries:
    #         task_id = activity.get('task_id')
    #         wbs_id = activity.get('wbs_id')
    #         if not wbs_id in wbs:
    #             raise LookupError('Missing %s from WBS!' % wbs_id)
    #         wb = wbs[wbs_id]
    #         if not 'activities' in wb:
    #             wb['activities'] = []
    #         wb['activities'].append(activity)
    #     for wb in wbs:
    #         wb = wbs[wb]
    #         parent_wbs_id = wb.get('parent_wbs_id')
    #         if not parent_wbs_id in wbs:
    #             if parent_wbs_id == '10962001': 
    #                 wb['parent_wbs_id'] = None
    #                 break
    #             raise LookupError('Missing %s from WBS!' % parent_wbs_id)
    #         parent_wb = wbs.get(parent_wbs_id)
    #         if not 'activities' in parent_wb:
    #             parent_wb['activities'] = []
    #         parent_wb['activities'].append(wb)
    #         # activities[activity.get('task_id')] = activity
    #     print('ok')
    def get_schedule_data(self):
        wbs = self.project_wbs.entries
        self.project_wbs_ids = list(map(lambda wb: wb.get('wbs_id'), wbs))
        activities = self.get_activites()
        self.activities_ids = list(map(lambda activity: activity.get('task_id'), activities))
        return {
            "activities": {
                "data": activities,
                "start": "start",
                "end": "end",
                "name": "name",
                "parent": "parent"
            },
            "resources": {
                "data": [],
                "parent": "parent",
                "name": "name",
                "id": "id"
            },
            "constraints": {
                "data": [],
                "from": "from",
                "to": "to",
                "type": "type"
            },
            "reservations": {
                "data": [],
                "activity": "activity",
                "resource": "resource"
            },
        }