# ARCHITECTURE.md - Process Decision Records

## 概要

このドキュメントはScreenOCR Loggerの主要な技術選択と、その決定理由を記録します。

---

## PDR-001: Vision Framework の採用

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

macOS上でスクリーンショットのテキスト抽出（OCR）を実現する方法を検討。

### 選択肢

| 方式 | 精度 | 速度 | 費用 | 依存性 |
|-----|------|------|------|--------|
| **Vision Framework** | ★★★★☆ | ★★★★★ | 無料 | macOS標準 |
| Google Cloud Vision | ★★★★★ | ★★★☆☆ | 有料 | ネットワーク |
| Azure Computer Vision | ★★★★★ | ★★★☆☆ | 有料 | ネットワーク |
| Tesseract | ★★★☆☆ | ★★★☆☆ | 無料 | 別途インストール |

### 決定

**Vision Framework を採用**

### 理由

1. **Apple Silicon最適化** - Neural Engine での高速処理（1～2秒/枚）
2. **ネットワーク不要** - オフライン動作で信頼性向上
3. **無料** - ランニングコストなし
4. **OS統合** - 別途ライブラリ導入不要
5. **プライバシー** - ローカル処理で機密情報がインターネット送信されない

### トレードオフ

- 精度はGoogle Vision に劣る（一般的なUIテキストでは実用上問題なし）
- 複雑な書体・手書きに弱い

### 実装

`Vision.VNRecognizeTextRequest` を Python（pyobjc経由）で実装。

---

## PDR-002: JSONL形式でのログ保存

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

毎分生成されるOCRデータを効率的に蓄積・管理する形式を選定。

### 選択肢

| 形式 | スケーラビリティ | 追記性 | 分析性 | ファイルサイズ |
|-----|----------------|-------|-------|---------------|
| **JSONL** | ★★★★★ | ★★★★★ | ★★★★☆ | 中 |
| JSON配列 | ★★☆☆☆ | ★☆☆☆☆ | ★★★★★ | 大 |
| CSV | ★★★★☆ | ★★★★☆ | ★★★★★ | 小 |
| SQLite | ★★★★★ | ★★★★★ | ★★★★★ | 中 |

### 決定

**JSONL形式を採用**

### 理由

1. **追記効率** - ファイル全体を読み込まずに新レコード追加可能
2. **スケーラビリティ** - 1年分（52万レコード）でも400MB程度
3. **ツール互換性** - `jq`、Python、SQL などで容易に処理可能
4. **スキーマ柔軟性** - レコードごとにフィールド追加可能
5. **ストリーム処理** - 大規模ファイルも行単位で処理可能

### 例

```json
{"timestamp": "2025-12-28T14:31:00.123456", "window": "VS Code", "text": "...", "text_length": 245}
{"timestamp": "2025-12-28T14:32:00.456789", "window": "Slack", "text": "...", "text_length": 28}
```

### トレードオフ

- JSON配列より分析が少し複雑（ライン単位の処理）
- SQLiteのようなクエリ言語がない（別途ツールが必要）

### 運用上の考慮

- **ローテーション戦略** - 月ごとにファイル分割推奨（検索性向上）
- **圧縮** - 過去ログはgzip圧縮でストレージ削減
- **バックアップ** - `.jsonl`ファイルをiCloudに自動同期

---

## PDR-003: launchd による定期実行

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

毎分スクリーンショットを取得し、処理を実行する定期実行メカニズムを選定。

### 選択肢

| 方式 | GUI可能 | リソース効率 | 管理性 | 標準性 |
|-----|--------|----------|-------|-------|
| **launchd** | ✓ | ★★★★★ | ★★★★☆ | 標準 |
| cron | ✗ | ★★★★☆ | ★★★☆☆ | 標準 |
| at | ✗ | ★★★☆☆ | ★★☆☆☆ | 標準 |
| 常駐アプリ | ✓ | ★★☆☆☆ | ★★★☆☆ | 非標準 |

### 決定

**launchd （StartInterval方式）を採用**

### 理由

1. **GUI環境必須** - スクリーンショット取得にはユーザーセッション必須
   - cron, at では `Display is not available` エラーになる
2. **ネイティブスケジューラー** - macOS推奨の標準方式
3. **自動ログローテーション** - StandardOutPath設定で対応
4. **管理簡素性** - `launchctl load/unload` で有効化・無効化容易
5. **リソース効率** - macOS が適切なタイミングで実行、スリープ時は自動停止

### 実装

plist ファイル例：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.screenocr.logger</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/scripts/screenshot_ocr.py</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>StandardOutPath</key>
    <string>/tmp/screenocr.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/screenocr_error.log</string>
