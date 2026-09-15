from datetime import UTC, datetime
from uuid import uuid4

from app.core.database.base import Base
from app.modules.auth.infrastructure.models import AuthUserModel
from app.modules.auth.infrastructure.repository import user_model_to_entity
from app.modules.auth.domain.value_objects import LoginMethod


def test_auth_tables_are_registered_in_sqlalchemy_metadata() -> None:
    assert "auth_users" in Base.metadata.tables
    assert "auth_verification_codes" in Base.metadata.tables

    codes_table = Base.metadata.tables["auth_verification_codes"]
    foreign_keys = {str(fk.column) for fk in codes_table.c.user_id.foreign_keys}
    assert foreign_keys == {"auth_users.id"}


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
