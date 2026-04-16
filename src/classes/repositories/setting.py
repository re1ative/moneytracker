from sqlalchemy import select
from classes.repositories.base_repository import BaseRepo
from classes.models import mSetting


class rSetting(BaseRepo):
    def __init__(self, session):
        super().__init__(mSetting, session)

    def get_by_key(self, key: str):
        stmt = select(mSetting).filter(mSetting.key == key)

        result = self._session.execute(stmt).scalar_one_or_none()

        return result
