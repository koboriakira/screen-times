# ScreenOCR Logger

macOS上で毎分スクリーンショットを取得し、Vision FrameworkでOCR処理して、JSONL形式でアクティビティログを記録するシステムです。

## 概要

**主な機能：**
- 毎分自動でスクリーンショット取得
- アクティブウインドウ名を自動記録
- macOSネイティブの Vision Framework でOCR処理
- JSONL形式で軽量・スケーラブルに蓄積
- 完了後に画像を自動削除

**用途例：**
- 実際の作業時間の可視化
- 日次行動パターン分析
- 生産性向上の自己観察

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

### 3. スクリプトに実行権限を付与

```bash
chmod +x scripts/screenshot_ocr.py
chmod +x scripts/setup_launchd.sh
```

### 4. launchd エージェントを登録

```bash
./scripts/setup_launchd.sh
```

このスクリプトが以下を実行します：
- `plist`ファイルを`~/Library/LaunchAgents/`にコピー
- launchd エージェントを登録
- 初回の定期実行をスケジュール

### 5. 動作確認

```bash
# launchd が正常に登録されたか確認
launchctl list | grep screenocr

# 手動実行でテスト
python3 scripts/screenshot_ocr.py

# ログを確認
tail -f /tmp/screenocr.log
```

## 使用方法

### 自動実行の開始

```bash
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### 自動実行の停止

```bash
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### ログファイルの確認

JSONL形式でログが記録されます：

```bash
cat ~/.screenocr_logger.jsonl | head -10
```

出力例：
```json
{"timestamp": "2025-12-28T14:31:00.123456", "window": "VS Code", "text": "def screenshot_ocr():\n    ...", "text_length": 245}
{"timestamp": "2025-12-28T14:32:00.456789", "window": "Slack", "text": "@akira Hey, how's the project?", "text_length": 28}
```

### 日次レポート生成（オプション）

```bash
python3 scripts/analyze_logs.py --date 2025-12-28
```

## ログフォーマット

### JONLスキーマ

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `timestamp` | string (ISO 8601) | キャプチャ時刻 |
| `window` | string | アクティブウインドウ名 |
| `text` | string | OCR認識テキスト |
| `text_length` | integer | テキストの文字数 |

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
ls -la ~/.screenocr_logger.jsonl
```

存在しない場合は手動実行で生成：

```bash
python3 scripts/screenshot_ocr.py
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
