"""add scheduled_sections table and lookup indexes

Revision ID: c4a8e1b0f2d3
Revises: 1fd97b94581d
Create Date: 2026-09-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4a8e1b0f2d3"
down_revision: Union[str, Sequence[str], None] = "1fd97b94581d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "scheduled_sections" not in tables:
        op.create_table(
            "scheduled_sections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("professor_id", sa.Integer(), nullable=True),
            sa.Column("course_id", sa.Integer(), nullable=True),
            sa.Column("quarter_code", sa.Text(), nullable=False),
            sa.Column("quarter_name", sa.Text(), nullable=True),
            sa.Column("enroll_code", sa.Text(), nullable=False),
            sa.Column("instructor_name_raw", sa.Text(), nullable=True),
            sa.Column("days", sa.Text(), nullable=True),
            sa.Column("begin_time", sa.Text(), nullable=True),
            sa.Column("end_time", sa.Text(), nullable=True),
            sa.Column("building", sa.Text(), nullable=True),
            sa.Column("room", sa.Text(), nullable=True),
            sa.Column("enrolled", sa.Integer(), nullable=True),
            sa.Column("max_enroll", sa.Integer(), nullable=True),
            sa.Column("section_cancelled", sa.Boolean(), nullable=True),
            sa.Column("fetched_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
            sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "quarter_code",
                "enroll_code",
                name="uq_scheduled_section_quarter_enroll",
            ),
        )

    inspector = sa.inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes("scheduled_sections")}
    if "ix_scheduled_sections_professor_id" not in existing:
        op.create_index(
            "ix_scheduled_sections_professor_id",
            "scheduled_sections",
            ["professor_id"],
        )
    if "ix_scheduled_sections_course_id" not in existing:
        op.create_index(
            "ix_scheduled_sections_course_id",
            "scheduled_sections",
            ["course_id"],
        )
    if "ix_scheduled_sections_quarter_code" not in existing:
        op.create_index(
            "ix_scheduled_sections_quarter_code",
            "scheduled_sections",
            ["quarter_code"],
        )


def downgrade() -> None:
    op.drop_index("ix_scheduled_sections_quarter_code", table_name="scheduled_sections")
    op.drop_index("ix_scheduled_sections_course_id", table_name="scheduled_sections")
    op.drop_index("ix_scheduled_sections_professor_id", table_name="scheduled_sections")
    op.drop_table("scheduled_sections")
