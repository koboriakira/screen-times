# screen-times

[![PyPI version](https://badge.fury.io/py/screen-times.svg)](https://badge.fury.io/py/screen-times)
[![Python Version](https://img.shields.io/pypi/pyversions/screen-times)](https://pypi.org/project/screen-times/)
[![CI](https://github.com/koboriakira/screen-times/workflows/CI/badge.svg)](https://github.com/koboriakira/screen-times/actions/workflows/ci.yml)
[![Build](https://github.com/koboriakira/screen-times/workflows/Build/badge.svg)](https://github.com/koboriakira/screen-times/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

macOS screen activity logger with OCR using Vision Framework

## 概要

**screen-times** は、macOS上で自動的にスクリーンショットを取得し、OCR処理してアクティビティログを記録するツールです。Vision Frameworkを使用した高精度なOCRで、作業内容を自動的にログ化します。

**主な機能：**
- 🖼️ 30秒ごとの自動スクリーンショット取得
- 🔍 Vision FrameworkによるネイティブOCR処理
- 📝 JSONL形式での軽量ログ保存
- 🏷️ タスクベースのログ分割機能
- 🔄 launchdによるバックグラウンド実行
- 🗑️ 処理後の画像自動削除

**用途例：**
- 作業時間の可視化・分析
- 生産性の自己観察
- プロジェクトごとの作業ログ管理

## システム要件

- macOS 10.15+ (Catalina以上)
- Apple Silicon または Intel Mac（Vision Framework対応）
- Python 3.9+
- 管理者権限（launchd登録時）

## インストール

```bash
pip install screen-times
```

### 必要な権限

初回実行時、以下の権限が必要です：

1. **画面収録権限**
   - システム設定 → プライバシーとセキュリティ → 画面収録
   - ターミナル（または実行環境）を許可

2. **アクセシビリティ権限**（アクティブウィンドウ名の取得に必要）
   - システム設定 → プライバシーとセキュリティ → アクセシビリティ
   - ターミナル（または実行環境）を許可

## クイックスタート

### 1. 画面収録権限を付与

**重要：** システム環境設定 → セキュリティとプライバシー → 画面収録 で、ターミナルにチェックを入れてください。

### 2. ScreenOCR Logger を起動

```bash
screenocr start
```

これで毎分自動的にスクリーンショットを取得し、OCR処理してログを記録します。

## 基本的な使い方

### エージェントの操作

```bash
# 現在の状態を確認
screenocr status

# エージェントを起動（自動ログ記録を開始）
screenocr start

# エージェンインストール

```bash
pip install screen-times
```

### 2. 権限を付与

システム設定 → プライバシーとセキュリティ で以下を許可：
- 画面収録
- アクセシビリティ

### 3. 起動

```bash
# エージェントを開始（バックグラウンドで自動ログ記録）
screenocr start

# 状態確認
screenocr status

# 停止
screenocr stop
```

これで30秒ごとに自動的にスクリーンショットを取得し、OCR処理してログを記録します。

ログは `~/.screenocr_logs/` に保存され

# 別のタスクを開始（前のタスクから切り替え）
screenocr split "バグ修正: ログイン画面"

# タスク管理をやめて、日付ベースのログに戻す
screenocr split --clear
```

タスクを指定すると、そのタスク専用のログファイルが作成され、以降のログはそこに記録されます。日付が変わる（朝5時）と自動的に日付ベースに戻ります。

### ログの確認

```bash
# ログディレクトリを確認
ls -lh ~/.screenocr_logs/

# 今日のログを表示（朝5時基準）
cat ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl | head -10

# ログをリアルタイムで監視
tail -f ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl
```

## 開発

### テストの実行

プロジェクトには統合テストが含まれています：

```bash
# 全テストを実行
pytest tests/ -v

# カバレッジレポートを生成
pytest tests/ --cov=src/screen_times --cov-report=term --cov-report=html

# HTMLカバレッジレポートを表示
open htmlcov/index.html
```

### テストの種類

- `tests/test_ocr.py`: OCR処理の統合テスト
  - 簡単なテキスト認識
  - 日本語テキスト認識
  - エラーハンドリング
- `tests/test_screenshot.py`: スクリーンショット取得のテスト
  - 画像取得
  - ディレクトリ作成
  - エラーハンドリング
- `tests/test_jsonl.py`: JSONL操作のテスト
  - 書き込み/読み込み
  - UTF-8エンコーディング
  - 追記操作
- `tests/test_jsonl_manager.py`: JSONLファイル管理のテスト
  - 日付判定ロジック（朝5時基準）
  - 自動・手動分割
  - メタデータ書き込み

## ログフォーマット

JSONL形式でログが記録されます。各行が1つのログエントリです。

### 通常のログ

```json
{"timestamp": "2025-12-28T14:31:00.123456", "window": "VS Code", "text": "def screenshot_ocr():\n    ...", "text_length": 245}
{"timestamp": "2025-12-28T14:32:00.456789", "window": "Slack", "text": "@akira Hey, how's the project?", "text_length": 28}
```

### タスク付きログ（1行目にメタデータ）

```json
{"type": "task_metadata", "timestamp": "2025-12-28T14:30:45", "description": "機能実装: ユーザー認証", "effective_date": "2025-12-28"}
{"timestamp": "2025-12-28T14:31:00", "window": "VS Code", "text": "...", "text_length": 245}
```

### ファイル名規則

- 日付ベース: `2025-12-28.jsonl`
- タスクベース: `2025-12-28_--_143045.jsonl`

**注意：** 日付は朝5時を基準に判定されます（5時より前は前日扱い）。

## トラブルシューティング

### 画面収録権限がない

システム環境設定 → セキュリティとプライバシー → 画面収録 で、ターミナルにチェックを入れてください。

### エージェントが起動しない

```bash
# 状態を確認
screenocr status

# 手動で確認
launchctl list | grep screenocr
```

### ログが記録されない

```bash
# ログディレクトリを確認
ls -la ~/.screenocr_logs/

# エージェントの状態を確認
screenocr status

# エージェントを再起動
screenocr stop
screenocr start
```

## 詳細設のドキュメント

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 技術的な設計と実装の詳細
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 開発者向けガイド
- [RELEASING.md](./RELEASING.md) - リリースプロセス

## ライセンス

MIT License - 詳細は [LICENSE](./LICENSE) を参照してください。

## 貢献

プルリクエスト・Issueを歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feat/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: add amazing feature'`)
4. ブランチにプッシュ (`git push origin feat/amazing-feature`)
5. Pull Requestを作成

## リンク

- **PyPI**: https://pypi.org/project/screen-times/
- **GitHub**: https://github.com/koboriakira/screen-times
- **Issues**: https://github.com/koboriakira/screen-times/issues
⚠️ **重要：** このシステムはスクリーン上のすべてのテキストを記録します。

- パスワードや機密情報がマスキングされずに記録される可能性があります
- 機密情報を扱うときは `screenocr stop` で一時停止してください
- ログファイルは暗号化されたディスクに保存することを推奨します

## その他

詳細は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。

## ライセンス

MIT

## 貢献

プルリクエストを歓迎します。
