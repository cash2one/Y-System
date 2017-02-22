# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
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


def __add_feed(user, event, category):
    feed = Feed(user_id=user.id, event=event, category=category)
    db.session.add(feed)


def add_feed(user, event, category, ignore_in=0):
    last_feed = None
    if ignore_in > 0:
        last_feed = Feed.query\
            .filter(Feed.user_id == user.id)\
            .filter(Feed.event == event)\
            .filter(Feed.category == category)\
            .filter(Feed.timestamp + timedelta(seconds=ignore_in) < datetime.utcnow())\
            .order_by(Feed.timestamp.desc())\
            .first()
    if last_feed is None:
        __add_feed(user_id=user.id, event=event, category=category)