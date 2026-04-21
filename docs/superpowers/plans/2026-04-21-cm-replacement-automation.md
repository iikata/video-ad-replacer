# CM差し替え自動化マシーン 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Targetフォルダ内の全MP4動画の末尾から指定フレーム数をカットし、新しい広告MP4を結合して出力するMac用GUIアプリを作る

**Architecture:** Python + tkinter GUIで3フォルダ/ファイルパスとカットフレーム数を受け付け、processor.pyがffmpegを呼び出して各動画を処理する。処理は別スレッドで実行してGUIをブロックしない。

**Tech Stack:** Python 3.14, tkinter（要 `brew install python-tk@3.14`）, ffmpeg（要 `brew install ffmpeg`）, pytest（テスト用）

---

## ファイル構成

| ファイル | 責務 |
|---------|------|
| `main.py` | エントリーポイント。Appを起動する |
| `app.py` | tkinter GUIクラス。ウィジェット構築・ユーザー操作ハンドリング |
| `processor.py` | ffmpegラッパー。フレーム数取得・トリム・結合・1本処理のオーケストレーション |
| `tests/test_processor.py` | processor.pyの単体テスト |

---

## Task 1: プロジェクトセットアップ

**Files:**
- Create: `main.py`
- Create: `app.py`
- Create: `processor.py`
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: 依存ライブラリのインストール確認**

```bash
brew install python-tk@3.14
pip3 install pytest
```

Expected: エラーなし

- [ ] **Step 2: ファイルを作成**

```bash
cd "/Users/myhome/CM差し替え自動化マシーン"
touch main.py app.py processor.py requirements.txt
mkdir -p tests && touch tests/__init__.py tests/test_processor.py
```

- [ ] **Step 3: requirements.txtに記載**

`requirements.txt`:
```
pytest
```

- [ ] **Step 4: gitリポジトリを初期化してコミット**

```bash
cd "/Users/myhome/CM差し替え自動化マシーン"
git init
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
git add .
git commit -m "chore: initial project setup"
```

---

## Task 2: processor.py — ffmpeg検出と動画情報取得

**Files:**
- Modify: `processor.py`
- Modify: `tests/test_processor.py`

- [ ] **Step 1: テストを書く**

`tests/test_processor.py`:
```python
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
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
cd "/Users/myhome/CM差し替え自動化マシーン"
python3 -m pytest tests/test_processor.py -v
```

Expected: `ImportError` または `ModuleNotFoundError`

- [ ] **Step 3: processor.pyに実装**

`processor.py`:
```python
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
```

- [ ] **Step 4: テストがパスすることを確認**

```bash
python3 -m pytest tests/test_processor.py -v
```

Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add processor.py tests/test_processor.py
git commit -m "feat: add check_ffmpeg and get_video_info"
```

---

## Task 3: processor.py — トリムと結合

**Files:**
- Modify: `processor.py`
- Modify: `tests/test_processor.py`

- [ ] **Step 1: テストを追記**

`tests/test_processor.py` の末尾に追加:
```python
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
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
python3 -m pytest tests/test_processor.py -v
```

Expected: 2 tests fail with `ImportError`

- [ ] **Step 3: processor.pyに実装を追加**

`processor.py` の末尾に追加:
```python

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
```

- [ ] **Step 4: テストがパスすることを確認**

```bash
python3 -m pytest tests/test_processor.py -v
```

Expected: 6 passed

- [ ] **Step 5: コミット**

```bash
git add processor.py tests/test_processor.py
git commit -m "feat: add trim_video and concat_videos"
```

---

## Task 4: processor.py — process_single_video オーケストレーター

**Files:**
- Modify: `processor.py`
- Modify: `tests/test_processor.py`

- [ ] **Step 1: テストを追記**

`tests/test_processor.py` の末尾に追加:
```python
from processor import process_single_video


