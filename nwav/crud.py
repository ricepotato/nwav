import hashlib
from optparse import Option
from typing import Optional
from sqlalchemy.orm import Session
import models

# from schemas import Blob, Shot, BlobType


def get_sha256(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_video(db: Session, name: str, path: str, sha256: str) -> Optional[int]:
    new_video_file = models.VideoFile(
        name=name, path=path, sha256=sha256, path_sha256=get_sha256(path)
    )
    db.add(new_video_file)
    db.commit()
    db.flush()
    return new_video_file.id


def get_video_by_id(db: Session, id: int) -> Optional[models.VideoFile]:
    return db.query(models.VideoFile).filter(models.VideoFile.id == id).one_or_none()


def get_video_by_path(db: Session, path: str) -> Optional[models.VideoFile]:
    path_sha256 = get_sha256(path)
    return (
        db.query(models.VideoFile)
        .filter(models.VideoFile.path_sha256 == path_sha256)
        .one_or_none()
    )
