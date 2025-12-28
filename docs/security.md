# セキュリティとプライバシー

ScreenOCR Loggerの使用におけるセキュリティとプライバシーに関する重要な情報です。

## ⚠️ 重要な注意事項

**このツールは画面上のすべてのテキストを記録します。** 以下の情報が含まれる可能性があります：

- パスワードやAPIキー
- 個人情報（メールアドレス、電話番号、住所など）
- 機密文書やソースコード
- プライベートなメッセージやチャット内容
- 財務情報

**使用前に必ずリスクを理解し、適切な対策を講じてください。**

---

## 目次
- [プライバシーリスク](#プライバシーリスク)
- [推奨される対策](#推奨される対策)
- [機密情報の保護](#機密情報の保護)
- [ログファイルの暗号化](#ログファイルの暗号化)
- [一時停止機能](#一時停止機能)
- [セキュリティベストプラクティス](#セキュリティベストプラクティス)

---

## プライバシーリスク

### 1. 画面上のすべてのテキストが記録される

**リスク：**
- パスワード入力画面のOCR
- 機密文書の閲覧内容
- プライベートなチャット内容
- 財務情報や医療情報

**影響範囲：**
```
ブラウザ → ウェブサイトのコンテンツ全て
ターミナル → コマンド履歴、出力結果
エディタ → ソースコード、設定ファイル
チャット → メッセージ内容
```

### 2. ログファイルが平文で保存される

**リスク：**
- `~/.screenocr_logger.jsonl` が誰でも読める
- バックアップ時に機密情報が含まれる
- ファイル共有時の意図しない情報漏洩

**危険な例：**
```bash
# ログファイルを誤って公開
git add ~/.screenocr_logger.jsonl
git push

# クラウドストレージに自動アップロード
Dropbox、iCloud Drive などでホームディレクトリを同期
```

### 3. スクリーンショットが一時保存される

**リスク：**
- `/tmp/screen-times/` に画像が保存（最大72時間）
- システムバックアップに含まれる可能性
- 他のアプリケーションからアクセス可能

### 4. システム権限

このツールは以下の権限を必要とします：

- **画面収録権限:** 画面全体を取得
- **アクセシビリティ権限:** ウィンドウ情報を取得

**リスク：** 権限が悪意のあるコードに悪用される可能性

---

## 推奨される対策

### 1. 機密情報入力時は一時停止

**強く推奨：** パスワードやAPIキーを入力する前に、必ずlaunchdエージェントを停止してください。

```bash
# 記録を一時停止
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist

# パスワード入力やAPIキー設定など...

# 記録を再開
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### 2. ログファイルのアクセス権限を制限

```bash
# 自分だけが読み書き可能に設定
chmod 600 ~/.screenocr_logger.jsonl

# ディレクトリも制限
chmod 700 ~/.screenocr_logger_backups/
```

### 3. 機密性の高い作業時は無効化

```bash
# エージェントを完全に停止
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist

# 再度有効化
launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
```

### 4. 定期的なログのレビューと削除

```bash
# 定期的に古いログを確認して削除
cat ~/.screenocr_logger.jsonl | grep -i "password\|secret\|api"

# 該当行を削除（要注意）
# ログファイル全体を削除する場合
rm ~/.screenocr_logger.jsonl
```

---

## 機密情報の保護

### パスワードマスキング機能の実装

OCR結果から機密情報をフィルタリングするスクリプト：

```python
#!/usr/bin/env python3
"""
機密情報をマスキングするフィルター
"""

import re

def mask_sensitive_data(text: str) -> str:
    """機密情報をマスクする"""
    
    # パスワードパターン
    # 例: password: xxx, Password=xxx
    text = re.sub(
        r'(password|passwd|pwd)[\s:=]+\S+',
        r'\1: ****',
        text,
        flags=re.IGNORECASE
    )
    
    # APIキーパターン
    # 例: api_key: xxxx, token=xxxx
    text = re.sub(
        r'(api[_-]?key|token|secret)[\s:=]+\S+',
        r'\1: ****',
        text,
        flags=re.IGNORECASE
    )
    
    # クレジットカード番号（16桁）
    text = re.sub(
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'XXXX-XXXX-XXXX-XXXX',
        text
    )
    
    # メールアドレス（部分マスク）
    text = re.sub(
        r'\b([a-zA-Z0-9._-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'\1***@\2',
        text
    )
    
    # 電話番号（日本）
    text = re.sub(
        r'\b0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}\b',
        '0XX-XXXX-XXXX',
        text
    )
    
    return text

# 使用例
if __name__ == "__main__":
    test_text = """
    username: john_doe
    password: MySecret123!
    api_key: sk-proj-abc123def456
    credit card: 1234-5678-9012-3456
    email: john.doe@example.com
    phone: 090-1234-5678
    """
    
    print("=== Original ===")
    print(test_text)
    
    print("\n=== Masked ===")
    print(mask_sensitive_data(test_text))
```

### screenshot_ocr.pyに統合

```python
# scripts/screenshot_ocr.py に追加

from mask_sensitive import mask_sensitive_data

# OCR処理後
text = perform_ocr(screenshot_path, timeout_seconds=30)

# 機密情報をマスク
text = mask_sensitive_data(text)

# ログに記録
entry = {
    "timestamp": timestamp,
    "window": window_name,
    "text": text,  # マスク済み
    "text_length": len(text),
}
```

---

## ログファイルの暗号化

### GPGを使用した暗号化

#### 1. GPGキーの作成

```bash
# GPGがインストールされていない場合
brew install gnupg

# 新しいキーペアを作成
gpg --full-generate-key

# RSA and RSA を選択
# キーサイズ: 4096
# 有効期限: 0 (無期限) または任意の期間
# 名前とメールアドレスを入力
# パスフレーズを設定（重要！）
```

#### 2. ログファイルの暗号化スクリプト

```bash
#!/bin/bash
# encrypt_logs.sh

LOG_FILE="$HOME/.screenocr_logger.jsonl"
ENCRYPTED_FILE="$HOME/.screenocr_logger.jsonl.gpg"

# GPGで暗号化
gpg --encrypt --recipient your-email@example.com "$LOG_FILE"

# 元のファイルを削除
rm "$LOG_FILE"

echo "Encrypted: $ENCRYPTED_FILE"
```

#### 3. 復号化

```bash
# 復号化して閲覧
gpg --decrypt ~/.screenocr_logger.jsonl.gpg | less

# ファイルに復号化
gpg --decrypt --output ~/.screenocr_logger.jsonl ~/.screenocr_logger.jsonl.gpg
```

#### 4. 自動暗号化の設定

cronまたはlaunchdで定期的に実行：

```bash
# 毎日深夜に暗号化
crontab -e

# 以下を追加
0 0 * * * /path/to/encrypt_logs.sh
```

### macOS FileVaultの使用

**推奨：** FileVaultでディスク全体を暗号化：

1. システム環境設定 → セキュリティとプライバシー → FileVault
2. "FileVaultを入にする" をクリック
3. 復旧キーを安全に保管

**効果：** ログファイルとスクリーンショットが自動的に暗号化されます。

---

## 一時停止機能

### 簡単なスクリプトでの制御

```bash
#!/bin/bash
# toggle_logger.sh

PLIST="$HOME/Library/LaunchAgents/com.screenocr.logger.plist"

if launchctl list | grep -q "com.screenocr.logger"; then
    echo "Stopping ScreenOCR Logger..."
    launchctl unload "$PLIST"
    echo "✓ Stopped"
else
    echo "Starting ScreenOCR Logger..."
    launchctl load "$PLIST"
    echo "✓ Started"
fi
```

使用方法：
```bash
chmod +x toggle_logger.sh
./toggle_logger.sh  # トグル（停止↔起動）
```

### メニューバーアプリでの制御

より便利な制御には、メニューバーアプリを作成できます：

```python
#!/usr/bin/env python3
"""
メニューバーアプリ（rumps使用）
pip install rumps
"""

import rumps
import subprocess

class ScreenOCRLoggerApp(rumps.App):
    def __init__(self):
        super().__init__("📸", quit_button=None)
        self.plist_path = f"{rumps.os.path.expanduser('~')}/Library/LaunchAgents/com.screenocr.logger.plist"
        self.menu = [
            rumps.MenuItem("Toggle Logger", callback=self.toggle),
            rumps.separator,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self.update_title()
    
    def is_running(self):
        """エージェントが実行中かチェック"""
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True
        )
        return "com.screenocr.logger" in result.stdout
    
    def update_title(self):
        """タイトルを更新"""
        if self.is_running():
            self.title = "📸🟢"  # 実行中: 緑
        else:
            self.title = "📸🔴"  # 停止中: 赤
    
    @rumps.clicked("Toggle Logger")
    def toggle(self, _):
        """エージェントをトグル"""
        if self.is_running():
            subprocess.run(["launchctl", "unload", self.plist_path])
            rumps.notification("ScreenOCR Logger", "Stopped", "Recording paused")
        else:
            subprocess.run(["launchctl", "load", self.plist_path])
            rumps.notification("ScreenOCR Logger", "Started", "Recording resumed")
        self.update_title()

if __name__ == "__main__":
    app = ScreenOCRLoggerApp()
    app.run()
```

### キーボードショートカットでの制御

Automatorを使用：

1. Automator.app を開く
2. 新規 → クイックアクション
3. "シェルスクリプトを実行" を追加
4. スクリプト内容:
```bash
if launchctl list | grep -q "com.screenocr.logger"; then
    launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist
    osascript -e 'display notification "Recording stopped" with title "ScreenOCR Logger"'
else
    launchctl load ~/Library/LaunchAgents/com.screenocr.logger.plist
    osascript -e 'display notification "Recording started" with title "ScreenOCR Logger"'
fi
```
5. 保存（例: "Toggle ScreenOCR Logger"）
6. システム環境設定 → キーボード → ショートカット → サービス
7. "Toggle ScreenOCR Logger" にショートカットを割り当て（例: ⌘⇧L）

---

## セキュリティベストプラクティス

### 1. 最小権限の原則

必要最小限の権限のみを付与：

```bash
# 画面収録権限を確認
tccutil reset ScreenCapture
```

### 2. ログの定期削除

```bash
# 30日以上前のログを自動削除
find ~/.screenocr_logger*.jsonl -mtime +30 -delete
```

### 3. バックアップからの除外

```bash
# Time Machineから除外
tmutil addexclusion ~/.screenocr_logger.jsonl
tmutil addexclusion /tmp/screen-times/
```

### 4. .gitignore に追加

```bash
# プロジェクトルートの .gitignore
echo "*.screenocr_logger.jsonl" >> ~/.gitignore_global
git config --global core.excludesfile ~/.gitignore_global
```

### 5. 機密情報検出スクリプト

```bash
#!/bin/bash
# check_sensitive.sh

echo "Checking for sensitive information in logs..."

# パスワード
grep -i "password" ~/.screenocr_logger.jsonl && echo "⚠️ Password found!"

# APIキー
grep -i "api.key\|token" ~/.screenocr_logger.jsonl && echo "⚠️ API key found!"

# クレジットカード
grep -E "\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b" ~/.screenocr_logger.jsonl && echo "⚠️ Credit card found!"

echo "Check complete."
```

### 6. ログの匿名化

個人を特定できる情報を削除：

```python
#!/usr/bin/env python3
"""ログファイルから個人情報を削除"""

import json
import sys

def anonymize_log(input_file, output_file):
    """ログを匿名化"""
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            entry = json.loads(line)
            
            # テキスト内容を削除
            entry.pop('text', None)
            
            # ウィンドウ名を一般化
            if 'window' in entry:
                # "Slack - Confidential Channel" → "Slack"
                entry['window'] = entry['window'].split('-')[0].split('—')[0].strip()
            
            # スクリーンショットパスを削除
            entry.pop('screenshot', None)
            
            json.dump(entry, f_out, ensure_ascii=False)
            f_out.write('\n')

if __name__ == "__main__":
    anonymize_log(
        sys.argv[1] if len(sys.argv) > 1 else "~/.screenocr_logger.jsonl",
        sys.argv[2] if len(sys.argv) > 2 else "~/.screenocr_logger_anonymous.jsonl"
    )
```

---

## 緊急時の対応

### すべてのデータを即座に削除

```bash
#!/bin/bash
# emergency_delete.sh

echo "⚠️ Deleting all ScreenOCR Logger data..."

# エージェントを停止
launchctl unload ~/Library/LaunchAgents/com.screenocr.logger.plist 2>/dev/null

# ログファイルを削除
rm -f ~/.screenocr_logger*.jsonl*

# スクリーンショットを削除
rm -rf /tmp/screen-times/

# plistを削除（再インストールが必要）
rm -f ~/Library/LaunchAgents/com.screenocr.logger.plist

echo "✓ All data deleted."
```

---

## 法的考慮事項

### 日本における注意点

1. **個人情報保護法**
   - 自分自身の情報を記録する場合は問題なし
   - 他人の情報が含まれる場合は注意が必要

2. **プライバシー権**
   - 共有PCでの使用は他人のプライバシーを侵害する可能性

3. **企業での使用**
   - 企業の情報セキュリティポリシーを確認
   - 機密情報や顧客情報の記録は禁止されている可能性
   - 上司や情報セキュリティ部門に相談を推奨

### 推奨事項

1. **個人使用に限定**
2. **企業情報を扱う際は使用しない**
3. **定期的なログのレビューと削除**
4. **暗号化の実施**

---

## まとめ

ScreenOCR Loggerは強力なツールですが、**重大なプライバシーリスク**があります。

**使用前に必ず：**
1. リスクを完全に理解する
2. 機密情報入力時は一時停止する
3. ログファイルを適切に保護する
4. 定期的にログを確認・削除する
5. 暗号化を検討する

**安全に使用するために、このドキュメントを定期的に見直してください。**
