
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


from config import DATABASE_URL
from classes import models




engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

#Поддежка каскадного удаления для SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def create_tables():
    """
    Создаёт таблицы в БД
    """
    models.BaseModel.metadata.create_all(bind=engine)


        
