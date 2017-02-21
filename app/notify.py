# -*- coding: utf-8 -*-

from flask import flash
from . import db
from .models import Announcement, AnnouncementType
from .models import Feed


def get_announcements(type_name, user=None, flash_first=False):
    query = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == type_name)\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)
    if flash_first:
        announcement = query.first()
        if announcement is not None:
            flash(u'<div class="content"><div class="header">%s</div>%s</div>' % (announcement.title, announcement.body_html), category='announcement')
        return
    else:
        announcements = query.order_by(Announcement.modified_at.desc()).all()
        for announcement in announcements:
            if not user.notified_by(announcement=announcement):
                flash(u'<div class="content"><div class="header">%s</div>%s</div>' % (announcement.title, announcement.body_html), category='announcement')
                announcement.notify(user=user)
        return announcements


def add_feed(user, event, category):
    feed = Feed(user_id=user.id, event=event, category=category)
    db.session.add(feed)