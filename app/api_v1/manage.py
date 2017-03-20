# -*- coding: utf-8 -*-

from sqlalchemy import or_
from flask import jsonify, request, current_app, url_for
from ..models import User
from . import api
from .decorators import permission_required
from .errors import bad_request