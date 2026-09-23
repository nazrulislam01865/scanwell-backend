from app.core.database.transaction import TransactionManager
from app.core.security.passwords import verify_password
from app.modules.auth.application.admin_dto import AdminAuthResult, to_admin_dto
from app.modules.auth.application.commands import LoginUserCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.domain.admin_repositories import AdminRepository
from app.modules.auth.domain.exceptions import AccountDisabledError, InvalidCredentialsError
from app.modules.auth.domain.value_objects import normalize_email


class LoginAdmin:
    def __init__(
        self,
        *,
        admins: AdminRepository,
        sessions: AuthSessionService,
        transaction: TransactionManager,
    ) -> None:
        self._admins = admins
        self._sessions = sessions
        self._transaction = transaction

    async def execute(self, command: LoginUserCommand) -> AdminAuthResult:
        admin = await self._admins.get_by_email(normalize_email(command.email))
        if admin is None or not verify_password(command.password, admin.password_hash):
            raise InvalidCredentialsError
        if not admin.is_active:
            raise AccountDisabledError

        tokens = await self._sessions.issue(user_id=admin.id)
        admin.mark_logged_in()
        await self._admins.save(admin)
        await self._transaction.commit()

        return AdminAuthResult(
            admin=to_admin_dto(admin),
            tokens=tokens,
        )
