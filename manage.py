# -*- coding: utf-8 -*-

import sys


reload(sys)
sys.setdefaultencoding('utf-8');


import os


if os.path.exists('.env'):
    print('Importing environment from .env...')
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
    '''Run cleanup tasks.'''
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
                print 'remove', full_db_file
        db.drop_all()
    else:
        confirm = raw_input(u'Are you sure to clean up the database? [Y/n]: ')
        if confirm == u'Y':
            db.drop_all()
            print '---> All data are deleted.'


@manager.command
def deploy():
    '''Run deployment tasks.'''
    from flask_migrate import upgrade
    from app.models import Color
    from app.models import Permission
    from app.models import Role
    from app.models import IDType
    from app.models import Gender
    from app.models import Relationship
    from app.models import PurposeType
    from app.models import ReferrerType
    from app.models import BookingState
    from app.models import AssignmentScoreGrade
    from app.models import GREAWScore
    from app.models import InvitationType
    from app.models import CourseType
    from app.models import Lesson
    from app.models import Section
    from app.models import User
    from app.models import Tag
    from app.models import EducationType
    from app.models import ScoreType
    from app.models import Product
    from app.models import Course
    from app.models import Period
    from app.models import iPadCapacity
    from app.models import iPadState
    from app.models import Room
    from app.models import iPad
    from app.models import iPadContent
    from app.models import Assignment
    from app.models import Test
    from app.models import NotaBene
    from app.models import AnnouncementType

    # migrate database to latest revision
    upgrade()

    # insert initial data
    Color.insert_colors()
    Permission.insert_permissions()
    Role.insert_roles()
    IDType.insert_id_types()
    Gender.insert_genders()
    Relationship.insert_relationships()
    PurposeType.insert_purpose_types()
    ReferrerType.insert_referrer_types()
    BookingState.insert_booking_states()
    AssignmentScoreGrade.insert_assignment_score_grades()
    GREAWScore.insert_gre_aw_scores()
    InvitationType.insert_invitation_types()
    CourseType.insert_course_types()
    Lesson.insert_lessons()
    Section.insert_sections()
    User.insert_admin()
    Tag.insert_tags()
    EducationType.insert_education_types()
    ScoreType.insert_score_types()
    Product.insert_products()
    Course.insert_courses()
    Period.insert_periods()
    iPadCapacity.insert_ipad_capacities()
    iPadState.insert_ipad_states()
    Room.insert_rooms()
    iPad.insert_ipads()
    iPadContent.insert_ipad_contents()
    Assignment.insert_assignments()
    Test.insert_tests()
    NotaBene.insert_notate_bene()
    AnnouncementType.insert_announcement_types()


@manager.command
def backup():
    '''Run backup tasks.'''
    pass


if __name__ == '__main__':
    manager.run()