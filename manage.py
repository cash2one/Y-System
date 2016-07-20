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
    from app.models import Role, BookingState, RentalType, iPadCapacity, iPadState, Room, iPad, OperationType, CourseType, Course, User, Activation, Lesson, Section

    # migrate database to latest revision
    upgrade()

    # insert initial data
    Role.insert_roles()

    BookingState.insert_booking_states()

    RentalType.insert_rental_types()

    iPadCapacity.insert_ipad_capacities()

    iPadState.insert_ipad_states()

    Room.insert_rooms()

    iPad.insert_ipads()

    OperationType.insert_operation_types()

    CourseType.insert_course_types()

    Course.insert_courses()

    User.insert_admin()

    Activation.insert_activations()

    Lesson.insert_lessons()

    Section.insert_sections()


if __name__ == '__main__':
    manager.run()