# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ScreenOCR LoggerはmacOS上でスクリーンショットを自動取得してVision FrameworkでOCR処理し、JSONL形式でログを記録するシステムです。

## テスト・リンター実行

```bash
# 全テスト実行（カバレッジ付き）
pytest tests/ --cov=scripts --cov-report=term --cov-report=html

# コードフォーマット・型チェック・リンター
black scripts/ tests/
mypy scripts/
flake8 scripts/ tests/
```

詳細なコマンドリファレンスは `docs/commands.md` を参照。

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
6. **ファサードパターン**: 複雑な処理をシンプルなインターフェースで提供

### データフロー
1. launchdが毎分scripts/screenshot_ocr.pyを実行
2. AppleScript経由でアクティブウィンドウ名取得
3. screencaptureコマンドでスクリーンショット取得
4. Vision FrameworkでOCR処理
5. 結果をJSONL形式でObsidian Vault内のアカウント別ディレクトリに追記
6. 画像ファイルを削除

### JSONL保存先
デフォルトの保存先は Obsidian Vault 内のアカウント別ディレクトリ:
```
{OBSIDIAN_VAULT_PATH}/screenocr_logs/{macOSアカウント名}/
```
- 未設定時のVaultパス: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault/`
- アカウント名は `getpass.getuser()` で自動取得

### 設定ファイル
- `pyproject.toml`: Python依存関係とツール設定（Black、mypy、pytest設定を含む）
- `requirements.txt`: 実行時依存関係
- `setup.cfg`: pytest、カバレッジ設定
- `config/com.screenocr.logger.plist`: launchd設定テンプレート
- `setup_launchd.sh`: 初回セットアップスクリプト（.venv/bin/python必須）

### 重要な環境変数
- `OBSIDIAN_VAULT_PATH="/path/to/vault"`: Obsidian Vaultパスの指定（未設定時はデフォルトパス）
- `DEBUG_KEEP_IMAGES=1`: デバッグ用に画像を保持
- `CAPTURE_REGION="x,y,w,h"`: キャプチャ領域の制限
- `JSONL_PATH="/path/to/log.jsonl"`: ログファイルパス指定

## 開発時の注意点

### セキュリティ考慮事項
- スクリーンに表示される全テキストを記録するため、パスワードや機密情報も含まれる可能性
- ログファイルの適切な管理とアクセス制御が重要

### macOS特有の制約
- GUIスクリーンショット取得にはユーザーセッションが必須（cronでは動作しない）
- アクセシビリティ権限とスクリーン録画権限が必要
- launchdはスリープ時に自動停止する
