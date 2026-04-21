import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
from pathlib import Path
from processor import check_ffmpeg, get_video_info, process_single_video


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
            ("old_ad_file", "前の広告MP4",      "old_ad"),
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
        tk.Label(frame_f, text="カットする秒数", anchor="w").pack(side="left")
        self._cut_seconds_var = tk.StringVar(value="")
        tk.Entry(frame_f, textvariable=self._cut_seconds_var, width=8).pack(side="left", padx=8)
        self._seconds_hint = tk.Label(frame_f, text="← 前の広告MP4を選択すると自動入力", fg="gray")
        self._seconds_hint.pack(side="left")

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
        elif kind == "old_ad":
            path = filedialog.askopenfilename(filetypes=[("MP4ファイル", "*.mp4")])
            if path:
                var.set(path)
                self._load_old_ad_frames(path)
            return
        else:
            path = filedialog.askopenfilename(filetypes=[("MP4ファイル", "*.mp4")])
        if path:
            var.set(path)

    def _load_old_ad_frames(self, path: str):
        try:
            info = get_video_info(path)
            seconds = round(info["duration"], 2)
            self._cut_seconds_var.set(str(seconds))
            self._seconds_hint.config(text=f"← {seconds}秒", fg="green")
        except Exception as e:
            self._seconds_hint.config(text=f"← 読み取りエラー: {e}", fg="red")

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
        old_ad = self._vars["old_ad_file"].get()
        ad = self._vars["ad_file"].get()
        output = self._vars["output_dir"].get()
        cut = self._cut_seconds_var.get()

        if not target or not Path(target).is_dir():
            return False, "Targetフォルダを選択してください"
        if not old_ad or not Path(old_ad).is_file():
            return False, "前の広告MP4を選択してください"
        if not ad or not Path(ad).is_file():
            return False, "新規広告MP4を選択してください"
        if not output or not Path(output).is_dir():
            return False, "出力先フォルダを選択してください"
        try:
            if float(cut) <= 0:
                raise ValueError
        except ValueError:
            return False, "秒数は正の数値を入力してください"
        return True, ""

    def _run(self):
        ok, msg = self._validate_inputs()
        if not ok:
            self._log_write(f"⚠ {msg}", "error")
            return

        target_dir = self._vars["target_dir"].get()
        ad_file = self._vars["ad_file"].get()
        output_dir = self._vars["output_dir"].get()
        cut_seconds = float(self._cut_seconds_var.get())

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
                        str(mp4), ad_file, output_dir, cut_seconds
                    )
                    self._log_write(f"  ✓ → {Path(out).name}", "success")
                except Exception as e:
                    self._log_write(f"  ✗ エラー: {e}", "error")
            self._log_write("完了!")
            self._run_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()
