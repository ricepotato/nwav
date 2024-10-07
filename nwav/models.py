from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestamedTable:
    @declared_attr
    def time_created(self):
        return Column(DateTime, server_default=func.now())

    @declared_attr
    def time_updated(self):
        return Column(DateTime, onupdate=func.now())


class VideoFile(Base, TimestamedTable):
    __tablename__ = "video_file"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    path = Column(String(500))
    path_sha256 = Column(String(64), unique=True)
    sha256 = Column(String(64), unique=True)
