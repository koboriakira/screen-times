# 開発ガイド

## プロジェクト構成

```
screenocr-logger/
├── README.md                          # ユーザー向けドキュメント
├── ARCHITECTURE.md                    # 技術決定記録（PDR）
├── DEVELOPMENT.md                     # このファイル
├── LICENSE
├── .gitignore
├── pyproject.toml                     # Python プロジェクト設定
├── requirements.txt                   # 依存ライブラリ
├── scripts/
│   ├── screenshot_ocr.py              # メイン処理スクリプト
│   ├── screenshot.py                  # スクリーンショット取得モジュール
│   ├── ocr.py                         # OCR処理モジュール
│   ├── jsonl_manager.py               # JSONLファイル管理モジュール（NEW）
│   ├── split_jsonl.py                 # 手動分割コマンド（NEW）
│   ├── screenshot_window.applescript  # AppleScript（アクティブ窓取得）
│   └── setup_launchd.sh               # launchd エージェント設定スクリプト
├── config/
│   └── com.screenocr.logger.plist     # launchd 設定テンプレート
├── tests/
│   ├── test_screenshot.py
│   ├── test_ocr.py
│   ├── test_jsonl.py
│   └── test_jsonl_manager.py          # JSONLマネージャーのテスト（NEW）
└── docs/
    ├── troubleshooting.md
    ├── performance.md
    └── security.md
```

## スクリプト概要

### `scripts/screenshot_ocr.py` （メイン処理）

**機能：**
1. AppleScript 経由でアクティブウインドウ名を取得
2. `screencapture` コマンドでスクリーンショット取得
3. Vision Framework で OCR 処理
4. 結果を日付ベースのJSONLファイルに追記（朝5時基準）
5. 一時ファイル削除

**実行例：**
```bash
python3 scripts/screenshot_ocr.py
```

**環境変数：**
- `DEBUG_KEEP_IMAGES=1` - スクリーンショット画像を削除しない（デバッグ用）
- `CAPTURE_REGION="x,y,w,h"` - キャプチャ領域を指定（例：`"0,0,1920,1080"`）

**エラーハンドリング：**
- OCR 処理がタイムアウト（30秒以上）→ エラーログに記録、スキップ
- アクティブウインドウ取得失敗 → "Unknown" に置換
- 権限不足 → stderr に出力、終了コード 1

### `scripts/jsonl_manager.py` （JSONLファイル管理）

**機能：**
1. 朝5時を基準とした実効日付の計算
2. 日付ベースの自動ファイル分割
3. タスクIDベースの手動ファイル分割
4. メタデータの書き込み
5. レコードの追記

**主要なクラス：**
- `JsonlManager`: JSONLファイルの管理を行うクラス
  - `get_effective_date()`: 朝5時基準の実効日付を取得
  - `get_jsonl_path()`: JSONLファイルのパスを取得
  - `write_metadata()`: メタデータを書き込み
  - `append_record()`: レコードを追記
  - `get_current_jsonl_path()`: 現在使用すべきパスを取得（状態管理を含む）
  - `_get_current_task_file()`: 状態ファイルから現在のタスクファイル情報を取得
  - `_set_current_task_file()`: 状態ファイルに現在のタスクファイル情報を保存
  - `_clear_current_task_file()`: 状態ファイルをクリア

**日付判定ロジック：**
```python
# 5時より前は前日として扱う
if timestamp.hour < 5:
    effective_date = timestamp - timedelta(days=1)
else:
    effective_date = timestamp
```

**状態管理：**
- 状態ファイル: `~/.screenocr_logs/.current_jsonl`
- タスクファイルが設定されている間は、そのファイルにログを記録
- 日付が変わると（実効日付が異なると）、自動的に日付ベースのファイルに切り替え
- タスクファイルが削除された場合も、日付ベースのファイルに切り替え

### `scripts/split_jsonl.py` （手動分割コマンド）

**機能：**
1. タスクの説明を受け取る
2. タスクIDを生成
3. 新しいJSONLファイルを作成
4. メタデータを1行目に書き込み

