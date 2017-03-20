# -*- coding: utf-8 -*-

import sys


reload(sys)
sys.setdefaultencoding('utf-8');


import os


if os.path.exists('.env'):
    print u'Importing environment from . env ...'
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]


from app import celery, create_app


app = create_app(os.getenv('YSYS_CONFIG') or 'default')
app.app_context().push()