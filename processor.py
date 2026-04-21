import subprocess
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


def trim_and_concat(
    input_path: str, ad_path: str, output_path: str, keep_duration: float
) -> None:
    filter_complex = (
        f"[0:v]trim=duration={keep_duration},setpts=PTS-STARTPTS[v0];"
        f"[0:a]atrim=duration={keep_duration},asetpts=PTS-STARTPTS[a0];"
        f"[v0][a0][1:v][1:a]concat=n=2:v=1:a=1[v][a]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", ad_path,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast",
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

    trim_and_concat(target_path, ad_path, output_path, keep_duration)

    if progress_callback:
        progress_callback(target.name, output_filename)

    return output_path
