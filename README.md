# ScreenOCR Logger

macOS上で毎分スクリーンショットを取得し、Vision FrameworkでOCR処理して、JSONL形式でアクティビティログを記録するシステムです。

## 概要

**主な機能：**
- 毎分自動でスクリーンショット取得
- アクティブウインドウ名を自動記録
- macOSネイティブの Vision Framework でOCR処理
- JSONL形式で軽量・スケーラブルに蓄積
- 完了後に画像を自動削除
- **日付ベースの自動ファイル分割（朝5時基準）**
- **手動でのタスク別ファイル分割機能**

**用途例：**
- 実際の作業時間の可視化
- 日次行動パターン分析
- 生産性向上の自己観察
- **タスク別の作業ログ分析**

## システム要件

- macOS 10.15+ (Catalina以上)
- Apple Silicon または Intel Mac（Vision Framework対応）
- Python 3.8+
- 管理者権限（launchd登録時）

## セットアップ

### 1. リポジトリをクローン

```bash
git clone <repository_url>
cd screenocr-logger
```

### 2. 依存ライブラリをインストール

```bash
pip install -r requirements.txt
```

### 3. CLIツールをインストール（推奨）

統合管理ツールをインストールすることで、任意のディレクトリから操作できます：

```bash
chmod +x scripts/install_cli.sh
./scripts/install_cli.sh
```

これにより、`screenocr` コマンドがどこからでも使えるようになります。

### 4. （代替）launchd エージェントを手動セットアップ

CLIツールを使わずに手動でセットアップする場合：

```bash
chmod +x scripts/setup_launchd.sh
./scripts/setup_launchd.sh
```

**セットアップスクリプトの機能：**
- 前提条件の自動チェック（plist、スクリプト、Python環境）
- 既存エージェントの自動アンロード（再インストール時）
- 環境に合わせたplistファイルの自動生成
- launchdエージェントの登録
- セットアップの検証
- 詳細なガイダンスの表示

スクリプトは以下のような出力を行います：

```
[INFO] === ScreenOCR Logger launchd セットアップ ===
[INFO] 前提条件をチェック中...
[INFO] 前提条件チェック完了
[INFO] plistファイルをインストール中...
[INFO] launchdエージェントをロードしました
[INFO] ✓ launchdエージェントが正常に登録されました
[INFO] セットアップが完了しました！
```

### 5. 画面収録権限の付与

**重要：** 初回実行前に画面収録権限を付与してください。

1. システム環境設定 → セキュリティとプライバシー → 画面収録
2. ターミナル（または使用しているターミナルアプリ）にチェックを入れる
3. 必要に応じてターミナルを再起動

### 6. 動作確認

CLIツールを使用する場合：

```bash
# ステータス確認
screenocr status

# エージェントを開始
screenocr start

# ログを確認
tail -f ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl
```

手動セットアップの場合：

```bash
# launchd が正常に登録されたか確認
launchctl list | grep screenocr

# 手動実行でテスト
.venv/bin/python scripts/screenshot_ocr.py

# ログを確認
tail -f ~/.screenocr_logger.jsonl
```

## 使用方法

### CLIツールを使用（推奨）

統合管理ツール `screenocr` を使用すると、簡単に操作できます：

```bash
# エージェントを開始
screenocr start

# エージェントを停止
screenocr stop

# タスク別にログを分割
screenocr split "新機能の実装"

# 日付ベースのファイルに戻す
screenocr split --clear

# 現在の状態を確認
screenocr status
```

### 手動での操作

#### 自動実行の開始

```bash
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

#### 自動実行の停止

```bash
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### ログファイルの確認

JSONL形式でログが日付ごとに記録されます：

```bash
# 今日のログを確認（朝5時基準）
cat ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl | head -10

# すべてのログファイルを一覧表示
ls -lh ~/.screenocr_logs/
```

出力例：
```json
{"timestamp": "2025-12-28T14:31:00.123456", "window": "VS Code", "text": "def screenshot_ocr():\n    ...", "text_length": 245}
{"timestamp": "2025-12-28T14:32:00.456789", "window": "Slack", "text": "@akira Hey, how's the project?", "text_length": 28}
```

### 手動でタスク別にログを分割

#### CLIツールを使用する場合

```bash
# タスクを開始するときに実行
screenocr split "〇〇機能の実装作業"

# 日付ベースのファイルに戻す
screenocr split --clear
```

#### 直接Pythonスクリプトを実行する場合

```bash
# タスクを開始するときに実行
python scripts/split_jsonl.py "〇〇機能の実装作業"
```

これにより、タスクの説明をメタデータとして含む新しいJSONLファイルが作成され、**以降のログはこのファイルに記録されます**：

```bash
# 生成されるファイル例
~/.screenocr_logs/2025-12-28_--_143045.jsonl
```

