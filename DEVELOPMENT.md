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
│   ├── screenshot_window.applescript  # AppleScript（アクティブ窓取得）
│   ├── setup_launchd.sh               # launchd エージェント設定スクリプト
│   ├── analyze_logs.py                # ログ分析ツール（オプション）
│   └── rotate_logs.py                 # ログローテーション（オプション）
├── config/
│   └── com.screenocr.logger.plist     # launchd 設定テンプレート
├── tests/
│   ├── test_screenshot_ocr.py
│   ├── test_vision_ocr.py
│   └── test_jsonl_operations.py
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
4. 結果を JSONL に追記
5. 一時ファイル削除

**実行例：**
```bash
python3 scripts/screenshot_ocr.py
```

**環境変数：**
- `DEBUG_KEEP_IMAGES=1` - スクリーンショット画像を削除しない（デバッグ用）
- `CAPTURE_REGION="x,y,w,h"` - キャプチャ領域を指定（例：`"0,0,1920,1080"`）
- `JSONL_PATH="/path/to/log.jsonl"` - ログファイルパスの指定

**エラーハンドリング：**
- OCR 処理がタイムアウト（5秒以上）→ エラーログに記録、スキップ
- アクティブウインドウ取得失敗 → "Unknown" に置換
- 権限不足 → stderr に出力、終了コード 1

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

### `scripts/analyze_logs.py` （オプション）

**機能：**
- JSONL ログを集計・分析
- 日次レポート生成

**実行例：**
```bash
python3 scripts/analyze_logs.py --date 2025-12-28
python3 scripts/analyze_logs.py --week
python3 scripts/analyze_logs.py --month
```

**出力例：**
```
=== Daily Activity Report: 2025-12-28 ===

Active Windows:
  VS Code           (360 min, 30%)
  Slack             (180 min, 15%)
  Chrome            (240 min, 20%)
  ...

Top Keywords:
  Python, Django, testing, deployment, ...

Total Capture Count: 1440
Average Text Length: 234 chars
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

## CI/CD パイプライン（今後）

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt && pip install -e ".[dev]"
      - run: black --check scripts/ tests/
      - run: flake8 scripts/ tests/
      - run: mypy scripts/
      - run: pytest tests/
```

## 貢献ガイドライン

1. フィーチャーブランチを作成
2. コミットメッセージは英語で簡潔に
3. テストを追加・更新
4. `black`，`flake8` でフォーマット
5. プルリクエストを作成

---

質問や問題がある場合は Issue を作成してください。
