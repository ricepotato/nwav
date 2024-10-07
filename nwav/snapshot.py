import os
import logging
import shutil
import tempfile
from typing import List
import cv2  # pip install opencv-python

# sudo apt-get install libcblas-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test

log = logging.getLogger(f"nwa.{__name__}")


def make_tmp_jpg_file():
    with tempfile.NamedTemporaryFile(prefix="opencv-tmp-", delete=False) as f:
        tmp_filepath = f.name

    new_tmpfilepath = f"{tmp_filepath}.jpg"
    shutil.move(tmp_filepath, new_tmpfilepath)
    return new_tmpfilepath


def make_snapshot(
    video_filepath: str, out_path: str = "", shot_count: int = 16, width: int = None
) -> List[str]:
    log.info("make snapshot video_filepath=%s", video_filepath)
    cam = cv2.VideoCapture(video_filepath)
    frame_count = cam.get(cv2.CAP_PROP_FRAME_COUNT)
    per_frame = int(frame_count / (shot_count + 1))
    filename = os.path.split(video_filepath)[-1]
    filename = os.path.splitext(filename)[0]
    res = []
    # 가장 앞 프레임 제외
    for idx in range(1, shot_count + 1):
        cam.set(cv2.CAP_PROP_POS_FRAMES, per_frame * idx)
        ret, frame = cam.read()
        if not ret:
            log.warning("read error. ret=%s", ret)
            continue

        if width is not None:
            _, img_width, _ = frame.shape
            ratio = width / img_width
        else:
            ratio = 1

        img_filepath = os.path.join(out_path, f"{idx}.jpg")
        log.info("make snapshot. %s", img_filepath)
        dst = cv2.resize(
            frame, dsize=(0, 0), fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA
        )

        tmp_filepath = make_tmp_jpg_file()
        cv2.imwrite(tmp_filepath, dst)
        shutil.move(tmp_filepath, img_filepath)
        res.append(img_filepath)

    cam.release()
    cv2.destroyAllWindows()
    return res
