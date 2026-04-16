from ..uow import UnitOfWork

from ..utils import hash_password
from config import PASSWORD_KEY


class AuthService:
    """Сервис авторизации"""

    def __init__(self, uow: UnitOfWork):
        self._logged = False
        self.uow = uow

    def is_logged(self) -> bool:
        """Возвращает состояние авторизации"""
        return self._logged

    def authorize(self, password) -> None:
        """Авторизация. Ничего не возвращает"""
        pwd_hash = hash_password(password)

        with self.uow.start():
            settings_repo = self.uow.repo("setting")
            base_pwd = settings_repo.get_by_key(PASSWORD_KEY)
            if base_pwd is None:
                self._logged = True
                return

        if pwd_hash == base_pwd.value:
            self._logged = True

        return None