ファイルの1行目にはメタデータが記録されます：
```json
{"type": "task_metadata", "timestamp": "2025-12-28T14:30:45", "description": "〇〇機能の実装作業", "effective_date": "2025-12-28"}
{"timestamp": "2025-12-28T14:31:00", "window": "VS Code", "text": "...", "text_length": 245}
...
```

**注意事項：**
- タスクファイルへの記録は、日付が変わる（朝5時を過ぎる）まで継続されます
- 日付が変わると自動的に日付ベースのファイルに切り替わります
- 手動で日付ベースのファイルに戻すこともできます：

```bash
# 日付ベースのファイルに戻す
python scripts/split_jsonl.py --clear
# または
python scripts/split_jsonl.py
```

## 開発

### テストの実行

プロジェクトには統合テストが含まれています：

```bash
# 全テストを実行
python -m pytest tests/ -v

# カバレッジレポートを生成
python -m pytest tests/ --cov=scripts --cov-report=term --cov-report=html

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

### JSONLスキーマ

#### 通常のログレコード

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `timestamp` | string (ISO 8601) | キャプチャ時刻 |
| `window` | string | アクティブウインドウ名 |
| `text` | string | OCR認識テキスト |
| `text_length` | integer | テキストの文字数 |

#### メタデータレコード（手動分割時のみ）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `type` | string | "task_metadata" 固定 |
| `timestamp` | string (ISO 8601) | タスク開始時刻 |
| `description` | string | タスクの説明 |
| `effective_date` | string (YYYY-MM-DD) | 実効日付（朝5時基準） |

### ファイル分割ルール

**自動分割（日付ベース）：**
- ファイル名形式: `YYYY-MM-DD.jsonl`
- 朝5時をトリガーとして新しいファイルを作成
- 5時より前の時刻は前日分として扱う
  - 例: 2025-12-28 04:59 → `2025-12-27.jsonl` に記録
  - 例: 2025-12-28 05:00 → `2025-12-28.jsonl` に記録

**手動分割（タスクベース）：**
- ファイル名形式: `YYYY-MM-DD_<task-id>_HHMMSS.jsonl`
- コマンド実行時に新しいファイルを作成
- ファイルの1行目にタスクのメタデータを記録

## トラブルシューティング

### スクリーンショットが取得できない

```
Error: Display is not available
```

**原因：** ユーザーセッションが有効でない  
**解決：** 以下のスクリプトの実行確認

```bash
screencapture -x /tmp/test.png
```

### OCR処理が遅い

Vision Framework の処理時間を確認：

```bash
time python3 scripts/screenshot_ocr.py
```

平均2秒以上かかる場合は、以下を検討：
- `StartInterval`を5分に延長（launchd plist内）
- キャプチャ領域を制限（環境変数`CAPTURE_REGION`で指定可能）

### ログファイルが見つからない

```bash
# 新しいログディレクトリを確認
ls -la ~/.screenocr_logs/

# 今日の日付のファイルを確認（朝5時基準）
ls -la ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl
```

存在しない場合は手動実行で生成：

```bash
python3 scripts/screenshot_ocr.py
```

### 手動分割コマンドの使い方

```bash
# タスクの説明を指定して新しいログファイルを開始
python scripts/split_jsonl.py "新機能の実装"

# 日本語も使用可能
python scripts/split_jsonl.py "バグ修正作業：ログイン機能"
```

## 設定のカスタマイズ

### 実行間隔の変更

`~/Library/LaunchAgents/com.screenocr.logger.plist` を編集：

```xml
<key>StartInterval</key>
<integer>300</integer>  <!-- 300秒 = 5分 -->
```

変更後、launchd を再読み込み：

```bash
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### キャプチャ領域の制限

特定領域のみキャプチャする場合：

```bash
CAPTURE_REGION="0,0,1920,1080" python3 scripts/screenshot_ocr.py
```

## パフォーマンス

### 推定リソース使用量（毎分実行）

- **CPU** - 約1～2秒の処理時間（Apple Silicon）
- **ディスク** - 約400～500MB/年（テキストのみ）
- **メモリ** - 約100MB ピーク

### JSONL ファイルのローテーション

長期運用を想定し、月ごとのローテーション推奨：

```bash
python3 scripts/rotate_logs.py
```

## セキュリティに関する注意

⚠️ **重要** このシステムはスクリーンに表示されたすべてのテキストをOCR記録します。

- **パスワード入力** - マスキングされずに記録される可能性
- **機密情報** - 本番環境の認証トークンなど
- **プライバシー** - 個人情報を含む可能性

**推奨対策：**

1. スクリーンロック時は自動停止
2. 機密アプリ（1Password等）使用時は一時停止
3. ログファイルをディスク暗号化フォルダに配置
4. 定期的にログをアーカイブ・削除

## アーキテクチャ

詳細は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。

## ライセンス

MIT

## 貢献

プルリクエストを歓迎します。
