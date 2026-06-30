from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.groups.models import Group, GroupMembership, GroupRole


class GroupsRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_group(self, group: Group) -> Group:
        self._db.add(group)
        return group

    def add_membership(self, membership: GroupMembership) -> GroupMembership:
        self._db.add(membership)
        return membership

    def delete_membership(self, membership: GroupMembership) -> None:
        self._db.delete(membership)

    def get_group(self, *, org_id: UUID, group_id: UUID) -> Group | None:
        return self._db.execute(
            select(Group).where(Group.org_id == org_id, Group.id == group_id)
        ).scalar_one_or_none()

    def list_groups(self, *, org_id: UUID) -> list[Group]:
        return list(
            self._db.execute(
                select(Group).where(Group.org_id == org_id).order_by(Group.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_membership(
        self, *, org_id: UUID, group_id: UUID, user_id: UUID
    ) -> GroupMembership | None:
        return self._db.execute(
            select(GroupMembership).where(
                GroupMembership.org_id == org_id,
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_user_group_ids(self, *, org_id: UUID, user_id: UUID) -> list[UUID]:
        return list(
            self._db.execute(
                select(GroupMembership.group_id).where(
                    GroupMembership.org_id == org_id,
                    GroupMembership.user_id == user_id,
                )
            )
            .scalars()
            .all()
        )

    def list_user_lead_group_ids(self, *, org_id: UUID, user_id: UUID) -> list[UUID]:
        return list(
            self._db.execute(
                select(GroupMembership.group_id).where(
                    GroupMembership.org_id == org_id,
                    GroupMembership.user_id == user_id,
                    GroupMembership.role == GroupRole.lead,
                )
            )
            .scalars()
            .all()
        )
