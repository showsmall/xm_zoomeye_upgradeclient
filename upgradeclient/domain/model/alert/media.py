#! -*- coding: utf-8 *-


import json


class Media(object):
    def __init__(self, relation_name=None, relation_type=None, to=None, cc=None):
        self.to = to
        self.cc = cc
        self.relation_name = relation_name
        self.relation_type = relation_type

    def get_relation_name(self):
        return self.relation_name

    def set_relation_name(self, relation_name):
        self.relation_name = relation_name

    def get_relation_type(self):
        return self.relation_type

    def set_relation_type(self, relation_type):
        self.relation_type = relation_type

    def get_to(self):
        return self.to

    def set_to(self, to):
        self.to = to

    def get_cc(self):
        return self.cc

    def set_cc(self, cc):
        self.cc = cc

    def to_dict(self):
        dict_data = {
            'to': self.get_to(),
            'cc': self.get_cc(),
            'relation_name': self.get_relation_name(),
            'relation_type': self.get_relation_type()
        }

        return dict_data

    def to_json(self):
        dict_data = self.to_dict()
        json_data = json.dumps(dict_data)

        return json_data

    @staticmethod
    def from_json(json_data):
        dict_data = json.loads(json_data)

        to = dict_data.get('to', None)
        cc = dict_data.get('cc', None)
        relation_name = dict_data.get('relation_name', None)
        relation_type = dict_data.get('relation_type', None)

        media = Media(relation_name=relation_name, relation_type=relation_type, to=to, cc=cc)

        return media
