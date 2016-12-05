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
from app.models import User, Role, RolePermission
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('YSYS_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade

    from app.models import Permission
    from app.models import Role
    from app.models import Gender
    from app.models import Relationship
    from app.models import PurposeType
    from app.models import ReferrerType
    from app.models import BookingState
    from app.models import AssignmentScoreGrade
    from app.models import GREVScore
    from app.models import GREQScore
    from app.models import GREAWScore
    from app.models import InvitationType
    from app.models import User
    from app.models import PreviousAchievementType
    from app.models import EducationType
    from app.models import Product
    from app.models import CourseType
    from app.models import Course
    from app.models import Period
    from app.models import iPadCapacity
    from app.models import iPadState
    from app.models import Room
    from app.models import iPad
    from app.models import Lesson
    from app.models import Section
    from app.models import iPadContent
    from app.models import Assignment
    from app.models import Test
    from app.models import AnnouncementType

    # migrate database to latest revision
    upgrade()

    # insert initial data
    Permission.insert_permissions()
    Role.insert_roles()
    Gender.insert_genders()
    Relationship.insert_relationships()
    PurposeType.insert_purpose_types()
    ReferrerType.insert_referrer_types()
    BookingState.insert_booking_states()
    AssignmentScoreGrade.insert_assignment_score_grades()
    GREVScore.insert_gre_v_scores()
    GREQScore.insert_gre_q_scores()
    GREAWScore.insert_gre_aw_scores()
    InvitationType.insert_invitation_types()
    User.insert_admin()
    PreviousAchievementType.insert_previous_achievement_types()
    EducationType.insert_education_types()
    Product.insert_products()
    CourseType.insert_course_types()
    Course.insert_courses()
    Period.insert_periods()
    iPadCapacity.insert_ipad_capacities()
    iPadState.insert_ipad_states()
    Room.insert_rooms()
    iPad.insert_ipads()
    Lesson.insert_lessons()
    Section.insert_sections()
    iPadContent.insert_ipad_contents()
    Assignment.insert_assignments()
    Test.insert_tests()
    AnnouncementType.insert_announcement_types()


if __name__ == '__main__':
    manager.run()