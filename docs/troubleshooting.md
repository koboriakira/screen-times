# トラブルシューティング

ScreenOCR Loggerの使用中に発生する可能性のある問題と解決方法をまとめています。

## 目次
- [スクリーンショット取得エラー](#スクリーンショット取得エラー)
- [OCR処理の問題](#ocr処理の問題)
- [launchd登録の問題](#launchd登録の問題)
- [権限エラー](#権限エラー)
- [ログファイルが見つからない](#ログファイルが見つからない)

---

## スクリーンショット取得エラー

### 症状
```
Error: Failed to capture screenshot
```

### 原因と解決方法

#### 1. 画面収録権限が付与されていない

**確認方法：**
```bash
# ターミナルで手動実行してエラーメッセージを確認
cd /Users/your_username/git/screen-times
.venv/bin/python scripts/screenshot_ocr.py
```

**解決方法：**
1. システム環境設定 → セキュリティとプライバシー → 画面収録
2. ターミナル（または使用しているターミナルアプリ）にチェックを入れる
3. ターミナルを再起動
4. 再度実行して確認

#### 2. ディレクトリの書き込み権限がない

**確認方法：**
```bash
ls -la /tmp/screen-times
```

**解決方法：**
```bash
# ディレクトリを削除して再作成
rm -rf /tmp/screen-times
mkdir -p /tmp/screen-times
chmod 755 /tmp/screen-times
```

#### 3. ディスク容量不足

**確認方法：**
```bash
df -h /tmp
```

**解決方法：**
- 不要なファイルを削除してディスク容量を確保
- スクリーンショットの保持期間を短くする（デフォルト72時間）

---

## OCR処理の問題

### 症状1: OCRが日本語を認識しない

**確認方法：**
```bash
# テスト実行
cd /Users/your_username/git/screen-times
.venv/bin/python scripts/test_ocr.py screen_samples/sample.png
```

**原因：**
- Vision Frameworkの言語設定が正しくない
- macOSのバージョンが古い（10.15未満）

**解決方法：**
1. macOSを最新バージョンにアップデート
2. `scripts/ocr.py`で言語設定を確認：
```python
request.setRecognitionLanguages_(["ja-JP", "en-US"])
```

### 症状2: OCR処理がタイムアウトする

**エラーメッセージ：**
```
TimeoutError: OCR processing timeout
```

**原因：**
- 画像が大きすぎる
- システムリソース不足
- 複雑な日本語テキストの処理

**解決方法：**

1. タイムアウト時間を延長（`scripts/ocr.py`）：
```python
# デフォルト: 30秒
result = perform_ocr(screenshot_path, timeout_seconds=60)  # 60秒に延長
```

2. システムリソースを確認：
```bash
# CPU使用率を確認
top -l 1 | grep "CPU usage"

# メモリ使用状況を確認
vm_stat
```

3. 他のプロセスを停止してリソースを確保

### 症状3: OCR結果が空になる

**確認方法：**
```bash
# ログファイルを確認
tail -n 10 ~/.screenocr_logger.jsonl
```

**原因：**
- 画面に表示されているテキストが少ない
- スクリーンセーバーやロック画面が表示されている
- 画像が真っ黒または真っ白

**解決方法：**
- 正常な動作です。テキストがない場合は空の結果が記録されます
- ログを確認して、text_lengthが0でないエントリを探してください

---

## launchd登録の問題

### 症状1: セットアップスクリプトが失敗する

**エラーメッセージ：**
```
[ERROR] Pythonの仮想環境が見つかりません
```

**解決方法：**
```bash
# 仮想環境を作成
cd /Users/your_username/git/screen-times
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 再度セットアップ
./scripts/setup_launchd.sh
```

### 症状2: エージェントが起動しない

**確認方法：**
```bash
# エージェントの状態を確認
launchctl list | grep screenocr

# エージェントが表示されない場合
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist

# エラーログを確認
cat /tmp/screenocr_error.log
```

**解決方法：**

1. plistファイルの構文チェック：
```bash
plutil -lint ~/Library/LaunchAgents/com.screenocr.logger.plist
```

2. パスが正しいか確認：
```bash
cat ~/Library/LaunchAgents/com.screenocr.logger.plist | grep ProgramArguments -A 3
```

3. エージェントを再登録：
```bash
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### 症状3: エージェントが実行されているのにログが記録されない

**確認方法：**
```bash
# エージェントのPIDを確認
launchctl list | grep screenocr

# 0以外の数字が表示されていれば実行中
# 出力例: 12345  0  com.screenocr.logger
```

**解決方法：**

1. 標準出力・エラー出力を確認：
```bash
cat /tmp/screenocr.log
cat /tmp/screenocr_error.log
```

2. 権限エラーが表示されている場合 → [権限エラー](#権限エラー)を参照

3. ログファイルへの書き込み権限を確認：
```bash
ls -la ~/.screenocr_logger.jsonl
touch ~/.screenocr_logger.jsonl
```

---

## 権限エラー

### アクセシビリティ権限

**エラーメッセージ：**
```
Error: Could not get active window
```

**解決方法：**
1. システム環境設定 → セキュリティとプライバシー → アクセシビリティ
2. ターミナル（または使用しているターミナルアプリ）にチェックを入れる
3. ターミナルを再起動

### 画面収録権限

**エラーメッセージ：**
```
Error: Failed to capture screenshot
screencapture: no file specified
```

**解決方法：**
1. システム環境設定 → セキュリティとプライバシー → 画面収録
2. ターミナル（または使用しているターミナルアプリ）にチェックを入れる
3. ターミナルを再起動
4. launchdエージェントを再起動：
```bash
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### ファイル書き込み権限

**エラーメッセージ：**
```
PermissionError: [Errno 13] Permission denied: '/Users/username/.screenocr_logger.jsonl'
```

**解決方法：**
```bash
# ファイルの権限を確認
ls -la ~/.screenocr_logger.jsonl

# 権限を修正
chmod 644 ~/.screenocr_logger.jsonl

# ホームディレクトリの権限を確認
ls -la ~ | grep screenocr
```

---

## ログファイルが見つからない

### 症状
ログファイル `~/.screenocr_logger.jsonl` が存在しない

### 原因と解決方法

#### 1. まだ一度も実行されていない

**確認方法：**
```bash
# エージェントが登録されているか確認
launchctl list | grep screenocr

# 実行間隔を確認（デフォルト60秒）
cat ~/Library/LaunchAgents/com.screenocr.logger.plist | grep StartInterval
```

**解決方法：**
```bash
# 手動で実行してログを作成
cd /Users/your_username/git/screen-times
.venv/bin/python scripts/screenshot_ocr.py

# ログファイルを確認
ls -la ~/.screenocr_logger.jsonl
```

#### 2. 別のパスに出力されている

**確認方法：**
```bash
# スクリプト内のログファイルパスを確認
grep "screenocr_logger.jsonl" scripts/screenshot_ocr.py

# システム全体で検索
find ~ -name "*screenocr*.jsonl" -type f 2>/dev/null
```

#### 3. エラーで処理が完了していない

**確認方法：**
```bash
# エラーログを確認
cat /tmp/screenocr_error.log

# 手動実行でエラーメッセージを確認
cd /Users/your_username/git/screen-times
.venv/bin/python scripts/screenshot_ocr.py
```

**解決方法：**
- エラーメッセージに応じて、該当するセクションを参照
- 権限エラー → [権限エラー](#権限エラー)
- スクリーンショットエラー → [スクリーンショット取得エラー](#スクリーンショット取得エラー)

---

## よくある質問 (FAQ)

### Q1: スクリーンショットが保存されたままになっている

**A:** デフォルトでは72時間（3日）後に自動削除されます。即座に削除したい場合：

```bash
rm -rf /tmp/screen-times/*
```

### Q2: launchdエージェントを完全に削除したい

**A:** 以下のコマンドを実行：

```bash
# エージェントをアンロード
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist

# plistファイルを削除
rm ~/Library/LaunchAgents/com.screenocr.logger.plist

# ログファイルを削除（任意）
rm ~/.screenocr_logger.jsonl

# スクリーンショットを削除（任意）
rm -rf /tmp/screen-times
```

### Q3: ログファイルのサイズが大きくなりすぎた

**A:** 手動でローテーション：

```bash
# 現在のログをリネーム
mv ~/.screenocr_logger.jsonl ~/.screenocr_logger.$(date +%Y-%m).jsonl

# 圧縮（任意）
gzip ~/.screenocr_logger.$(date +%Y-%m).jsonl

# 新しいログファイルは自動的に作成されます
```

### Q4: 特定の時間帯だけ記録したい

**A:** launchdエージェントをアンロード/ロードで制御：

```bash
# 記録を停止
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist

# 記録を再開
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

または、より高度な制御が必要な場合は、plistファイルの`StartCalendarInterval`を使用して特定の時間帯のみ実行するように設定できます。

---

## サポート

上記の方法で解決しない場合は、以下の情報を添えてIssueを作成してください：

1. macOSのバージョン
```bash
sw_vers
```

2. Pythonのバージョン
```bash
python3 --version
```

3. エラーログ
```bash
cat /tmp/screenocr_error.log
```

4. 実行ログ
```bash
cat /tmp/screenocr.log | tail -n 50
```

5. launchdエージェントの状態
```bash
launchctl list | grep screenocr
```
