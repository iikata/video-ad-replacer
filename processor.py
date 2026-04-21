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


def trim_video(input_path: str, output_path: str, keep_frames: int, fps: float) -> None:
    duration = keep_frames / fps
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            output_path,
        ],
        capture_output=True,
        check=True,
    )


def concat_videos(video1_path: str, video2_path: str, output_path: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(f"file '{video1_path}'\n")
        f.write(f"file '{video2_path}'\n")
        list_path = f.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_path,
                "-c", "copy",
                output_path,
            ],
            capture_output=True,
            check=True,
        )
    finally:
        os.unlink(list_path)
