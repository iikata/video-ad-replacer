import pytest
from unittest.mock import patch, MagicMock
from processor import check_ffmpeg, get_video_info, trim_video, concat_videos, process_single_video


def test_check_ffmpeg_returns_true_when_available():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert check_ffmpeg() is True


def test_check_ffmpeg_returns_false_when_not_found():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        assert check_ffmpeg() is False


def test_get_video_info_returns_duration():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="60.033333\n", returncode=0)
        info = get_video_info("test.mp4")
        assert abs(info["duration"] - 60.033333) < 0.001


def test_get_video_info_raises_on_ffprobe_error():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.side_effect = Exception("ffprobe failed")
        with pytest.raises(Exception):
            get_video_info("test.mp4")


def test_trim_video_calls_ffmpeg_with_correct_duration():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        trim_video("input.mp4", "out.mp4", keep_duration=30.5)
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-t" in args
        duration_index = args.index("-t") + 1
        assert abs(float(args[duration_index]) - 30.5) < 0.001


def test_concat_videos_uses_filter_complex():
    with patch("processor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        concat_videos("trimmed.mp4", "ad.mp4", "output.mp4")
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-filter_complex" in args
        assert "concat=n=2" in args[args.index("-filter_complex") + 1]


def test_process_single_video_returns_output_path():
    with patch("processor.get_video_info") as mock_info, \
         patch("processor.trim_video"), \
         patch("processor.concat_videos"), \
         patch("processor.tempfile.TemporaryDirectory") as mock_tmp:
        mock_info.return_value = {"duration": 120.0}
        mock_tmp.return_value.__enter__ = lambda s: "/tmp/fake"
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        result = process_single_video(
            target_path="/videos/lecture_001.mp4",
            ad_path="/ads/new_ad.mp4",
            output_dir="/output",
            cut_seconds=30.0,
        )
        assert result == "/output/ad_updated_lecture_001.mp4"


def test_process_single_video_raises_when_cut_exceeds_total():
    with patch("processor.get_video_info") as mock_info:
        mock_info.return_value = {"duration": 20.0}
        with pytest.raises(ValueError, match="カット秒数"):
            process_single_video(
                target_path="input.mp4",
                ad_path="ad.mp4",
                output_dir="/output",
                cut_seconds=30.0,
            )
