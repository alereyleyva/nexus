from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.identity.models import Organization, OrgMembership, User, UserStatus


class IdentityRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_organization(self, organization: Organization) -> Organization:
        self._db.add(organization)
        return organization

    def add_user(self, user: User) -> User:
        self._db.add(user)
        return user

    def add_org_membership(self, membership: OrgMembership) -> OrgMembership:
        self._db.add(membership)
        return membership

    def get_organization_by_slug(self, slug: str) -> Organization | None:
        return self._db.execute(
            select(Organization).where(Organization.slug == slug)
        ).scalar_one_or_none()

    def get_user_by_id_for_org(self, *, org_id: UUID, user_id: UUID) -> User | None:
        return self._db.execute(
            select(User).where(User.org_id == org_id, User.id == user_id)
        ).scalar_one_or_none()

    def get_user_by_email_for_org(self, *, org_id: UUID, email: str) -> User | None:
        return self._db.execute(
            select(User).where(User.org_id == org_id, User.email == email)
        ).scalar_one_or_none()

    def list_users_for_org(self, *, org_id: UUID) -> list[User]:
        return list(
            self._db.execute(
                select(User).where(User.org_id == org_id).order_by(User.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_membership(self, *, org_id: UUID, user_id: UUID) -> OrgMembership | None:
        return self._db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id,
                OrgMembership.user_id == user_id,
            )
        ).scalar_one_or_none()

    def count_org_admins(self, *, org_id: UUID) -> int:
        value = self._db.execute(
            select(func.count())
            .select_from(OrgMembership)
            .where(
                OrgMembership.org_id == org_id,
                OrgMembership.is_org_admin.is_(True),
            )
        ).scalar_one()
        return int(value)

    def is_active_org_member(self, *, org_id: UUID, user_id: UUID) -> bool:
        statement = (
            select(User.id)
            .join(OrgMembership, OrgMembership.user_id == User.id)
            .where(
                User.org_id == org_id,
                User.id == user_id,
                User.status == UserStatus.active,
                OrgMembership.org_id == org_id,
            )
        )
        return self._db.execute(statement).scalar_one_or_none() is not None
