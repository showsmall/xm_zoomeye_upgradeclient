#! -*- coding: utf-8 -*-

import os
import web
import json
import time
import datetime


from upgradeclient.database.database import db
from upgradeclient.domain.common.helper import Helper
from upgradeclient.domain.utils.webui.config import template_dir, upgwebui_dir


com_render = web.template.render('{0}/'.format(template_dir), base='layout', cache=False)


class BaseView(object):
    """
    'id': ins.id,
    'log_level': ins.log_level,
    'log_name': ins.log_name,
    'log_class': ins.log_class,
    'dao_name': ins.dao_name,
    'file_type': ins.file_type,
    'file_name': ins.file_name,
    'file_url': ins.file_url,
    'last_author': ins.last_author,
    'last_date': ins.last_date,
    'last_revision': ins.last_revision,
    'last_action': ins.last_action,
    'log_message': ins.log_message,
    'created_date': ins.created_time.strftime('%Y-%m-%d'),
    'created_time': ins.created_time.strftime('%H-%M-%S')
    """
    def json_response(self, data):
        web.header('Content-type', 'application/json')

        return json.dumps(data, indent=4)

    def make_time(self, time_fmt, time_str):
        struct_time = time.strptime(time_str, time_fmt)

        return time.mktime(struct_time)

    def GET(self, *args, **kwargs):
        raise NotImplementedError

    def POST(self, *args, **kwargs):
        raise NotImplementedError


class StaticFileView(BaseView):
    def GET(self, media, name):
        file_path = os.path.join(upgwebui_dir, 'statics', media, name)
        if not os.path.exists(file_path):
            web.notfound()

        web.header('Content-type', 'application/octet-stream')
        web.header('Transfer-Encoding', 'chunked')
        web.header('Content-Disposition', 'attachment; filename="{0}"'.format(name))
        try:
            with open(file_path, 'r+b') as fd:
                while True:
                    data = fd.read(262144)
                    if not data:
                        break
                    yield data
        except Exception, e:
            yield e


class RedirectView(BaseView):
    def GET(self, path):
        web.seeother('/{0}'.format(path))


class IndexView(BaseView):
    def GET(self):
        return com_render.index()


class ExceptionThreadView(BaseView):
    def GET(self):
        pass


class ExceptionFmodelView(BaseView):
    def GET(self):
        pass


class ExceptionExceptView(BaseView):
    def GET(self):
        response_data = []

        exp_during = web.input(exp_during='weeks_1')
        split_keys = exp_during.exp_during.split('_')
        response_data = self.dispatch(split_keys[0])(split_keys[-1])

        return self.json_response(response_data)

    def dispatch(self, key):
        handler = {
            'days': self.days_response,
            'weeks': self.week_response,
        }.get(key, self.default_response)

        return handler

    def days_response(self, n):
        response_data = []

        time_fmt = '\'%Y-%m-%d %H:%M\''
        group_con = "strftime({0}, created_time)".format(time_fmt)
        what_con = ','.join(["{0} as date", "count({0}) as count"]).format(group_con)
        n_days_ago = datetime.datetime.now()-datetime.timedelta(days=int(n))
        having_con = "{0} > {1}".format(group_con, n_days_ago.strftime(time_fmt))

        select_command = [
            'select {0} from upgradeclient'.format(what_con),
            'group by {0}'.format(group_con),
            'having {0}'.format(having_con)
        ]

        select_results = db.select(' '.join(select_command))
        if select_results is None:
            return self.json_response([])
        for ins in select_results:
            response_data.append([self.make_time('%Y-%m-%d %H:%M', ins[0]), ins[-1]])
        response_data.sort(key=lambda s: s[0])

        return response_data

    def week_response(self, n):
        response_data = []

        date_fmt = '\'%Y-%m-%d\''
        group_con = "strftime({0}, created_time)".format(date_fmt)
        what_con = ','.join(["{0} as date", "count({0}) as count"]).format(group_con)
        n_week_ago = datetime.datetime.now() - datetime.timedelta(weeks=int(n))
        having_con = "{0} > {1}".format(group_con, n_week_ago.strftime(date_fmt))

        select_command = [
            'select {0} from upgradeclient'.format(what_con),
            'group by {0}'.format(group_con),
            'having {0}'.format(having_con)
        ]

        select_results = db.select(' '.join(select_command))
        if select_results is None:
            return self.json_response([])
        for ins in select_results:
            response_data.append([self.make_time('%Y-%m-%d', ins[0]), ins[-1]])
        response_data.sort(key=lambda s: s[0])

        return response_data

    def default_response(self, n):
        pass


class ExceptionRealtimeView(BaseView):
    def GET(self):
        response_data = []

        loglevels = ['info', 'warning', 'error']
        input_storage = web.input(log_limit=20, log_level='info')
        log_limit = input_storage.log_limit
        log_level = loglevels[loglevels.index(input_storage.log_level):]

        kwargs = zip(['log_level', ]*len(log_level), log_level)

        select_where_condition = ' '.join(Helper.combin_sql_conditions('or', kwargs))

        select_command = [
            'select * from upgradeclient',
            'where {0}'.format(select_where_condition),
            'order by created_time desc',
            'limit {0}'.format(log_limit)
        ]

        select_results = db.select(' '.join(select_command))
        if select_results is None:
            return self.json_response([])
        for ins in select_results:
            created_date, created_time = ins[-1].split()
            response_data.append({
                'id': ins[0],
                'log_level': ins[1],
                'log_message': ins[12],
                'created_date': created_date.strip(),
                'created_time': created_time.strip()
            })
        response_data.sort(key=lambda s: '{0} {1}'.format(s['created_date'], s['created_time']), reverse=True)

        return self.json_response(response_data)


