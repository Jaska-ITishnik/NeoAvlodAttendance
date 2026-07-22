import hmac

import bcrypt
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

from config import settings


SESSION_ADMIN_KEY = "attendance_admin_username"


class UsernameAndPasswordProvider(AuthProvider):
    """Session authentication backed by configured admin credentials."""

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        errors = {}
        if not username.strip():
            errors["username"] = "Loginni kiriting"
        if not password:
            errors["password"] = "Parolni kiriting"
        if errors:
            raise FormValidationError(errors)

        if not settings.USERNAME or not self._password_matches(password):
            raise LoginFailed("Login yoki parol noto‘g‘ri")
        if not hmac.compare_digest(username.strip(), settings.USERNAME):
            raise LoginFailed("Login yoki parol noto‘g‘ri")

        request.session.clear()
        request.session[SESSION_ADMIN_KEY] = settings.USERNAME
        return response

    @staticmethod
    def _password_matches(password: str) -> bool:
        if settings.ADMIN_PASSWORD_HASH:
            try:
                return bcrypt.checkpw(
                    password.encode("utf-8"),
                    settings.ADMIN_PASSWORD_HASH.encode("utf-8"),
                )
            except (ValueError, TypeError):
                return False
        if settings.ADMIN_PASSWORD:
            return hmac.compare_digest(password, settings.ADMIN_PASSWORD)
        return False

    async def is_authenticated(self, request: Request) -> bool:
        username = request.session.get(SESSION_ADMIN_KEY)
        if not username or not settings.USERNAME:
            return False
        if not hmac.compare_digest(str(username), settings.USERNAME):
            return False
        request.state.user = username
        return True

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(
            app_title="Neo Avlod · Davomat boshqaruvi",
            logo_url=str(request.url_for("admin:statics", path="images/logo.svg")),
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=getattr(request.state, "user", "Administrator"))

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