**実行例：**
```bash
# タスクを開始
python scripts/split_jsonl.py "新機能の実装作業"

# 出力例
✓ 新しいJSONLファイルを作成しました: /Users/user/.screenocr_logs/2025-12-28_--_143045.jsonl
  タスク: 新機能の実装作業
  タスクID: --
  実効日付: 2025-12-28

このファイルに今後のログが記録されます。
日付が変わると（朝5時を過ぎると）、自動的に日付ベースのファイルに切り替わります。

# 日付ベースのファイルに戻す
python scripts/split_jsonl.py --clear
# または
python scripts/split_jsonl.py
```

**コマンドライン引数：**
- `description`: タスクの説明（オプション、省略すると日付ベースに戻る）
- `--base-dir`: ログディレクトリのベースパス（オプション）
- `--clear`: 明示的に日付ベースのファイルに戻す（オプション）

### `scripts/screenshot_window.applescript` （補助）

**機能：**
- 現在のアクティブウインドウアプリケーション名を取得

**実行例：**
```bash
osascript scripts/screenshot_window.applescript
```

**出力例：**
```
VS Code
```

### `scripts/setup_launchd.sh` （セットアップ）

**機能：**
1. plist ファイルをテンプレートからコピー
2. パスを実際の環境に置き換え
3. `~/Library/LaunchAgents/` に配置
4. launchd に登録
5. 初回実行

**実行例：**
```bash
./scripts/setup_launchd.sh
```

**内部処理：**
```bash
# 1. plist コピー
cp config/com.screenocr.logger.plist ~/Library/LaunchAgents/

# 2. パス置換
sed -i '' "s|{SCRIPT_PATH}|$(pwd)/scripts/screenshot_ocr.py|g" ~/Library/LaunchAgents/com.screenocr.logger.plist

# 3. launchd 登録
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist

# 4. 初回テスト実行
python3 scripts/screenshot_ocr.py
```

### `scripts/rotate_logs.py` （オプション）

**機能：**
- JSONL ファイルをローテーション（月単位）
- 過去ログを圧縮

**実行例：**
```bash
python3 scripts/rotate_logs.py
```

**処理内容：**
```
~/.screenocr_logger.jsonl       → ~/.screenocr_logger.2025-12.jsonl
                                → ~/.screenocr_logger.2025-12.jsonl.gz (圧縮)
新しいファイルを作成開始
```

## 設定ファイル

### `config/com.screenocr.logger.plist`

launchd エージェント設定テンプレート。以下をカスタマイズ可能：

```xml
<key>StartInterval</key>
<integer>60</integer>  <!-- 実行間隔（秒） -->

<key>StandardOutPath</key>
<string>/tmp/screenocr.log</string>  <!-- 標準出力ログ -->

<key>StandardErrorPath</key>
<string>/tmp/screenocr_error.log</string>  <!-- エラーログ -->
```

## 開発フロー

### 1. 開発環境セットアップ

```bash
# リポジトリクローン
git clone <repository_url>
cd screenocr-logger

# Python 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存ライブラリインストール
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2. ローカルテスト

```bash
# メイン処理の手動実行
python3 scripts/screenshot_ocr.py

# ユニットテスト実行
pytest tests/

# コードフォーマット（Black）
black scripts/ tests/

# 型チェック（mypy）
mypy scripts/
```

### 3. デバッグ

```bash
# デバッグモード（画像ファイル保持）
DEBUG_KEEP_IMAGES=1 python3 scripts/screenshot_ocr.py

# ログ確認
tail -f /tmp/screenocr.log
tail -f /tmp/screenocr_error.log

# JSONL ファイル確認
cat ~/.screenocr_logger.jsonl | head -5
```

### 4. 本番環境へのデプロイ

```bash
# セットアップスクリプト実行
./scripts/setup_launchd.sh

# launchd ログ確認
log stream --predicate 'process == "python3"' --level debug