</dict>
</plist>
```

### トレードオフ

- StartInterval は秒単位のみ（柔軟な時間指定には`StartCalendarInterval`使用）

---

## PDR-004: 言語選択（Python + AppleScript + Bash）

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

以下を統合する実装言語/スクリプト言語を選定：
- アクティブウインドウ情報取得
- スクリーンショット取得
- Vision Framework 経由のOCR処理
- JSONL ログ記録

### 選択肢

| 構成 | 習得度 | パフォーマンス | 保守性 | 相互運用性 |
|-----|-------|------------|-------|----------|
| **Python + AppleScript** | ★★★☆☆ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| 完全Swift | ★★☆☆☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ |
| 完全AppleScript | ★★★★☆ | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ |
| Bash + 各種ユーティリティ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | ★★★★★ |

### 決定

**Python（メイン） + AppleScript（補助） + Bash（統合）**

### 理由

#### Python を主言語に選んだ理由

1. **macOS FW へのアクセス** - `pyobjc` で Vision Framework に直接アクセス可能
2. **JSON/ファイル操作** - 標準ライブラリで充実
3. **習得性** - 本プロジェクト実装者の既存スキル活用
4. **クロスプラットフォーム** - 将来の拡張性（Linux対応等）

#### AppleScript を補助に使う理由

1. **アクティブウインドウ取得** - AppleScript が最もシンプル

   ```applescript
   tell application "System Events"
       set active_app to name of (processes where frontmost is true)
   end tell
   ```

2. **Python での実装は複雑** - Cocoa フレームワークの別途理解が必要

#### Bash を統合層に使う理由

1. **launchd との親和性** - ProgramArguments 配列との相性が良好
2. **スクリーンショット取得** - `screencapture` コマンドの直接実行

### トレードオフ

- 言語混在による学習コスト増
- デバッグが複数言語間で必要
- Python環境構築の初期セットアップ必須

### 将来の最適化案

Apple Silicon の進化に合わせて、完全Swift 実装への移行を検討。その場合：
- パフォーマンス向上（ネイティブコンパイル）
- 依存性削減（Python環境不要）
- IDE 統合（Xcode での開発）

---

## PDR-005: 実行時間制限（Timeout） の設定

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

OCR処理が異常に長時間化した場合、次の毎分実行がブロックされるリスク。

### 決定

**Python スクリプト内で5秒のタイムアウト設定**

### 理由

1. **毎分実行のロック防止** - 処理が遅延してもスケジュール維持
2. **リソース枯渇対策** - 無限ループ防止
3. **実装の簡潔性** - signal ライブラリで1～2行で実装可能

### 実装例

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("OCR timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)  # 5秒タイムアウト

try:
    ocr_result = vision_ocr(screenshot_path)
finally:
    signal.alarm(0)  # タイムアウトキャンセル
```

### トレードオフ

- 5秒以上の処理は失敗（実測平均1～2秒なので実用上問題なし）
- エラーログが増える可能性（正常なログローテーション機構の構築が必須）

---

## PDR-006: スクリーンショット後の画像削除

**決定日:** 2025-12-28  
**ステータス:** 承認

### 課題

毎分スクリーンショットを取得する場合、ディスク容量の急速な消費リスク。

### 決定

**OCR処理完了直後に画像ファイルを削除**

### 理由

1. **ストレージ効率** - 1年分で400～500MB（テキストのみ） vs 100GB+（画像保持時）
2. **プライバシー保護** - 機密情報が画像形式で残らない
3. **処理の簡潔性** - JSONL にテキストが保存されていれば不要

### 実装例

```python
try:
    screenshot_path = take_screenshot()
    ocr_text = vision_ocr(screenshot_path)
    save_to_jsonl(ocr_text)
finally:
    os.remove(screenshot_path)  # 必ず削除
```

### 例外ケース

デバッグ時は環境変数で画像保持を有効化：

```bash
DEBUG_KEEP_IMAGES=1 python3 scripts/screenshot_ocr.py
```

---

## システムアーキテクチャ図

```
┌─────────────────────────────────────────────────┐
│  macOS System                                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  launchd (com.screenocr.logger)                 │
│  ├─ StartInterval: 60 秒                        │
│  └─ Trigger: scripts/screenshot_ocr.py          │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ screenshot_ocr.py (Python)              │   │
│  ├─────────────────────────────────────────┤   │
│  │ 1. AppleScript → アクティブ窓名取得     │   │
│  │ 2. screencapture → 画像取得            │   │
│  │ 3. Vision Framework → OCR 処理         │   │
│  │ 4. JSONL → ログ記録                    │   │
│  │ 5. rm → 画像削除                       │   │
│  └─────────────────────────────────────────┘   │
│                  ↓                              │
│  ~/.screenocr_logger.jsonl (JSONL形式)         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### データフロー

```
┌──────────────┐
│ User Screen  │
└──────┬───────┘
       │ (毎60秒)
       ↓
┌──────────────────────────┐
│ screencapture            │ ← PNG 画像ファイル
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ Vision Framework OCR     │ ← テキスト抽出
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ JSONL Append             │ ← {"timestamp", "window", "text", ...}
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ ~/.screenocr_logger.jsonl                │
│ {ts1, win1, txt1}                        │
│ {ts2, win2, txt2}                        │
│ {ts3, win3, txt3}                        │
│ ...                                      │
└──────────────────────────────────────────┘
```

---

## 今後の拡張考慮事項

### 短期（1～3ヶ月）

- [ ] 日次レポート生成機能
- [ ] 機密情報マスキング（パスワード除外等）
- [ ] 既存ツール連携（Obsidian, Notion）

### 中期（3～6ヶ月）

- [ ] Web ダッシュボード（行動可視化）
- [ ] SQLite への並列出力オプション
- [ ] ローカルLLM との統計分析

### 長期（6～12ヶ月）

- [ ] 完全Swift 実装への移行
- [ ] Linux / Windows 対応
- [ ] エッジデバイス（iPad）対応

---

## 参考資料

- [macOS Vision Framework Documentation](https://developer.apple.com/documentation/vision)
- [launchd.plist Manual](https://www.manpagez.com/man/5/launchd.plist)
- [JSON Lines Format](https://jsonlines.org/)
- [pyobjc Documentation](https://pyobjc.readthedocs.io/)
