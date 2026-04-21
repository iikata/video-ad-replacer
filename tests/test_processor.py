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


from processor import trim_video, concat_videos


def test_trim_video_calls_ffmpeg_with_correct_duration():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        trim_video("input.mp4", "out.mp4", keep_frames=870, fps=29.97)
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-t" in args
        duration_index = args.index("-t") + 1
        assert abs(float(args[duration_index]) - 29.03) < 0.1


def test_concat_videos_creates_list_file_and_calls_ffmpeg():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        concat_videos("trimmed.mp4", "ad.mp4", "output.mp4")
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-f" in args
        assert "concat" in args
