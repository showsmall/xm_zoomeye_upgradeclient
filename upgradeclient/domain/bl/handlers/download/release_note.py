#! -*- coding: utf-8 -*-


import os
import json
import datetime


from upgradeclient.domain.common.filter import Q, R
from upgradeclient.domain.utils.extstr import ExtStr
from upgradeclient.domain.common.logger import Logger
from upgradeclient.domain.utils.download import Download
from upgradeclient.domain.utils.firmware import Firmware
from upgradeclient.domain.model.event.event import Event
from upgradeclient.domain.model.event.event_type import EventType
from upgradeclient.domain.bl.handlers.download.base import BaseHandler


logger = Logger.get_logger(__name__)


class ReleaseNoteHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(ReleaseNoteHandler, self).__init__(*args, **kwargs)
        self.event_type = EventType.downloading_releasenote
        
    def send_task_cache(self, event):
        json_data = event.to_json()
        relative_path = os.path.join('check_cache', event.get_filename())
        self.cache.write(json_data, relative_path=relative_path)

    def create_event(self, **kwargs):
        kwargs.pop('name')
        event = Event(name=EventType.downloading_firmware, **kwargs)

        return event

    def filter_event(self, q, objs_list):
        event_list = []
        for obj in objs_list:
            obj.filename = ExtStr(obj.filename)
            obj.download_url = ExtStr(obj.download_url)
            res = R(obj, q_ins=q)()
            if res is True:
                event = self.create_event(**dict(obj.__dict__))
                event_list.append(event)
        return event_list

    def analysis_log(self, obj):
        event_list = []
        event_data = obj.get_data()

        filename = obj.get_filename()
        file_url = obj.get_download_url()

        fdirname = os.path.join(self.cache.base_path, 'download_cache')
        filename = os.path.join(fdirname, filename)

        if not event_data:
            fmtdata = (self.__class__.__name__, file_url)
            msgdata = '{0} detected no event data for releasenote, url={1}'.format(*fmtdata)
            self.insert_to_db(obj, log_level='warning', log_message=msgdata)
            logger.warning(msgdata)
            return event_list

        objs_list = map(lambda o: type('obj', (object,), json.loads(o)), obj.get_data())

        dict_data = Firmware.release_note2dict(filename)
        if not dict_data:
            fmtdata = (self.__class__.__name__, file_url)
            msgdata = '{0} parse releasenot use Firmware with exception, url={1}'.format(*fmtdata)
            self.insert_to_db(obj, log_level='error', log_message=msgdata)
            logger.error(msgdata)
            return event_list
        dao_data = self.get_dao_data(obj)
        end_time = datetime.datetime.now()
        sta_time = end_time - datetime.timedelta(seconds=dao_data.get_revision_seconds())
        for key, val in dict_data.iteritems():
            date, flag = key
            sta_date = sta_time.strftime('%Y-%m-%d')
            end_date = end_time.strftime('%Y-%m-%d')
            if date < sta_date or date > end_date:
                fmtdata = (self.__class__.__name__, date, sta_date, end_date, obj.get_download_url())
                msgdata = '{0} delected invalid date-range in releasenote, cur={1} stat={2} end ={3} url={4}'
                logger.warning(msgdata.format(*fmtdata))
                continue

            q = Q(obj__download_url__contains=date) & Q(obj__filename__contains=flag)
            filter_res = self.filter_event(q, objs_list)
            filter_res and val.update({'Date': date})
            map(lambda e: e.set_data(val), filter_res)

            event_list.extend(filter_res)

        return event_list

    def handle(self, obj):
        filename = obj.get_filename()
        file_url = obj.get_download_url()

        tdirname = os.path.join(self.cache.base_path, 'download_cache')
        sdirname = os.path.join(self.cache.base_path, 'check_cache')
        dst_name = os.path.join(tdirname, filename)
        src_name = os.path.join(sdirname, filename)

        download = Download()
        download_res = download.wget(file_url, dst_name)

        if download_res['is_success'] is False:
            fmtdata = (self.__class__.__name__, filename, download_res['error'], file_url)
            msgdata = '{0} download {1} with exception, exp={2} url={3}'.format(*fmtdata)
            self.insert_to_db(obj, log_level='error', log_message=msgdata)
            logger.error(msgdata)
            return

        event_list = self.analysis_log(obj)
        for event in event_list:
            self.send_task_cache(event)

        self.delete(src_name, dst_name)

