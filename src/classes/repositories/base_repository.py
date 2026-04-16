from sqlalchemy.orm.session import Session
from classes.models.base_model import BaseModel
from sqlalchemy import select, update


class BaseRepo:
    """
    Базовый класс-репозиторий
    """

    def __init__(self, model: BaseModel, session: Session):
        self._model = model
        self._session = session

    def add(self, instance: BaseModel):

        self._session.add(instance)
        self._session.flush()

        return instance

    def delete(self, instance: BaseModel):
        self._session.delete(instance)

    def get_by_id(self, id_: int) -> BaseModel:
        m = BaseModel()

        return self._session.get(self._model, id_)

    def list(
        self, filter_: dict = {}, offset: int = 0, limit: int = 0
    ) -> list[BaseModel]:
        stmt = select(self._model)

        if filter_:
            stmt = stmt.filter_by(**filter_)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = self._session.execute(stmt)

        return result.scalars().all()

    def update(self, id, data):
        stmt = update(self._model).values(**data).where(self._model.id == id)
        self._session.execute(stmt)

        return id
