#! -*- coding: utf-8 -*-


import os
import time


from threading import Thread
from upgradeclient.domain.common.logger import Logger
from upgradeclient.domain.model.event.event import Event


logger = Logger.get_logger(__name__)


class DownloadHandlerThread(Thread):
    def __init__(self, json_data, service):
        super(DownloadHandlerThread, self).__init__()
        self.service = service
        self.json_data = json_data

    def run(self):
        event = Event.from_json(self.json_data)
        self.service.handle(event)


class DownloadService(object):
    def __init__(self, cache=None, handler_factory=None, abstruct_path=None, relative_path=None, check_interval=15):
        self.cache = cache
        self.sub_threads = []
        self.abstruct_path = abstruct_path
        self.relative_path = relative_path
        self.handler_factory = handler_factory
        self.check_interval = check_interval or 15

    def start(self):
        def target():
            while True:
                messages = self.cache.read(self.abstruct_path, self.relative_path)
                if not messages:
                    time.sleep(self.check_interval)
                    continue
                for message in messages:
                    t = DownloadHandlerThread(message, self)
                    t.setDaemon(True)
                    t.start()
                    self.sub_threads.append(t)

                while True:
                    threads_status = map(lambda _: not _.isAlive(), self.sub_threads)
                    if all(threads_status):
                        break
                    logger.warning('download service thread group not finished, ignore, number={0}'.format(len(messages)))
                    time.sleep(1)
                time.sleep(self.check_interval)
        t = Thread(target=target)
        t.setDaemon(True)
        t.start()

    def handle(self, obj):
        fdirname = os.path.join(self.cache.base_path, 'download_cache')
        if not os.path.exists(fdirname):
            os.makedirs(fdirname)
        filepath = os.path.join(fdirname, obj.get_filename())
        if os.path.exists(filepath):
            logger.warning('download file has not been consumed, ignore, path={0}'.format(filepath))
            return
        handler = self.handler_factory.create_download_handler(obj)
        handler.handle(obj)
