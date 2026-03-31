"""add foreign key indexes

Revision ID: 1fd97b94581d
Revises: 3ee0c9e2add3
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '1fd97b94581d'
down_revision: Union[str, Sequence[str], None] = '3ee0c9e2add3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_grade_distributions_professor_id', 'grade_distributions', ['professor_id'], if_not_exists=True)
    op.create_index('ix_grade_distributions_course_id', 'grade_distributions', ['course_id'], if_not_exists=True)
    op.create_index('ix_rmp_ratings_professor_id', 'rmp_ratings', ['professor_id'], if_not_exists=True)
    op.create_index('ix_rmp_comments_rmp_rating_id', 'rmp_comments', ['rmp_rating_id'], if_not_exists=True)
    op.create_index('ix_gaucho_scores_professor_id', 'gaucho_scores', ['professor_id'], if_not_exists=True)
    op.create_index('ix_gaucho_scores_course_id', 'gaucho_scores', ['course_id'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_gaucho_scores_course_id', table_name='gaucho_scores', if_exists=True)
    op.drop_index('ix_gaucho_scores_professor_id', table_name='gaucho_scores', if_exists=True)
    op.drop_index('ix_rmp_comments_rmp_rating_id', table_name='rmp_comments', if_exists=True)
    op.drop_index('ix_rmp_ratings_professor_id', table_name='rmp_ratings', if_exists=True)
    op.drop_index('ix_grade_distributions_course_id', table_name='grade_distributions', if_exists=True)
    op.drop_index('ix_grade_distributions_professor_id', table_name='grade_distributions', if_exists=True)