def test_process_single_video_returns_output_path():
    with patch("processor.get_video_info") as mock_info, \
         patch("processor.trim_video") as mock_trim, \
         patch("processor.concat_videos") as mock_concat, \
         patch("processor.tempfile.TemporaryDirectory") as mock_tmp:
        mock_info.return_value = {"frame_count": 900, "fps": 30.0}
        mock_tmp.return_value.__enter__ = lambda s: "/tmp/fake"
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        result = process_single_video(
            target_path="/videos/lecture_001.mp4",
            ad_path="/ads/new_ad.mp4",
            output_dir="/output",
            cut_frames=300,
        )
        assert result == "/output/ad_updated_lecture_001.mp4"


def test_process_single_video_raises_when_cut_exceeds_total():
    with patch("processor.get_video_info") as mock_info:
        mock_info.return_value = {"frame_count": 100, "fps": 30.0}
        with pytest.raises(ValueError, match="カットフレーム数"):
            process_single_video(
                target_path="input.mp4",
                ad_path="ad.mp4",
                output_dir="/output",
                cut_frames=200,
            )
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
python3 -m pytest tests/test_processor.py -v
```

Expected: 2 tests fail with `ImportError`

- [ ] **Step 3: processor.pyに実装を追加**

`processor.py` の末尾に追加:
```python

