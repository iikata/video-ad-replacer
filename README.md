# Video Ad Replacer

複数のMP4動画の末尾にある広告を、新しい広告へ一括で差し替えるmacOS向けGUIアプリです。

対象フォルダ内の動画ごとに、末尾から指定秒数をカットして新しい広告動画を結合します。元の動画は変更せず、処理結果を別ファイルとして出力します。

## 主な機能

- フォルダ内にある複数のMP4を一括処理
- 以前の広告動画からカット秒数を自動取得
- 動画処理中の進捗とエラーを画面に表示
- 動画ごとにエラーが起きても、残りの処理を継続
- FFmpegを使った映像・音声のトリムと結合

## 必要なもの

- macOS
- Python 3
- tkinter
- FFmpeg / ffprobe

Homebrewを使用する場合は、次のコマンドで導入できます。

```bash
brew install python-tk@3.14 ffmpeg
```

## インストール

リポジトリをクローンします。

```bash
git clone https://github.com/iikata/video-ad-replacer.git
cd video-ad-replacer
```

テストも実行する場合は、仮想環境を作成して依存パッケージをインストールします。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## 起動方法

```bash
python3 main.py
```

起動時にFFmpegが見つからない場合は、画面に警告が表示され、実行ボタンが無効になります。

## 使い方

1. **Targetフォルダ**で、差し替え対象のMP4が入ったフォルダを選択します。
2. **前の広告MP4**で、現在動画の末尾に付いている広告ファイルを選択します。
3. 自動入力された**カットする秒数**を確認し、必要であれば変更します。
4. **新規広告MP4**で、差し替え後の広告ファイルを選択します。
5. **出力先フォルダ**を選択します。
6. **実行**を押します。

Targetフォルダ直下の `*.mp4` が、ファイル名順に処理されます。サブフォルダ内の動画は対象になりません。

## 出力ファイル

出力ファイル名には、元のファイル名の先頭に `ad_updated_` が付きます。

```text
lecture_001.mp4
└── ad_updated_lecture_001.mp4
```

元の動画は上書きされません。誤って処理済み動画を再処理しないよう、Targetフォルダとは別の出力先フォルダを指定することをおすすめします。

## 動画についての注意事項

- 対応する入力形式はMP4です。
- 対象動画と広告動画には、映像ストリームと音声ストリームの両方が必要です。
- 安定して結合するため、対象動画と新しい広告動画は、解像度や音声設定などをそろえてください。
- カット秒数が対象動画全体の長さ以上の場合、その動画は処理されません。
- 出力映像はH.264（CRF 18）、音声はAACで再エンコードされます。
- 動画の本数や長さによっては、処理に時間がかかります。

## テスト

```bash
python3 -m pytest -v
```

## macOSアプリのビルド

PyInstallerをインストールし、同梱のspecファイルを使用します。

```bash
python3 -m pip install pyinstaller
pyinstaller main.spec
```

ビルド結果は `dist/CM差し替え自動化マシーン.app` に生成されます。

`main.spec` はApple Silicon版Homebrewの `/opt/homebrew/bin/ffmpeg` と `/opt/homebrew/bin/ffprobe` を同梱する設定です。別の場所にインストールしている場合は、ビルド前にパスを変更してください。

## ファイル構成

```text
.
├── main.py          # アプリのエントリーポイント
├── app.py           # tkinterによるGUI
├── processor.py     # FFmpegを使った動画処理
├── main.spec        # PyInstallerのビルド設定
├── requirements.txt # テスト用依存パッケージ
└── tests/           # 単体テスト
```

## ライセンス

このソフトウェアは[GNU General Public License v2.0](LICENSE)で公開されています。

ビルド版には[FFmpeg](https://ffmpeg.org/)が含まれます。FFmpegのライセンスについては、FFmpegプロジェクトの案内を確認してください。
