# CM差し替え自動化マシーン 設計ドキュメント

**日付:** 2026-04-21

## 概要

リベ大YouTube動画の末尾広告（CM）を一括差し替えするMac用GUIアプリ。
Targetフォルダ内の全MP4動画に対して、末尾から指定フレーム数をカットし、新しい広告MP4を結合して出力する。

## 技術スタック

- **言語:** Python 3.x（Mac標準搭載）
- **GUI:** tkinter（Python標準ライブラリ）
- **動画処理:** ffmpeg（要 `brew install ffmpeg`）
- **外部Pythonライブラリ:** なし

## ファイル構成

```
CM差し替え自動化マシーン/
├── main.py          # エントリーポイント・GUI起動
├── app.py           # tkinter GUIクラス
├── processor.py     # ffmpegを使った動画処理ロジック
└── requirements.txt # 依存ライブラリ記載（今回は空）
```

## GUI仕様

| 要素 | 内容 |
|------|------|
| Targetフォルダ | フォルダ選択ダイアログ |
| 新規広告MP4 | ファイル選択ダイアログ（.mp4のみ） |
| 出力先フォルダ | フォルダ選択ダイアログ |
| カットフレーム数 | 数値入力欄。ラベルに「前の広告のフレーム数（例: 1800）」と表示してガイドする |
| 実行ボタン | 処理中はグレーアウト（二重実行防止） |
| ログエリア | 1本ずつ進捗をリアルタイム表示、エラーは赤文字 |

## 処理ロジック

### 出力ファイル名

```
ad_updated_{元ファイル名}.mp4
```

例: `lecture_001.mp4` → `ad_updated_lecture_001.mp4`

### ffmpegコマンド

**ステップ1: 総フレーム数取得**
```bash
ffprobe -v error -select_streams v:0 -count_packets \
  -show_entries stream=nb_read_packets \
  -of csv=p=0 input.mp4
```

**ステップ2: 末尾カット（再エンコードなし）**
```bash
ffmpeg -i input.mp4 -frames:v {総フレーム数 - カットフレーム数} \
  -c copy trimmed_tmp.mp4
```

**ステップ3: 広告と結合（再エンコードなし）**
```bash
ffmpeg -i "concat:trimmed_tmp.mp4|ad.mp4" -c copy output.mp4
```

中間ファイルはシステムのtempディレクトリに作成し、処理完了後に自動削除。

## エラー処理

| ケース | 対応 |
|--------|------|
| ffmpegが未インストール | 起動時に検出してエラーメッセージ表示 |
| カットフレーム数 > 総フレーム数 | その動画をスキップしてログに警告 |
| ffmpegがエラー終了 | ログに赤文字表示して次の動画へ続行 |

## 制約・前提

- 対象動画フォーマット: MP4のみ
- 新規広告: 1ファイルを全Targetに共通適用
- 実行環境: macOS
- カットフレーム数は全動画共通の固定値
