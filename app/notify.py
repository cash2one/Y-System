# -*- coding: utf-8 -*-

from flask import flash
from .models import Announcement, AnnouncementType


def get_announcements(type_name, user=None, flash_first=False):
    query = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == type_name)\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)
    if flash_first:
        announcement = query.first()
        if announcement is not None:
            flash(u'[%s]%s' % (announcement.title, announcement.body), category='announcement')
        return
    else:
        announcements = query.order_by(Announcement.modified_at.desc()).all()
        for announcement in announcements:
            if not user.notified_by(announcement=announcement):
                flash(u'<div class="content" style="text-align: left;"><div class="header">%s</div>%s</div>' % (announcement.title, announcement.body_html), category='announcement')
                announcement.notify(user=user)
        return announcements


def add_feed(user, message, category, snapshot_json):
    pass