from classes.models.base_model import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class mSetting(BaseModel):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(nullable=True)
    value: Mapped[str]  
    