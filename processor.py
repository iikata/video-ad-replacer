import subprocess
import tempfile
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
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    duration = float(result.stdout.strip())
    return {"duration": duration}


def trim_video(input_path: str, output_path: str, keep_duration: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(keep_duration),
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            output_path,
        ],
        capture_output=True,
        check=True,
    )


def concat_videos(video1_path: str, video2_path: str, output_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video1_path,
            "-i", video2_path,
            "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            output_path,
        ],
        capture_output=True,
        check=True,
    )


def process_single_video(
    target_path: str,
    ad_path: str,
    output_dir: str,
    cut_seconds: float,
    progress_callback=None,
) -> str:
    target = Path(target_path)
    output_filename = f"ad_updated_{target.name}"
    output_path = str(Path(output_dir) / output_filename)

    info = get_video_info(target_path)
    keep_duration = info["duration"] - cut_seconds

    if keep_duration <= 0:
        raise ValueError(
            f"カット秒数({cut_seconds}秒)が動画の長さ({info['duration']:.1f}秒)以上です"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        trimmed_path = str(Path(tmpdir) / "trimmed.mp4")
        trim_video(target_path, trimmed_path, keep_duration)
        concat_videos(trimmed_path, ad_path, output_path)

    if progress_callback:
        progress_callback(target.name, output_filename)

    return output_path
