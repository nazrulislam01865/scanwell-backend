from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database.base import Base
from app.modules.auth.domain.value_objects import LoginMethod
from app.modules.auth.infrastructure.models import AuthSessionModel, AuthUserModel
from app.modules.auth.infrastructure.repository import (
    auth_session_model_to_entity,
    user_model_to_entity,
)


def test_auth_tables_are_registered_in_sqlalchemy_metadata() -> None:
    assert "auth_users" in Base.metadata.tables
    assert "auth_verification_codes" in Base.metadata.tables
    assert "auth_sessions" in Base.metadata.tables

    codes_table = Base.metadata.tables["auth_verification_codes"]
    code_foreign_keys = {str(fk.column) for fk in codes_table.c.user_id.foreign_keys}
    assert code_foreign_keys == {"auth_users.id"}

    sessions_table = Base.metadata.tables["auth_sessions"]
    session_foreign_keys = {str(fk.column) for fk in sessions_table.c.user_id.foreign_keys}
    assert session_foreign_keys == {"auth_users.id"}


def test_user_model_converts_to_domain_entity() -> None:
    now = datetime.now(UTC)
    model = AuthUserModel(
        id=uuid4(),
        name="Nazrul",
        email="nazrul@example.com",
        phone=None,
        password_hash="$argon2id$example",
        preferred_login_method=LoginMethod.PASSWORD.value,
        email_verified_at=now,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    entity = user_model_to_entity(model)

    assert entity.id == model.id
    assert entity.email == model.email
    assert entity.preferred_login_method is LoginMethod.PASSWORD


def test_auth_session_model_converts_to_domain_entity() -> None:
    now = datetime.now(UTC)
    model = AuthSessionModel(
        id=uuid4(),
        user_id=uuid4(),
        refresh_token_hash="a" * 64,
        expires_at=now + timedelta(days=30),
        created_at=now,
        last_used_at=now,
        revoked_at=None,
        revoked_reason=None,
    )

    entity = auth_session_model_to_entity(model)

    assert entity.id == model.id
    assert entity.user_id == model.user_id
    assert entity.refresh_token_hash == model.refresh_token_hash
    assert entity.revoked is False
