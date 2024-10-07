import concurrent.futures
import dataclasses
import hashlib
import json
import logging
import os
import pathlib
import urllib
import urllib.parse

import dotenv

from nwav import snapshot

log = logging.getLogger("nwa")
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
log = logging.getLogger(f"nwa.{__name__}")

dotenv.load_dotenv()


CHUNK_SIZE = 1024 * 1024


@dataclasses.dataclass
class VideoLink:
    name: str
    url: str

    def dict(self, **kwargs):
        return {"name": self.name, "url": self.url}


@dataclasses.dataclass
class VideoItem:
    url: str
    path: pathlib.Path
    name: str

    def dict(self, **kwargs):
        return {"name": self.name, "url": self.url}


@dataclasses.dataclass
class Snapshot:
    url: str
    path: pathlib.Path

    def dict(self, **kwargs):
        return {"url": self.url}


@dataclasses.dataclass
class Shot:
    name: str
    video_item: VideoItem
    snapshots: list[Snapshot]
    links: list[VideoLink]

    def dict(self, **kwargs):
        return {
            "name": self.name,
            "video_item": self.video_item.dict(),
            "snapshots": [s.dict() for s in self.snapshots],
            "links": [link.dict() for link in self.links],
        }

    def shots_dict(self):
        return {
            "name": self.name,
            "dirname": self.video_item.path.parent.name,
            "target": self.video_item.url,
            "snapshots": [s.url for s in self.snapshots],
        }


def main():
    BASE_URL = os.environ.get(
        "BASE_URL", "https://ricepotato.direct.quickconnect.to:61290/"
    )
    SNAPSHOT_PATH = os.getenv("SNAPSHOT_PATH")
    ROOT_PATH = os.getenv("ROOT_PATH")
    if ROOT_PATH is None:
        log.error("ROOT_PATH is not set.")
        return

    if SNAPSHOT_PATH is None:
        log.error("SNAPSHOT_PATH is not set.")
        return
    if BASE_URL is None:
        log.error("BASE_URL is not set.")
        return

    root_path = pathlib.Path(ROOT_PATH)
    sub_paths = ["FC2", "AV", "dirty", "other", "ul"]
    root_paths = [root_path / pathlib.Path(p) for p in sub_paths]

    log.info("ROOT_PATH = %s", os.getenv("ROOT_PATH"))
    log.info("ROOT_PATHS = %s", root_paths)
    log.info("SNAPSHOT_PATH = %s", SNAPSHOT_PATH)

    snapshot_path = pathlib.Path(SNAPSHOT_PATH)
    if not root_path.exists():
        log.warning("path not exists. %s", root_path)
        return

    for path in root_paths:
        log.info("shots process. %s", root_path.name)
        video_items = find_mp4_web_urls(path, BASE_URL)
        shots = make_video_shots(video_items, snapshot_path)
        sorted_shots = sorted(
            shots, key=lambda shot: shot.video_item.path.stat().st_mtime, reverse=True
        )
        dump_jsonfile(sorted_shots, root_path)


def find_mp4_web_urls(root_path: pathlib.Path, base_url: str) -> list[VideoItem]:
    paths = root_path.rglob("**/*")
    mp4_paths = list(filter(lambda p: p.suffix == ".mp4", paths))
    mp4_filepaths = [p for p in mp4_paths if p.is_file()]
    names = [p.name for p in mp4_filepaths]
    urls = [path_to_url(path, base_url) for path in mp4_filepaths]
    return [
        VideoItem(url=url, path=path, name=name)
        for name, path, url in zip(names, mp4_filepaths, urls)
    ]


def path_to_url(path: pathlib.Path, base_url: str) -> str:
    """가장 앞의 /web 을 삭제하고 base url 과 합쳐 URL 을 출력"""
    path_url = urllib.parse.urlsplit(path.as_uri())
    r_path = path_url.path.replace("/web", "")
    return urllib.parse.urljoin(base_url, r_path)


def make_video_shots(
    video_items: list[VideoItem], snapshot_path: pathlib.Path
) -> list[Shot]:
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as exec:
        future_to_vi = {
            vi.url: exec.submit(make_video_snapshots, vi.path, snapshot_path)
            for vi in video_items
        }
        return [
            Shot(
                name=vi.name,
                video_item=vi,
                snapshots=future_to_vi[vi.url].result(),
                links=[
                    VideoLink(name="potplayer", url=f"potplayer://{vi.url}"),
                    VideoLink(name="browser", url=vi.url),
                ],
            )
            for vi in video_items
        ]


def make_video_snapshots(
    video_path: pathlib.Path, output: pathlib.Path
) -> list[Snapshot]:
    log.info("make_video_snapshots. %s", video_path)
    hash = get_file_hash(video_path)
    snapshot_path = output / pathlib.Path(hash)
    if snapshot_path.exists():
        log.info("snapshot exsits. skip. %s", snapshot_path)
        return [
            Snapshot(url=path_to_url(pathlib.Path(p), BASE_URL), path=pathlib.Path(p))
            for p in snapshot_path.iterdir()
        ]
    else:
        log.info("making snapshots. %s", video_path.name)
        snapshot_path.mkdir()
        paths = snapshot.make_snapshot(str(video_path), str(snapshot_path), width=250)
        return [
            Snapshot(url=path_to_url(pathlib.Path(p), BASE_URL), path=pathlib.Path(p))
            for p in paths
        ]


def dump_jsonfile(snapshots: list[Shot], output_path: pathlib.Path):
    ss_list = [s.shots_dict() for s in snapshots]
    json_str = json.dumps(ss_list, indent=4)
    json_filepath = output_path / "snapshots.json"
    with json_filepath.open("w") as f:
        f.write(json_str)
    js_filepath = output_path / "snapshots.js"
    with js_filepath.open("w") as f:
        f.write(f"const videos={json_str}")


def get_file_hash(filepath: pathlib.Path) -> str:
    hash_filename = filepath.parent / f"{filepath.stem}.hash"
    if hash_filename.exists():
        with hash_filename.open("r") as f:
            result = f.read()
            log.info("cached hash:%s", result)
            return result

    log.info("hash file not exist. %s", hash_filename)
    log.info("openning video file:%s", filepath)
    with filepath.open("rb") as f:
        data = f.read(CHUNK_SIZE)
        sha256 = hashlib.sha256()
        sha256.update(data)
        result = sha256.hexdigest()
        with hash_filename.open("w") as f:
            f.write(result)
            return result


if __name__ == "__main__":
    main()
