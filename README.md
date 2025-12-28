# screen-times

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

macOS上で毎分スクリーンショットを取得し、Vision FrameworkでOCR処理して、JSONL形式でアクティビティログを記録するシステムです。

## 概要

**主な機能：**
- 毎分自動でスクリーンショット取得
- アクティブウインドウ名を自動記録
- macOSネイティブの Vision Framework でOCR処理
- JSONL形式で軽量・スケーラブルに蓄積
- 完了後に画像を自動削除
- 日付ベースの自動ファイル分割（朝5時基準）
- 手動でのタスク別ファイル分割機能

**用途例：**
- 実際の作業時間の可視化
- 日次行動パターン分析
- 生産性向上の自己観察
- タスク別の作業ログ分析

## システム要件

- macOS 10.15+ (Catalina以上)
- Apple Silicon または Intel Mac（Vision Framework対応）
- Python 3.9+
- 管理者権限（launchd登録時）

## インストール

### PyPIからインストール（推奨）

```bash
# pipxを使用（推奨 - コマンドラインツールとして独立環境にインストール）
pipx install screen-times

# または通常のpip
pip install screen-times
```

### GitHubからインストール（開発版）

最新の開発版を使いたい場合：

```bash
# pipxで開発版をインストール
pipx install git+https://github.com/koboriakira/screen-times.git

# または通常のpip
pip install git+https://github.com/koboriakira/screen-times.git
```

### 開発者向けインストール

コードを変更したい場合：

```bash
# リポジトリをクローン
git clone https://github.com/koboriakira/screen-times.git
cd screen-times

# 仮想環境を作成してアクティベート
python3 -m venv .venv
source .venv/bin/activate

# 開発モードでインストール
pip install -e .[dev]
```

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

# エージェントを停止
screenocr stop
```

### タスク別のログ管理

作業を開始するときに、タスク名を指定してログを分割できます：

```bash
# 新しいタスクを開始
screenocr split "機能実装: ユーザー認証"

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

## 詳細設定

実行間隔を変更したい場合は、`~/Library/LaunchAgents/com.screenocr.logger.plist` を編集後、エージェントを再起動してください：

```bash
screenocr stop
screenocr start
```

## セキュリティに関する注意

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
