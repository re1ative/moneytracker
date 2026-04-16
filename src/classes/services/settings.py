from ..uow import UnitOfWork
from ..models import mSetting
from sqlalchemy import select


class SettingService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def set_setting(self, key, value):
        result = None

        with self.uow.start():
            repo = self.uow.repo("setting")
            exists_stmt = select(mSetting).filter(mSetting.key == key)
            exists = self.uow.session.execute(exists_stmt).scalar_one_or_none()

            if exists:
                repo.update(exists.id, {"value": value})

                result = exists.id
            else:
                setting = mSetting(key=key, value=value)
                repo.add(setting)
                result = setting.id

        return result

    def get_value(self, key):
        result = None
        with self.uow.start():
            repo = self.uow.repo("setting")
            stmt = select(mSetting).filter(mSetting.key == key)
            item = self.uow.session.execute(stmt).scalar_one_or_none()

            if item:
                result = item.value

        return result

    def get_list(self, filters: dict):

        results = []

        with self.uow.start():
            repo = self.uow.repo("setting")
            results = repo.list(filters)

        return results
