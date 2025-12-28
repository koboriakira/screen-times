#!/bin/bash
# ScreenOCR CLI インストールスクリプト
# このスクリプトはscreenocr CLIツールを~/.local/bin/にインストールします

set -euo pipefail

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# インストール先
INSTALL_DIR="$HOME/.local/bin"
CLI_SCRIPT="$PROJECT_ROOT/scripts/screenocr_cli.py"
CLI_NAME="screenocr"

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

# メイン処理
main() {
    log_info "=== ScreenOCR CLI インストール ==="
    echo

    # CLIスクリプトの存在確認
    if [ ! -f "$CLI_SCRIPT" ]; then
        error_exit "CLIスクリプトが見つかりません: $CLI_SCRIPT"
    fi

    # インストールディレクトリの作成
    mkdir -p "$INSTALL_DIR"
    log_info "インストールディレクトリ: $INSTALL_DIR"

    # シンボリックリンクを作成
    if [ -L "$INSTALL_DIR/$CLI_NAME" ]; then
        log_warn "既存のシンボリックリンクを削除します"
        rm "$INSTALL_DIR/$CLI_NAME"
    elif [ -f "$INSTALL_DIR/$CLI_NAME" ]; then
        log_warn "既存のファイルをバックアップします"
        mv "$INSTALL_DIR/$CLI_NAME" "$INSTALL_DIR/$CLI_NAME.bak"
    fi

    # 実行権限を付与
    chmod +x "$CLI_SCRIPT"

    # シンボリックリンクを作成
    ln -s "$CLI_SCRIPT" "$INSTALL_DIR/$CLI_NAME"
    log_info "シンボリックリンクを作成しました: $INSTALL_DIR/$CLI_NAME"

    # PATHの確認
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        log_warn "$INSTALL_DIR がPATHに含まれていません"
        echo
        echo "以下を ~/.zshrc または ~/.bashrc に追加してください:"
        echo
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo
        echo "追加後、以下を実行してください:"
        echo
        echo "  source ~/.zshrc  # または source ~/.bashrc"
        echo
    else
        log_info "✓ PATHが正しく設定されています"
    fi

    # インストール完了
    echo
    log_info "✓ インストールが完了しました！"
    echo
    echo "使用例:"
    echo "  screenocr start                 # エージェントを開始"
    echo "  screenocr stop                  # エージェントを停止"
    echo "  screenocr split \"新機能の実装\"   # タスクを分割"
    echo "  screenocr status                # 現在の状態を表示"
    echo
    echo "詳細なヘルプ:"
    echo "  screenocr --help"
    echo
}

# スクリプト実行
main "$@"
