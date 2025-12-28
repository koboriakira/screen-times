#!/bin/bash

###############################################################################
# ScreenOCR Logger - launchd セットアップスクリプト
#
# 機能：
# 1. launchd エージェント（plist）の設定
# 2. 正しいパスへの配置
# 3. launchd への登録
# 4. 初回テスト実行
#
# 使用方法：
#   ./scripts/setup_launchd.sh
###############################################################################

set -e  # エラー時に終了

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

###############################################################################
# 前提チェック
###############################################################################

log_info "前提条件をチェック中..."

# macOS の確認
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "このスクリプトは macOS でのみ動作します"
    exit 1
fi

# Python 3 の確認
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 がインストールされていません"
    exit 1
fi

log_success "Python 3: $(python3 --version)"

# リポジトリディレクトリの確認
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT_PATH="$SCRIPT_DIR/screenshot_ocr.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    log_error "メインスクリプトが見つかりません: $SCRIPT_PATH"
    exit 1
fi

log_success "リポジトリパス: $REPO_DIR"

###############################################################################
# 依存ライブラリのインストール確認
###############################################################################

log_info "Python 依存ライブラリをチェック中..."

python3 << 'EOF'
try:
    import pyobjc
    from Foundation import NSURL
    from Vision import VNRecognizeTextRequest
    from Cocoa import NSScreen
    print("✓ Vision Framework: OK")
except ImportError as e:
    print(f"✗ エラー: {e}")
    print("以下のコマンドでインストールしてください:")
    print("  pip install -r requirements.txt")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    log_error "依存ライブラリが不足しています"
    log_error "以下のコマンドを実行してください:"
    echo "  pip install -r $REPO_DIR/requirements.txt"
    exit 1
fi

###############################################################################
# plist ファイルの設定
###############################################################################

log_info "launchd 設定ファイルを準備中..."

# launchd エージェントディレクトリ
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="com.screenocr.logger.plist"
PLIST_SOURCE="$REPO_DIR/config/$PLIST_FILE"
PLIST_DEST="$LAUNCHD_DIR/$PLIST_FILE"

# ディレクトリが存在しない場合は作成
if [ ! -d "$LAUNCHD_DIR" ]; then
    log_info "$LAUNCHD_DIR を作成中..."
    mkdir -p "$LAUNCHD_DIR"
fi

# plist がない場合は新規作成
if [ ! -f "$PLIST_SOURCE" ]; then
    log_warning "テンプレート plist が見つかりません。新規作成します"
    mkdir -p "$REPO_DIR/config"
    
    cat > "$PLIST_SOURCE" << 'PLIST_TEMPLATE'
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
        <string>{SCRIPT_PATH}</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>StandardOutPath</key>
    <string>/tmp/screenocr.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/screenocr_error.log</string>
    <key>SessionCreate</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST_TEMPLATE
    
    log_success "plist テンプレートを作成: $PLIST_SOURCE"
fi

# plist をコピー（既存の場合はバックアップ）
if [ -f "$PLIST_DEST" ]; then
    BACKUP="$PLIST_DEST.bak.$(date +%Y%m%d_%H%M%S)"
    log_warning "既存の plist をバックアップ: $BACKUP"
    cp "$PLIST_DEST" "$BACKUP"
fi

# テンプレートから置換して生成
log_info "plist ファイルを設定中..."
sed "s|{SCRIPT_PATH}|$SCRIPT_PATH|g" "$PLIST_SOURCE" > "$PLIST_DEST"

log_success "plist ファイルをインストール: $PLIST_DEST"

###############################################################################
# launchd 登録
###############################################################################

log_info "launchd エージェントに登録中..."

# 既に登録されている場合はアンロード
if launchctl list | grep -q "com.screenocr.logger"; then
    log_warning "既に登録されています。アンロード中..."
    launchctl unload "$PLIST_DEST" || true
    sleep 1
fi

# launchd に登録
launchctl load "$PLIST_DEST"

if launchctl list | grep -q "com.screenocr.logger"; then
    log_success "launchd エージェントを登録しました"
else
    log_error "launchd 登録に失敗しました"
    exit 1
fi

###############################################################################
# 初回テスト実行
###############################################################################

log_info "初回テスト実行を実行中..."
echo "（画面が暗くなります）"

python3 "$SCRIPT_PATH"

if [ $? -eq 0 ]; then
    log_success "初回テスト実行に成功しました"
else
    log_warning "初回実行にエラーが発生しました。ログを確認してください"
fi

###############################################################################
# 完了メッセージ
###############################################################################

echo ""
log_success "セットアップが完了しました"
echo ""
echo "=== ScreenOCR Logger がセットアップされました ==="
echo ""
echo "📋 ログファイル:"
echo "   標準出力: /tmp/screenocr.log"
echo "   エラー出力: /tmp/screenocr_error.log"
echo ""
echo "📊 ログデータ:"
echo "   JSONL: $HOME/.screenocr_logger.jsonl"
echo ""
echo "🔧 管理コマンド:"
echo "   有効化: launchctl load $PLIST_DEST"
echo "   無効化: launchctl unload $PLIST_DEST"
echo "   状態確認: launchctl list | grep screenocr"
echo ""
echo "📖 詳細は README.md を参照してください"
echo ""
