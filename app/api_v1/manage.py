# -*- coding: utf-8 -*-

from sqlalchemy import or_
from flask import jsonify, request, current_app, url_for
from ..models import User
from . import api
from .decorators import permission_required
from .errors import bad_request


# @api.route('/suggest-user/')
# @permission_required(u'管理')
# def suggest_user():
#     q = request.args.get('q', '')
#     if q == '':
#         return bad_request('Empty query')
#     users = User.query\
#         .filter(or_(
#             User.name.like('%' + q + '%'),
#             User.email.like('%' + q + '%'),
#         ))\
#         .all()
#     return jsonify({'results': [user.to_json_suggestion for user in users]})