def process_single_video(
    target_path: str,
    ad_path: str,
    output_dir: str,
    cut_frames: int,
    progress_callback=None,
) -> str:
    target = Path(target_path)
    output_filename = f"ad_updated_{target.name}"
    output_path = str(Path(output_dir) / output_filename)

    info = get_video_info(target_path)
    keep_frames = info["frame_count"] - cut_frames

    if keep_frames <= 0:
        raise ValueError(
            f"カットフレーム数({cut_frames})が総フレーム数({info['frame_count']})以上です"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        trimmed_path = str(Path(tmpdir) / "trimmed.mp4")
        trim_video(target_path, trimmed_path, keep_frames, info["fps"])
        concat_videos(trimmed_path, ad_path, output_path)

    if progress_callback:
        progress_callback(target.name, output_filename)

    return output_path
```

- [ ] **Step 4: テストがパスすることを確認**

```bash
python3 -m pytest tests/test_processor.py -v
```

Expected: 8 passed

- [ ] **Step 5: コミット**

```bash
git add processor.py tests/test_processor.py
git commit -m "feat: add process_single_video orchestrator"
```

---

## Task 5: app.py — GUIレイアウト

**Files:**
- Modify: `app.py`

- [ ] **Step 1: app.pyを実装**

`app.py`:
```python
import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
from pathlib import Path
from processor import check_ffmpeg, process_single_video


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CM差し替え自動化マシーン")
        self.resizable(False, False)
        self._build_widgets()
        self._check_ffmpeg_on_start()

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 5}

        # --- フォルダ / ファイル選択エリア ---
        fields = [
            ("target_dir",  "Targetフォルダ",  "dir"),
            ("ad_file",     "新規広告MP4",       "file"),
            ("output_dir",  "出力先フォルダ",    "dir"),
        ]
        self._vars = {}
        for attr, label, kind in fields:
            frame = tk.Frame(self)
            frame.pack(fill="x", **pad)
            tk.Label(frame, text=label, width=14, anchor="w").pack(side="left")
            var = tk.StringVar()
            self._vars[attr] = var
            tk.Entry(frame, textvariable=var, width=50).pack(side="left", padx=4)
            tk.Button(
                frame, text="選択",
                command=lambda k=kind, v=var: self._browse(k, v)
            ).pack(side="left")

        # --- フレーム数入力 ---
        frame_f = tk.Frame(self)
        frame_f.pack(fill="x", **pad)
        tk.Label(
            frame_f,
            text="前の広告のフレーム数（例: 1800）",
            anchor="w",
        ).pack(side="left")
        self._cut_frames_var = tk.StringVar(value="1800")
        tk.Entry(frame_f, textvariable=self._cut_frames_var, width=8).pack(side="left", padx=8)

        # --- 実行ボタン ---
        self._run_btn = tk.Button(self, text="実行", width=20, command=self._run)
        self._run_btn.pack(pady=8)

        # --- ログエリア ---
        tk.Label(self, text="ログ:", anchor="w").pack(fill="x", padx=10)
        self._log = scrolledtext.ScrolledText(self, height=14, width=70, state="disabled")
        self._log.tag_config("error", foreground="red")
        self._log.tag_config("success", foreground="green")
        self._log.pack(padx=10, pady=(0, 10))

    def _browse(self, kind: str, var: tk.StringVar):
        if kind == "dir":
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=[("MP4ファイル", "*.mp4")])
        if path:
            var.set(path)

    def _log_write(self, message: str, tag: str = ""):
        self._log.config(state="normal")
        self._log.insert("end", message + "\n", tag)
        self._log.see("end")
        self._log.config(state="disabled")

    def _check_ffmpeg_on_start(self):
        if not check_ffmpeg():
            self._log_write(
                "⚠ ffmpegが見つかりません。brew install ffmpeg を実行してください。",
                "error",
            )
            self._run_btn.config(state="disabled")

    def _validate_inputs(self) -> tuple[bool, str]:
        target = self._vars["target_dir"].get()
        ad = self._vars["ad_file"].get()
        output = self._vars["output_dir"].get()
        cut = self._cut_frames_var.get()

        if not target or not Path(target).is_dir():
            return False, "Targetフォルダを選択してください"
        if not ad or not Path(ad).is_file():
            return False, "新規広告MP4を選択してください"
        if not output or not Path(output).is_dir():
            return False, "出力先フォルダを選択してください"
        if not cut.isdigit() or int(cut) <= 0:
            return False, "フレーム数は正の整数を入力してください"
        return True, ""

    def _run(self):
        ok, msg = self._validate_inputs()
        if not ok:
            self._log_write(f"⚠ {msg}", "error")
            return

        target_dir = self._vars["target_dir"].get()
        ad_file = self._vars["ad_file"].get()
        output_dir = self._vars["output_dir"].get()
        cut_frames = int(self._cut_frames_var.get())

        mp4_files = sorted(Path(target_dir).glob("*.mp4"))
        if not mp4_files:
            self._log_write("⚠ Targetフォルダにmp4ファイルが見つかりません", "error")
            return

        self._run_btn.config(state="disabled")
        self._log_write(f"処理開始: {len(mp4_files)}本")

        def worker():
            for i, mp4 in enumerate(mp4_files, 1):
                self._log_write(f"[{i}/{len(mp4_files)}] 処理中: {mp4.name} ...")
                try:
                    out = process_single_video(
                        str(mp4), ad_file, output_dir, cut_frames
                    )
                    self._log_write(f"  ✓ → {Path(out).name}", "success")
                except Exception as e:
                    self._log_write(f"  ✗ エラー: {e}", "error")
            self._log_write("完了!")
            self._run_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()
```

- [ ] **Step 2: GUIが起動できることを確認**

```bash
cd "/Users/myhome/CM差し替え自動化マシーン"
python3 -c "from app import App; print('import OK')"
```

Expected: `import OK`

- [ ] **Step 3: コミット**

```bash
git add app.py
git commit -m "feat: add tkinter GUI"
```

---

## Task 6: main.py — エントリーポイント

**Files:**
- Modify: `main.py`

- [ ] **Step 1: main.pyを実装**

`main.py`:
```python
from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

- [ ] **Step 2: アプリが起動することを確認**

```bash
cd "/Users/myhome/CM差し替え自動化マシーン"
python3 main.py
```

Expected: GUIウィンドウが表示される。ffmpegは既にインストール済みなのでログエリアは空欄

- [ ] **Step 3: 全テストが通ることを確認**

```bash
python3 -m pytest tests/ -v
```

Expected: 8 passed

- [ ] **Step 4: 最終コミット**

```bash
git add main.py
git commit -m "feat: complete CM replacement automation app"
```
