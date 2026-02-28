# コマンドリファレンス

## 開発環境セットアップ

```bash
# Python仮想環境の作成（Python 3.14が必要）
python3 -m venv .venv
source .venv/bin/activate

# 基本依存関係のインストール
pip install -r requirements.txt

# 開発用依存関係のインストール（black, mypy, pytest, flake8）
pip install -e ".[dev]"

# launchdエージェントのセットアップ
./setup_launchd.sh
```

## 手動実行・検証

```bash
# メインスクリプトの手動実行
python3 scripts/screenshot_ocr.py

# Vision Framework動作確認
python3 -c "from Foundation import NSURL; from Vision import VNRecognizeTextRequest; print('Vision Framework: OK')"

# AppleScript単体テスト
osascript scripts/screenshot_window.applescript

# screencapture動作テスト
screencapture -x /tmp/test.png && ls -la /tmp/test.png
```

## launchd管理コマンド

```bash
# 自動実行の開始
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist

# 自動実行の停止
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist

# 実行状態の確認
launchctl list | grep screenocr

# ログの確認
tail -f /tmp/screenocr.log
tail -f /tmp/screenocr_error.log
cat ~/.screenocr_logger.jsonl | head -10
```

## デバッグ・プロファイリング

```bash
# デバッグモード（スクリーンショットを保持）
DEBUG_KEEP_IMAGES=1 python3 scripts/screenshot_ocr.py

# パフォーマンス測定
time python3 scripts/screenshot_ocr.py

# CPUプロファイリング
python3 -m cProfile -s cumtime scripts/screenshot_ocr.py > profile.txt

# メモリプロファイリング
python3 -m memory_profiler scripts/screenshot_ocr.py

# launchdログのリアルタイム確認
log stream --predicate 'process == "python3"' --level debug
```

## ファサードクラスの使用方法

`ScreenOCRLogger`クラスは、スクリーンショット取得、OCR処理、ログ記録の一連の処理をシンプルなインターフェースで提供します。

### 基本的な使用方法

```python
from screen_ocr_logger import ScreenOCRLogger

logger = ScreenOCRLogger()
result = logger.run()

if result.success:
    print(f"成功: {result.text_length} 文字を記録")
    print(f"保存先: {result.jsonl_path}")
else:
    print(f"失敗: {result.error}")

deleted_count = logger.cleanup()
print(f"{deleted_count} ファイルを削除")
```

### カスタム設定での使用

```python
from pathlib import Path
from screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig

config = ScreenOCRConfig(
    screenshot_dir=Path("/custom/screenshots"),
    timeout_seconds=10,
    screenshot_retention_hours=48,
    verbose=True
)

logger = ScreenOCRLogger(config)
result = logger.run()
```

### 設定オプション

- `screenshot_dir`: スクリーンショット保存先ディレクトリ（デフォルト: `/tmp/screen-times`）
- `timeout_seconds`: OCRタイムアウト時間（デフォルト: 30秒）
- `screenshot_retention_hours`: スクリーンショット保持期間（デフォルト: 72時間）
- `verbose`: 詳細ログ出力の有効化（デフォルト: False）

### 実行結果（ScreenOCRResult）

- `success`: 処理が成功したかどうか
- `timestamp`: 実行時刻
- `window_name`: アクティブウィンドウ名
- `screenshot_path`: スクリーンショットファイルパス
- `text`: OCR処理結果のテキスト
- `text_length`: テキストの文字数
- `jsonl_path`: ログファイルパス
- `error`: エラーメッセージ（失敗時）
