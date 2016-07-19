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
from app.models import Activation
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('YSYS_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Activation=Activation)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, BookingState, RentalType, iPadCapacity, iPadState, OperationType, User, Activation

    # migrate database to latest revision
    upgrade()

    # insert initial data
    Role.insert_roles()

    BookingState.insert_booking_states()

    RentalType.insert_rental_types()

    iPadCapacity.insert_ipad_capacities()

    iPadState.insert_ipad_states()

    OperationType.insert_operation_types()

    User.insert_admin()

    Activation.insert_activations()


if __name__ == '__main__':
    manager.run()