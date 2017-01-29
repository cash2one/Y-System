# -*- coding: utf-8 -*-

from functools import wraps
from flask import abort
from flask_login import current_user


def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def administrator_required(f):
    return permission_required(u'管理权限')(f)


def developer_required(f):
    return permission_required(u'开发权限')(f)