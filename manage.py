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


from app import create_app, db
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.getenv('YSYS_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def cleanup():
    '''
    Run cleanup tasks.
    '''
    if app.debug:
        from config import basedir
        from shutil import rmtree
        db_files = [
            'ysys-dev.sqlite',
            'migrations',
        ]
        for db_file in db_files:
            full_db_file = os.path.join(basedir, db_file)
            if os.path.exists(full_db_file):
                if os.path.isfile(full_db_file):
                    os.remove(full_db_file)
                elif os.path.isdir(full_db_file):
                    rmtree(full_db_file)
                print u'---> Remove %s' %  full_db_file
        db.drop_all()
    else:
        confirm = raw_input(u'Are you sure to clean up the database? [Y/n]: ')
        if confirm == u'Y':
            db.drop_all()
            print u'---> All data are deleted.'


@manager.command
def deploy():
    '''
    Run deployment tasks.
    '''

    # migrate database to latest revision
    from flask_migrate import upgrade
    upgrade()

    # insert data
    from app.models import Color
    Color.insert_entries()

    from app.models import Permission
    Permission.insert_entries()

    from app.models import Role
    Role.insert_entries()

    from app.models import IDType
    IDType.insert_entries()

    from app.models import Gender
    Gender.insert_entries()

    from app.models import Relationship
    Relationship.insert_entries()

    from app.models import PurposeType
    PurposeType.insert_entries()

    from app.models import ReferrerType
    ReferrerType.insert_entries()

    from app.models import BookingState
    BookingState.insert_entries()

    from app.models import AssignmentScoreGrade
    AssignmentScoreGrade.insert_entries()

    from app.models import GREAWScore
    GREAWScore.insert_entries()

    from app.models import ScoreLabel
    ScoreLabel.insert_entries()

    from app.models import InvitationType
    InvitationType.insert_entries()

    from app.models import EducationType
    EducationType.insert_entries()

    from app.models import ScoreType
    ScoreType.insert_entries()

    from app.models import CourseType
    CourseType.insert_entries()

    from app.models import iPadCapacity
    iPadCapacity.insert_entries()

    from app.models import iPadState
    iPadState.insert_entries()

    from app.models import Room
    Room.insert_entries()

    from app.models import Lesson
    Lesson.insert_entries()

    from app.models import Section
    Section.insert_entries()

    from app.models import Assignment
    Assignment.insert_entries()

    from app.models import Test
    Test.insert_entries()

    from app.models import AnnouncementType
    AnnouncementType.insert_entries()

    from config import basedir
    data = raw_input(u'Enter data identifier (e.g.: initial or 20160422): ')
    datadir = os.path.join(basedir, 'data', data)
    if os.path.exists(datadir):
        from app.models import User
        User.insert_entries(data=data, basedir=basedir)

        from app.models import UserCreation
        UserCreation.insert_entries(data=data, basedir=basedir)

        from app.models import Purpose
        Purpose.insert_entries(data=data, basedir=basedir)

        from app.models import Referrer
        Referrer.insert_entries(data=data, basedir=basedir)

        from app.models import Product
        Product.insert_entries(data=data, basedir=basedir)

        from app.models import Purchase
        Purchase.insert_entries(data=data, basedir=basedir)

        from app.models import Punch
        Punch.insert_entries(data=data, basedir=basedir)

        from app.models import Tag
        Tag.insert_entries(data='initial', basedir=basedir)

        from app.models import Course
        Course.insert_entries(data='initial', basedir=basedir)

        from app.models import Period
        Period.insert_entries(data='initial', basedir=basedir)

        from app.models import iPad
        iPad.insert_entries(data='initial', basedir=basedir)

        from app.models import iPadContent
        iPadContent.insert_entries(data='initial', basedir=basedir)

        from app.models import NotaBene
        NotaBene.insert_entries(data='initial', basedir=basedir)

        from app.models import Feed
        Feed.insert_entries(data=data, basedir=basedir)
    else:
        print u'---> Invalid data identifier: %s' % data


@manager.command
def backup():
    '''
    Run backup tasks.
    '''
    from config import basedir
    data = raw_input(u'Enter data identifier (e.g.: backup or 20160422): ')
    datadir = os.path.join(basedir, 'data', data)
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    from app.models import User
    User.backup_entries(data=data, basedir=basedir)

    from app.models import UserCreation
    UserCreation.backup_entries(data=data, basedir=basedir)

    from app.models import Purpose
    Purpose.backup_entries(data=data, basedir=basedir)

    from app.models import Referrer
    Referrer.backup_entries(data=data, basedir=basedir)

    from app.models import Product
    Product.backup_entries(data=data, basedir=basedir)

    from app.models import Purchase
    Purchase.backup_entries(data=data, basedir=basedir)

    from app.models import Punch
    Punch.backup_entries(data=data, basedir=basedir)

    from app.models import Feed
    Feed.backup_entries(data=data, basedir=basedir)


if __name__ == '__main__':
    manager.run()