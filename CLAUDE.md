# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ScreenOCR LoggerはmacOS上でスクリーンショットを自動取得してVision FrameworkでOCR処理し、JSONL形式でログを記録するシステムです。

## 主なコマンド

### 開発環境セットアップ
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

### テスト・リンター実行
```bash
# 全テスト実行（カバレッジ付き）
pytest tests/ --cov=scripts --cov-report=term --cov-report=html

# HTMLカバレッジレポート表示
open htmlcov/index.html

# 個別テストファイル実行
pytest tests/test_ocr.py -v
pytest tests/test_screenshot.py -v
pytest tests/test_jsonl.py -v

# コードフォーマット・型チェック・リンター
black scripts/ tests/
mypy scripts/
flake8 scripts/ tests/
```

### 手動実行・検証
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

### launchd管理コマンド
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

### デバッグ・プロファイリング
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

## アーキテクチャの特徴

### 技術スタック
- **メイン言語**: Python 3.8+
- **OCR処理**: macOSのVision Framework（pyobjc経由）
- **データ形式**: JSONL（JSON Lines）
- **定期実行**: launchd
- **補助スクリプト**: AppleScript（アクティブウィンドウ取得用）

### システム設計の重要な特徴
1. **オフライン完結**: Vision Frameworkによりネットワーク不要
2. **プライバシー重視**: スクリーンショット画像は処理後即削除
3. **軽量データ**: テキストのみをJSONL形式で蓄積（年間約400-500MB）
4. **macOS最適化**: Apple Siliconで高速動作（1-2秒/回）
5. **タイムアウト保護**: 5秒でOCR処理をタイムアウト
6. **ファサードパターン**: 複雑な処理をシンプルなインターフェースで提供

### データフロー
1. launchdが毎分scripts/screenshot_ocr.pyを実行
2. AppleScript経由でアクティブウィンドウ名取得
3. screencaptureコマンドでスクリーンショット取得
4. Vision FrameworkでOCR処理
5. 結果をJSONL形式で~/.screenocr_logger.jsonlに追記
6. 画像ファイルを削除

### 設定ファイル
- `pyproject.toml`: Python依存関係とツール設定（Black、mypy、pytest設定を含む）
- `requirements.txt`: 実行時依存関係
- `setup.cfg`: pytest、カバレッジ設定
- `config/com.screenocr.logger.plist`: launchd設定テンプレート
- `setup_launchd.sh`: 初回セットアップスクリプト（.venv/bin/python必須）

### ファサードクラスの使用方法

`ScreenOCRLogger`クラスは、スクリーンショット取得、OCR処理、ログ記録の一連の処理をシンプルなインターフェースで提供します。

#### 基本的な使用方法
```python
from screen_ocr_logger import ScreenOCRLogger

# デフォルト設定で使用
logger = ScreenOCRLogger()
result = logger.run()

# 結果を確認
if result.success:
    print(f"成功: {result.text_length} 文字を記録")
    print(f"保存先: {result.jsonl_path}")
else:
    print(f"失敗: {result.error}")

# 古いスクリーンショットをクリーンアップ
deleted_count = logger.cleanup()
print(f"{deleted_count} ファイルを削除")
```

#### カスタム設定での使用
```python
from pathlib import Path
from screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig

# カスタム設定を作成
config = ScreenOCRConfig(
    screenshot_dir=Path("/custom/screenshots"),
    timeout_seconds=10,
    screenshot_retention_hours=48,
    verbose=True  # 詳細ログを出力
)

# カスタム設定でロガーを初期化
logger = ScreenOCRLogger(config)
result = logger.run()
```

#### 設定オプション
- `screenshot_dir`: スクリーンショット保存先ディレクトリ（デフォルト: `/tmp/screen-times`）
- `timeout_seconds`: OCRタイムアウト時間（デフォルト: 30秒）
- `screenshot_retention_hours`: スクリーンショット保持期間（デフォルト: 72時間）
- `verbose`: 詳細ログ出力の有効化（デフォルト: False）

#### 実行結果（ScreenOCRResult）
- `success`: 処理が成功したかどうか
- `timestamp`: 実行時刻
- `window_name`: アクティブウィンドウ名
- `screenshot_path`: スクリーンショットファイルパス
- `text`: OCR処理結果のテキスト
- `text_length`: テキストの文字数
- `jsonl_path`: ログファイルパス
- `error`: エラーメッセージ（失敗時）

### 重要な環境変数
- `DEBUG_KEEP_IMAGES=1`: デバッグ用に画像を保持
- `CAPTURE_REGION="x,y,w,h"`: キャプチャ領域の制限
- `JSONL_PATH="/path/to/log.jsonl"`: ログファイルパス指定

## 開発時の注意点

### セキュリティ考慮事項
- スクリーンに表示される全テキストを記録するため、パスワードや機密情報も含まれる可能性
- ログファイルの適切な管理とアクセス制御が重要
- 機密アプリ使用時の一時停止機能の検討

### パフォーマンス考慮事項
- Vision FrameworkはApple Siliconで最適化されているが、古いIntel Macでは処理が遅い可能性
- 毎分実行がブロックされないよう、5秒のタイムアウト設定が重要
- JSONL形式により大量ログでも効率的にストリーム処理可能

### macOS特有の制約
- GUIスクリーンショット取得にはユーザーセッションが必須（cronでは動作しない）
- アクセシビリティ権限とスクリーン録画権限が必要
- launchdはスリープ時に自動停止する