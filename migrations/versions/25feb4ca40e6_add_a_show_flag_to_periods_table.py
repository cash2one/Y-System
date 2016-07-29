"""add a show flag to periods table

Revision ID: 25feb4ca40e6
Revises: 64425d8df01a
Create Date: 2016-07-29 10:52:27.266333

"""

# revision identifiers, used by Alembic.
revision = '25feb4ca40e6'
down_revision = '64425d8df01a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('periods', sa.Column('show', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('periods', 'show')
    ### end Alembic commands ###
