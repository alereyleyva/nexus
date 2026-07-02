"""Bootstrap the first organization and its initial admin for a deployment.

The admin API requires an existing org admin, and OIDC/dev login reject unknown
users — so a fresh deployment has a chicken-and-egg problem: nobody can sign in,
and nobody can create the first account through the API. This operator-run command
breaks the cycle by creating, directly against the database, an organization plus
one active user that holds org-admin rights. After running it, that admin signs in
(Google OIDC in production) and manages everyone else through the admin API or the
web app — this command is not needed again for adding people.

Run it from a host with database access (e.g. a one-off task in the deploy
environment, reusing the API image and `DATABASE_URL`):

    uv run python -m scripts.bootstrap_org \\
        --org-slug acme --org-name "Acme" \\
        --admin-email admin@acme.example --admin-name "Acme Admin"

It is idempotent: an existing org/user is reused, the user is (re)activated, and
the org-admin membership is ensured — so it is safe to re-run, including to restore
admin access after a lockout.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.base import load_all_models
from app.db.session import SessionLocal
from app.modules.identity.models import (
    Organization,
    OrgMembership,
    OrgRole,
    User,
    UserStatus,
)
from app.modules.identity.repository import IdentityRepository


@dataclass(frozen=True)
class BootstrapResult:
    org_id: UUID
    user_id: UUID
    org_created: bool
    user_created: bool


def bootstrap_org(
    session: Session,
    *,
    org_slug: str,
    org_name: str,
    admin_email: str,
    admin_name: str,
    role: OrgRole = OrgRole.knowledge_admin,
) -> BootstrapResult:
    """Ensure an organization exists with the given user as an active org admin.

    Writes directly via the identity repository (the admin API cannot be used
    before the first admin exists). Flushes but does not commit — the caller owns
    the transaction boundary so this stays testable within a rolled-back session.
    """
    repository = IdentityRepository(session)

    organization = repository.get_organization_by_slug(org_slug)
    org_created = organization is None
    if organization is None:
        organization = repository.add_organization(Organization(slug=org_slug, name=org_name))
        session.flush()

    user = repository.get_user_by_email_for_org(org_id=organization.id, email=admin_email)
    user_created = user is None
    if user is None:
        user = repository.add_user(
            User(
                org_id=organization.id,
                email=admin_email,
                display_name=admin_name,
                status=UserStatus.active,
            )
        )
        session.flush()
    elif user.status != UserStatus.active:
        user.status = UserStatus.active

    membership = repository.get_membership(org_id=organization.id, user_id=user.id)
    if membership is None:
        repository.add_org_membership(
            OrgMembership(
                org_id=organization.id,
                user_id=user.id,
                role=role,
                is_org_admin=True,
            )
        )
    else:
        membership.role = role
        membership.is_org_admin = True

    return BootstrapResult(
        org_id=organization.id,
        user_id=user.id,
        org_created=org_created,
        user_created=user_created,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bootstrap_org",
        description="Create the first organization and its initial org admin.",
    )
    parser.add_argument("--org-slug", required=True, help="Unique organization slug, e.g. acme.")
    parser.add_argument("--org-name", required=True, help='Organization display name, e.g. "Acme".')
    parser.add_argument(
        "--admin-email",
        required=True,
        help="Email of the first admin. Must match the identity used to sign in.",
    )
    parser.add_argument(
        "--admin-name",
        default=None,
        help="Admin display name. Defaults to the local part of the email.",
    )
    parser.add_argument(
        "--role",
        choices=[role.value for role in OrgRole],
        default=OrgRole.knowledge_admin.value,
        help="Organization knowledge role for the admin (default: knowledge_admin).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    admin_name = args.admin_name or args.admin_email.split("@", 1)[0]

    load_all_models()
    session = SessionLocal()
    try:
        result = bootstrap_org(
            session,
            org_slug=args.org_slug,
            org_name=args.org_name,
            admin_email=args.admin_email,
            admin_name=admin_name,
            role=OrgRole(args.role),
        )
        session.commit()
    finally:
        session.close()

    org_state = "created" if result.org_created else "reused"
    user_state = "created" if result.user_created else "reused"
    print(f"Organization '{args.org_slug}' {org_state} (org_id={result.org_id}).")
    print(f"Admin '{args.admin_email}' {user_state} (user_id={result.user_id}), is_org_admin=true.")
    print("Next: sign in as this admin (Google OIDC in production), then manage users via the API.")


if __name__ == "__main__":
    main()
