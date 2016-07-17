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
from app.models import User, Role, Permission
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('YSYS_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Run deployment tasks."""
    # from flask_migrate import upgrade
    from app.models import Role, BookingState, RentalType, iPadCapacity

    # migrate database to latest revision
    # upgrade()

    # create user roles
    Role.insert_roles()

    # create booking states
    BookingState.insert_booking_states()

    # create rental types
    RentalType.insert_rental_types()

    # create iPad capacities
    iPadCapacity.insert_ipad_capacities()

if __name__ == '__main__':
    manager.run()