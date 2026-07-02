from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.identity.models import OrgRole, UserStatus
from app.modules.identity.repository import IdentityRepository
from scripts.bootstrap_org import bootstrap_org


def test_bootstrap_creates_org_and_active_admin(db: Session) -> None:
    result = bootstrap_org(
        db,
        org_slug="acme",
        org_name="Acme",
        admin_email="admin@acme.example",
        admin_name="Acme Admin",
    )
    db.flush()

    assert result.org_created is True
    assert result.user_created is True

    repository = IdentityRepository(db)
    org = repository.get_organization_by_slug("acme")
    assert org is not None
    assert org.id == result.org_id
    user = repository.get_user_by_email_for_org(org_id=org.id, email="admin@acme.example")
    assert user is not None
    assert user.status == UserStatus.active
    membership = repository.get_membership(org_id=org.id, user_id=user.id)
    assert membership is not None
    assert membership.is_org_admin is True
    assert membership.role == OrgRole.knowledge_admin


def test_bootstrap_is_idempotent(db: Session) -> None:
    first = bootstrap_org(
        db, org_slug="acme", org_name="Acme", admin_email="admin@acme.example", admin_name="A"
    )
    db.flush()
    second = bootstrap_org(
        db, org_slug="acme", org_name="Acme", admin_email="admin@acme.example", admin_name="A"
    )
    db.flush()

    assert second.org_created is False
    assert second.user_created is False
    assert second.org_id == first.org_id
    assert second.user_id == first.user_id
    assert IdentityRepository(db).count_org_admins(org_id=first.org_id) == 1


def test_bootstrap_reactivates_and_promotes_existing_user(db: Session) -> None:
    result = bootstrap_org(
        db, org_slug="acme", org_name="Acme", admin_email="admin@acme.example", admin_name="A"
    )
    db.flush()
    repository = IdentityRepository(db)
    membership = repository.get_membership(org_id=result.org_id, user_id=result.user_id)
    assert membership is not None
    membership.is_org_admin = False
    membership.role = OrgRole.member
    user = repository.get_user_by_email_for_org(org_id=result.org_id, email="admin@acme.example")
    assert user is not None
    user.status = UserStatus.disabled
    db.flush()

    bootstrap_org(
        db, org_slug="acme", org_name="Acme", admin_email="admin@acme.example", admin_name="A"
    )
    db.flush()

    refreshed_user = repository.get_user_by_email_for_org(
        org_id=result.org_id, email="admin@acme.example"
    )
    refreshed_membership = repository.get_membership(org_id=result.org_id, user_id=result.user_id)
    assert refreshed_user is not None
    assert refreshed_user.status == UserStatus.active
    assert refreshed_membership is not None
    assert refreshed_membership.is_org_admin is True
    assert refreshed_membership.role == OrgRole.knowledge_admin
