#!/bin/bash
set -euo pipefail

# ScreenOCR Logger - launchd セットアップスクリプト
# このスクリプトはlaunchdエージェントを自動的にセットアップします

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ファイルパス
PLIST_TEMPLATE="$PROJECT_ROOT/config/com.screenocr.logger.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.screenocr.logger.plist"
MAIN_SCRIPT="$PROJECT_ROOT/scripts/screenshot_ocr.py"
LAUNCHD_LABEL="com.screenocr.logger"

# ログ関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# エラーハンドリング
error_exit() {
    log_error "$1"
    exit 1
}

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."

    # plistテンプレートの存在確認
    if [ ! -f "$PLIST_TEMPLATE" ]; then
        error_exit "plistテンプレートが見つかりません: $PLIST_TEMPLATE"
    fi

    # メインスクリプトの存在確認
    if [ ! -f "$MAIN_SCRIPT" ]; then
        error_exit "メインスクリプトが見つかりません: $MAIN_SCRIPT"
    fi

    # Pythonの存在確認
    if [ ! -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        error_exit "Pythonの仮想環境が見つかりません: $PROJECT_ROOT/.venv"
    fi

    # LaunchAgentsディレクトリの作成
    mkdir -p "$HOME/Library/LaunchAgents"

    log_info "前提条件チェック完了"
}

# 既存のlaunchdエージェントをアンロード
unload_existing() {
    log_info "既存のlaunchdエージェントをチェック中..."

    if launchctl list | grep -q "$LAUNCHD_LABEL"; then
        log_warn "既存のエージェントを停止します..."
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        log_info "既存のエージェントを停止しました"
    fi
}

# plistファイルの生成とコピー
install_plist() {
    log_info "plistファイルをインストール中..."

    # Pythonパスを取得
    PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python"

    # テンプレートを読み込み、パスを置換してコピー
    sed -e "s|{PYTHON_PATH}|$PYTHON_PATH|g" \
        -e "s|{SCRIPT_PATH}|$MAIN_SCRIPT|g" \
        "$PLIST_TEMPLATE" > "$PLIST_DEST"

    log_info "plistファイルをインストールしました: $PLIST_DEST"
}

# launchdエージェントをロード
load_agent() {
    log_info "launchdエージェントをロード中..."

    if launchctl load "$PLIST_DEST"; then
        log_info "launchdエージェントをロードしました"
    else
        error_exit "launchdエージェントのロードに失敗しました"
    fi
}

# セットアップの検証
verify_setup() {
    log_info "セットアップを検証中..."

    # エージェントが登録されているか確認
    if launchctl list | grep -q "$LAUNCHD_LABEL"; then
        log_info "✓ launchdエージェントが正常に登録されました"
    else
        log_warn "launchdエージェントが見つかりません"
        return 1
    fi

    # plistファイルの存在確認
    if [ -f "$PLIST_DEST" ]; then
        log_info "✓ plistファイルが存在します"
    else
        log_warn "plistファイルが見つかりません"
        return 1
    fi

    return 0
}

# テスト実行
test_execution() {
    log_info ""
    log_info "セットアップが完了しました！"
    log_info ""
    log_info "次のステップ:"
    log_info "1. システム環境設定 > セキュリティとプライバシー > 画面収録"
    log_info "   で、ターミナルまたはPythonに権限を付与してください"
    log_info ""
    log_info "2. 手動でテスト実行:"
    log_info "   cd $PROJECT_ROOT"
    log_info "   .venv/bin/python scripts/screenshot_ocr.py"
    log_info ""
    log_info "3. launchdの状態確認:"
    log_info "   launchctl list | grep screenocr"
    log_info ""
    log_info "4. ログファイル確認（日付ベースで自動分割）:"
    log_info "   ls -lh ~/.screenocr_logs/"
    log_info "   tail -f ~/.screenocr_logs/\$(date +%Y-%m-%d).jsonl"
    log_info ""
    log_info "5. タスク別に手動でログを分割する場合:"
    log_info "   cd $PROJECT_ROOT"
    log_info "   .venv/bin/python scripts/split_jsonl.py \"タスクの説明\""
    log_info ""
    log_info "6. エージェントを停止する場合:"
    log_info "   launchctl unload $PLIST_DEST"
    log_info ""
}

# メイン処理
main() {
    log_info "=== ScreenOCR Logger launchd セットアップ ==="
    log_info ""

    check_prerequisites
    unload_existing
    install_plist
    load_agent

    if verify_setup; then
        test_execution
        exit 0
    else
        error_exit "セットアップの検証に失敗しました"
    fi
}

# スクリプト実行
main "$@"