# 運用確認
launchctl list | grep screenocr
```

## テスト戦略

### ユニットテスト

```python
# tests/test_vision_ocr.py
def test_ocr_empty_image():
    """空のスクリーンショットに対応"""
    result = vision_ocr(image_path)
    assert result == ""

def test_ocr_long_text():
    """長いテキストを正しく抽出"""
    result = vision_ocr(image_path)
    assert len(result) > 1000

# tests/test_jsonl_operations.py
def test_append_to_jsonl():
    """JSONL に正しく追記"""
    append_to_jsonl("test text", timestamp)
    with open(JSONL_PATH) as f:
        last_line = f.readlines()[-1]
    assert json.loads(last_line)["text"] == "test text"

def test_jsonl_encoding():
    """日本語を含む JSONL の正しい エンコーディング"""
    append_to_jsonl("テスト", timestamp)
    with open(JSONL_PATH, encoding='utf-8') as f:
        assert "テスト" in f.read()
```

### 統合テスト

```bash
# 1時間の自動実行テスト
DEBUG=1 python3 scripts/screenshot_ocr.py  # 手動実行 1回
sleep 3600  # 1時間待機
# ログ確認・検証

# パフォーマンステスト
time python3 scripts/screenshot_ocr.py  # 実行時間計測
```

## トラブルシューティング（開発者向け）

### AppleScript 動作確認

```bash
osascript scripts/screenshot_window.applescript
# 出力例: "VS Code"
```

### Vision Framework テスト

```python
python3 -c "
from Foundation import NSURL
from Vision import VNRecognizeTextRequest
print('Vision Framework: OK')
"
```

### screencapture テスト

```bash
screencapture -x /tmp/test.png
ls -la /tmp/test.png
```

### JSONL 追記テスト

```python
python3 -c "
import json
from datetime import datetime

record = {
    'timestamp': datetime.now().isoformat(),
    'window': 'Test',
    'text': 'Hello World',
    'text_length': 11
}

with open('/tmp/test.jsonl', 'a') as f:
    f.write(json.dumps(record, ensure_ascii=False) + '\n')

with open('/tmp/test.jsonl') as f:
    print(f.read())
"
```

## パフォーマンス最適化

### プロファイリング

```bash
python3 -m cProfile -s cumtime scripts/screenshot_ocr.py > profile.txt
cat profile.txt
```

### メモリ使用量確認

```bash
python3 -m memory_profiler scripts/screenshot_ocr.py
```

## CI/CD パイプライン

### Ubuntu CI (テスト・コード品質チェック)

`.github/workflows/ci.yml` でPython 3.9-3.12のマトリックステスト、black/flake8/mypy/pytestを実行。

### macOS Build (パッケージビルド検証)

`.github/workflows/build.yml` でmacOS環境でのビルド・インストール・動作確認を実行。

### TestPyPI 自動公開

`.github/workflows/publish-test.yml` でmainブランチへのマージ時にTestPyPIへ自動公開。

#### TestPyPI APIトークンの設定

1. **TestPyPIアカウント作成**
   - https://test.pypi.org/ でアカウント登録

2. **APIトークン生成**
   - Account Settings → API tokens
   - "Add API token" でプロジェクト用トークン作成

3. **GitHub Secretsに登録**
   - リポジトリ Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: 生成したトークン（`pypi-`で始まる文字列）

#### TestPyPIからのインストール

```bash
# TestPyPIからインストール（依存関係はPyPIから取得）
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            screen-times

# 動作確認
screenocr --help
```

#### バージョン管理の注意点

TestPyPIでは同じバージョン番号は1度しかアップロードできません。開発版は以下のような形式を推奨：

```toml
# pyproject.toml
version = "0.1.0"  # 本番リリース用
# または
version = "0.1.1.dev1"  # 開発版
```

## 貢献ガイドライン

1. フィーチャーブランチを作成
2. コミットメッセージは英語で簡潔に
3. テストを追加・更新
4. `black`，`flake8` でフォーマット
5. プルリクエストを作成

---

質問や問題がある場合は Issue を作成してください。
