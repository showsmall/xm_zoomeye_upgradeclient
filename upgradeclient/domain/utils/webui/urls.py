#! -*- coding: utf-8 -*-


url_patterns = [
    r'/(.*)/', 'RedirectView',
    r'/', 'IndexView',
    r'/firmware', 'FirmwareView',
    r'/ajax/firmware/list', 'FirmwareListView',
    r'/firmware/([0-9]+)', 'FirmwareDetailView',
    r'/statics/(js|css|img|fonts)/(.*)', 'StaticFileView',
    r'/ajax/exception/threads', 'ExceptionThreadView',
    r'/ajax/exception/fmodels', 'ExceptionFmodelView',
    r'/ajax/exception/excepts', 'ExceptionExceptView',
    r'/ajax/exception/realtime', 'ExceptionRealtimeView',
]
