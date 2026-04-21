import pytest
from unittest.mock import patch, MagicMock
from processor import check_ffmpeg, get_video_info


def test_check_ffmpeg_returns_true_when_available():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert check_ffmpeg() is True


def test_check_ffmpeg_returns_false_when_not_found():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        assert check_ffmpeg() is False


def test_get_video_info_parses_fps_and_frame_count():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="30000/1001,900\n",
            returncode=0,
        )
        info = get_video_info("test.mp4")
        assert info["frame_count"] == 900
        assert abs(info["fps"] - 29.97) < 0.01


def test_get_video_info_raises_on_ffprobe_error():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.side_effect = Exception("ffprobe failed")
        with pytest.raises(Exception):
            get_video_info("test.mp4")
