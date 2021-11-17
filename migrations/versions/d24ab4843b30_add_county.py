"""add county

Revision ID: d24ab4843b30
Revises: 16c6cc7171bf
Create Date: 2021-11-15 11:05:07.041907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd24ab4843b30'
down_revision = '16c6cc7171bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('places', sa.Column('county', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('places', 'county')
    # ### end Alembic commands ###