from contextlib import contextmanager
from .repositories.registry import REPO_REGISTRY
from .repositories.base_repository import BaseRepo
from sqlalchemy.orm.session import Session


class UnitOfWork:
    """Реализация паттерна UnitOfWork"""
    session: Session

    def __init__(self, session_factory, repo_registry=REPO_REGISTRY):
        self.session_factory = session_factory
        self._repo_registry = repo_registry
        self._repos = {}
        self.session = None

    @contextmanager
    def start(self):
        self.session = self.session_factory()
        try:
            yield self
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            self._repos.clear()
            self.session = None

    def repo(self, name) -> BaseRepo:
        """Получает репозиторий по имени и регистра"""
        if name not in self._repos:
            repo_cls = self._repo_registry[name]
            self._repos[name] = repo_cls(self.session)
        return self._repos[name]
