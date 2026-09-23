from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from getpass import getpass
from pathlib import Path
from uuid import uuid4

# Allow `uv run python scripts/create_superuser.py` from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database.session import get_session_factory
from app.core.security.passwords import hash_password
from app.modules.auth.domain.admin_entities import Admin
from app.modules.auth.domain.value_objects import normalize_email
from app.modules.auth.infrastructure.admin_repository import SQLAlchemyAdminRepository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the initial ScanWell admin account."
    )
    parser.add_argument("--name", help="Admin display name")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password")
    parser.add_argument("--role", help="Admin role")
    return parser.parse_args()


def _required_value(value: str | None, prompt: str) -> str:
    if value is not None and value.strip():
        return value.strip()
    if not sys.stdin.isatty():
        raise ValueError(f"{prompt} is required in non-interactive mode")
    entered = input(f"{prompt}: ").strip()
    if not entered:
        raise ValueError(f"{prompt} cannot be empty")
    return entered


def _password_value(value: str | None) -> str:
    if value is not None:
        password = value
    else:
        if not sys.stdin.isatty():
            raise ValueError("Admin password is required in non-interactive mode")
        password = getpass("Admin password: ")
        confirm = getpass("Confirm password: ")
        if password != confirm:
            raise ValueError("Passwords do not match")

    if len(password) < 6 or len(password) > 128:
        raise ValueError("Admin password must be between 6 and 128 characters")
    return password


async def create_superuser(
    *,
    name: str,
    email: str,
    password: str,
    role: str,
) -> bool:
    normalized_email = normalize_email(email)
    if "@" not in normalized_email:
        raise ValueError("Admin email is invalid")

    session_factory = get_session_factory()
    async with session_factory() as session:
        admins = SQLAlchemyAdminRepository(session)

        # auth_admins.email is indexed/unique: one lookup, no relationship loading.
        existing = await admins.get_by_email(normalized_email)
        if existing is not None:
            return False

        now = datetime.now(UTC)
        admin = Admin(
            id=uuid4(),
            name=name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            role=role.strip(),
            status="Active",
            last_login_at=None,
            created_at=now,
            updated_at=now,
        )
        await admins.add(admin)
        await session.commit()
        return True


async def _main() -> int:
    args = _parse_args()

    name = (args.name or settings.default_admin_name).strip()
    email = _required_value(args.email or settings.default_admin_email, "Admin email")
    password = _password_value(args.password or settings.default_admin_password)
    role = (args.role or settings.default_admin_role).strip()

    if not name:
        raise ValueError("Admin name cannot be empty")
    if not role:
        raise ValueError("Admin role cannot be empty")

    created = await create_superuser(
        name=name,
        email=email,
        password=password,
        role=role,
    )
    if created:
        print(f"Admin created successfully: {normalize_email(email)}")
    else:
        print(f"Admin already exists: {normalize_email(email)}. No changes made.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_main()))
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
