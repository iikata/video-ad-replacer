import subprocess
import tempfile
import os
from pathlib import Path


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_info(path: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-count_packets",
            "-show_entries", "stream=avg_frame_rate,nb_read_packets",
            "-of", "csv=p=0",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    parts = result.stdout.strip().split(",")
    fps_num, fps_den = parts[0].split("/")
    fps = float(fps_num) / float(fps_den)
    frame_count = int(parts[1])
    return {"frame_count": frame_count, "fps": fps}
