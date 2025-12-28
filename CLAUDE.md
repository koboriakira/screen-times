# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ScreenOCR LoggerはmacOS上でスクリーンショットを自動取得してVision FrameworkでOCR処理し、JSONL形式でログを記録するシステムです。

## 主なコマンド

### 開発関連コマンド
```bash
# 依存関係のインストール
pip install -r requirements.txt

# メインスクリプトの手動実行
python3 scripts/screenshot_ocr.py

# launchdエージェントのセットアップ
./setup_launchd.sh

# 開発ツール
black scripts/ tests/    # コードフォーマット
mypy scripts/           # 型チェック
pytest tests/           # ユニットテスト実行
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

### デバッグコマンド
```bash
# デバッグモード（スクリーンショットを保持）
DEBUG_KEEP_IMAGES=1 python3 scripts/screenshot_ocr.py

# OCR処理のパフォーマンス測定
time python3 scripts/screenshot_ocr.py

# メモリプロファイリング
python3 -m memory_profiler scripts/screenshot_ocr.py
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

### データフロー
1. launchdが毎分scripts/screenshot_ocr.pyを実行
2. AppleScript経由でアクティブウィンドウ名取得
3. screencaptureコマンドでスクリーンショット取得
4. Vision FrameworkでOCR処理
5. 結果をJSONL形式で~/.screenocr_logger.jsonlに追記
6. 画像ファイルを削除

### 設定ファイル
- `pyproject.toml`: Python依存関係とツール設定
- `requirements.txt`: 実行時依存関係
- `com.screenocr.logger.plist`: launchd設定テンプレート
- `setup_launchd.sh`: 初回セットアップスクリプト

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