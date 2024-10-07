import sqlalchemy
from sqlalchemy import orm

# from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"


def create_engine():
    return sqlalchemy.create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )


def session_local(engine):
    SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal
