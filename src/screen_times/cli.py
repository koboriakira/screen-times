#!/usr/bin/env python3
"""
ScreenOCR CLI - ScreenOCR Logger の統合管理ツール

launchdエージェントの開始・停止、タスク分割などを統合管理するCLIツール
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from typing import Optional

# ローカルモジュールをインポート
from .jsonl_manager import JsonlManager


# 色定義
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def log_info(message: str):
    """情報メッセージを出力"""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")


def log_warn(message: str):
    """警告メッセージを出力"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")


def log_error(message: str):
    """エラーメッセージを出力"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)


def get_project_root() -> Path:
    """プロジェクトルートディレクトリを取得

    開発環境: src/screen_times/cli.py -> プロジェクトルート
    インストール済み: site-packages/screen_times/cli.py -> ホームディレクトリにフォールバック
    """
    # パッケージのディレクトリ
    package_dir = Path(__file__).parent.absolute()

    # 開発環境かチェック（src/screen_times/cli.pyの場合）
    if package_dir.parent.name == "src":
        # 開発環境: src/screen_times -> src -> プロジェクトルート
        return package_dir.parent.parent

    # インストール済み環境: ホームディレクトリ配下のプロジェクトを探す
    # フォールバック: カレントディレクトリまたはホームディレクトリ
    cwd = Path.cwd()
    if (cwd / ".venv").exists() and (cwd / "pyproject.toml").exists():
        return cwd

    # 最終フォールバック
    return Path.home() / "git" / "screen-times"


def get_plist_path() -> Path:
    """plistファイルのパスを取得"""
    return Path.home() / "Library" / "LaunchAgents" / "com.screenocr.logger.plist"


def get_launchd_label() -> str:
    """launchdラベルを取得"""
    return "com.screenocr.logger"


def check_launchd_status() -> bool:
    """launchdエージェントが実行中かチェック"""
    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True, check=True)
        return get_launchd_label() in result.stdout
    except subprocess.CalledProcessError:
        return False


def start_agent():
    """launchdエージェントを開始"""
    log_info("ScreenOCR Logger を起動します...")

    project_root = get_project_root()
    plist_template = project_root / "config" / "com.screenocr.logger.plist"
    plist_dest = get_plist_path()
    main_script = project_root / "src" / "screen_times" / "screenshot_ocr.py"
    python_path = project_root / ".venv" / "bin" / "python"

    # 前提条件チェック
    if not plist_template.exists():
        log_error(f"plistテンプレートが見つかりません: {plist_template}")
        sys.exit(1)

    if not main_script.exists():
        log_error(f"メインスクリプトが見つかりません: {main_script}")
        sys.exit(1)

    if not python_path.exists():
        log_error(f"Pythonの仮想環境が見つかりません: {python_path}")
        log_info("まず 'pipenv install' を実行してください")
        sys.exit(1)

    # LaunchAgentsディレクトリを作成
    plist_dest.parent.mkdir(parents=True, exist_ok=True)

    # 既存のエージェントをアンロード
    if check_launchd_status():
        log_warn("既存のエージェントを停止します...")
        try:
            subprocess.run(
                ["launchctl", "unload", str(plist_dest)], capture_output=True, check=False
            )
        except Exception:
            pass

    # plistファイルを生成
    log_info("plistファイルを生成中...")
    with open(plist_template, "r") as f:
        template_content = f.read()

    # パスを置換
    plist_content = template_content.replace("{PYTHON_PATH}", str(python_path))
    plist_content = plist_content.replace("{SCRIPT_PATH}", str(main_script))

    with open(plist_dest, "w") as f:
        f.write(plist_content)

    log_info(f"plistファイルを生成しました: {plist_dest}")

    # launchdエージェントをロード
    log_info("launchdエージェントをロード中...")
    try:
        subprocess.run(
            ["launchctl", "load", str(plist_dest)], check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        log_error(f"launchdエージェントのロードに失敗しました: {e.stderr}")
        sys.exit(1)

    # 検証
    if check_launchd_status():
        log_info("✓ ScreenOCR Logger が正常に起動しました")
        print()
        log_info("次のステップ:")
        print("  1. システム環境設定 > セキュリティとプライバシー > 画面収録")
        print("     で、ターミナルまたはPythonに権限を付与してください")
        print()
        print("  2. ログファイルを確認:")
        print("     tail -f ~/.screenocr_logs/$(date +%Y-%m-%d).jsonl")
    else:
        log_error("エージェントの起動確認に失敗しました")
        sys.exit(1)


def stop_agent():
    """launchdエージェントを停止"""
    log_info("ScreenOCR Logger を停止します...")

    plist_dest = get_plist_path()

    if not plist_dest.exists():
        log_warn("plistファイルが見つかりません。エージェントは登録されていません。")
        return

    if not check_launchd_status():
        log_warn("エージェントは実行されていません。")
        return

    # エージェントをアンロード
    try:
        subprocess.run(
            ["launchctl", "unload", str(plist_dest)], check=True, capture_output=True, text=True
        )
        log_info("✓ ScreenOCR Logger を停止しました")
    except subprocess.CalledProcessError as e:
        log_error(f"エージェントの停止に失敗しました: {e.stderr}")
        sys.exit(1)


def split_task(description: Optional[str] = None, clear: bool = False):
    """タスク別にJSONLファイルを分割"""
    try:
        # エージェントが停止している場合は自動起動
        if not check_launchd_status():
            log_warn("エージェントが停止しています。自動的に起動します...")
            try:
                start_agent()
                print()  # 空行を追加して読みやすく
            except SystemExit:
                # start_agent()がsys.exit()を呼ぶ場合があるので捕捉
                log_error("エージェントの起動に失敗しました。タスク分割を中断します。")
                sys.exit(1)

        # JSONLマネージャーの初期化
        jsonl_manager = JsonlManager(base_dir=Path.home())

        # --clear オプションまたは説明なしの場合は日付ベースに戻す
        if clear or not description:
            jsonl_manager._clear_current_task_file()
            timestamp = datetime.now()
            effective_date = jsonl_manager.get_effective_date(timestamp)
            current_path = jsonl_manager.get_current_jsonl_path(timestamp)
            log_info(f"日付ベースのファイルに戻しました: {current_path}")
            print(f"  実効日付: {effective_date.strftime('%Y-%m-%d')}")
            return

        # タスクIDを生成
        def generate_task_id(desc: str) -> str:
            """タスク説明からタスクIDを生成"""
            task_id = desc[:20].replace(" ", "-").replace("　", "-")
            allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
            task_id = "".join(c for c in task_id if c in allowed_chars)
            return task_id or "task"

        task_id = generate_task_id(description)
        timestamp = datetime.now()

        # 新しいJSONLファイルのパスを取得
        jsonl_path = jsonl_manager.get_jsonl_path(timestamp=timestamp, task_id=task_id)

        # メタデータを書き込み
        jsonl_manager.write_metadata(jsonl_path, description, timestamp)

        # 状態ファイルを更新
        effective_date = jsonl_manager.get_effective_date(timestamp)
        jsonl_manager._set_current_task_file(jsonl_path, effective_date.strftime("%Y-%m-%d"))

        log_info(f"新しいJSONLファイルを作成しました: {jsonl_path}")
        print(f"  タスク: {description}")
        print(f"  タスクID: {task_id}")
        print(f"  実効日付: {effective_date.strftime('%Y-%m-%d')}")
        print()
        print("このファイルに今後のログが記録されます。")
        print("日付が変わると（朝5時を過ぎると）、自動的に日付ベースのファイルに切り替わります。")

    except Exception as e:
        log_error(f"タスク分割に失敗しました: {e}")
        sys.exit(1)


def dry_run(merge_threshold: Optional[float] = None):
    """dry-run実行（5秒待機後にOCR処理を実行し、結果を標準出力）

    Args:
        merge_threshold: マージのしきい値（0.0～1.0）
    """
    import json
    from .screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig

    log_info("Dry-runモードで実行します")
    if merge_threshold is not None:
        log_info(f"マージしきい値: {merge_threshold}")
    print()
    print("5秒後にスクリーンショットとOCR処理を実行します...")
    print("任意のウィンドウをアクティブにしてお待ちください。")
    print()

    # カウントダウン
    for i in range(5, 0, -1):
        print(f"  {i}...", flush=True)
        import time

        time.sleep(1)

    print("\n実行中...\n")

    # dry-runモードで実行
    config = ScreenOCRConfig(dry_run=True, verbose=True, merge_threshold=merge_threshold)
    logger = ScreenOCRLogger(config)
    result = logger.run()

    # 結果を表示
    print("\n" + "=" * 60)
    print("DRY-RUN 実行結果")
    print("=" * 60)

    if result.success:
        # JSON形式で表示するデータを構築
        output_data = {
            "timestamp": result.timestamp.isoformat(),
            "window": result.window_name,
            "text": result.text,
            "text_length": result.text_length,
        }

        print(f"\n{Colors.GREEN}✓ 成功{Colors.NC}")
        print(f"\nタイムスタンプ: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ウィンドウ名: {result.window_name}")
        print(f"テキスト長: {result.text_length} 文字")
        print(f"\nスクリーンショット: {result.screenshot_path}")
        print("\nJSONL形式（実際には保存されていません）:")
        print("-" * 60)
        print(json.dumps(output_data, ensure_ascii=False, indent=2))
        print("-" * 60)

        # テキストのプレビュー
        if result.text:
            preview_length = 200
            preview_text = result.text[:preview_length]
            if len(result.text) > preview_length:
                preview_text += "..."
            print("\nテキストプレビュー:")
            print("-" * 60)
            print(preview_text)
            print("-" * 60)
    else:
        print(f"\n{Colors.RED}✗ 失敗{Colors.NC}")
        print(f"エラー: {result.error}")
        sys.exit(1)


def show_status():
    """現在の状態を表示"""
    log_info("=== ScreenOCR Logger ステータス ===")
    print()

    # launchdの状態
    is_running = check_launchd_status()
    status_color = Colors.GREEN if is_running else Colors.YELLOW
    status_text = "実行中" if is_running else "停止中"
    print(f"  launchdエージェント: {status_color}{status_text}{Colors.NC}")

    # plistファイルの存在
    plist_dest = get_plist_path()
    plist_exists = plist_dest.exists()
    print(f"  plistファイル: {'存在' if plist_exists else '未作成'}")
    if plist_exists:
        print(f"    -> {plist_dest}")

    # ログディレクトリ
    log_dir = Path.home() / ".screenocr_logs"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.jsonl"))
        print(f"  ログファイル: {len(log_files)} 個")
        print(f"    -> {log_dir}")

        # 今日のログファイル
        timestamp = datetime.now()
        jsonl_manager = JsonlManager(base_dir=Path.home())
        current_path = jsonl_manager.get_current_jsonl_path(timestamp)
        if current_path.exists():
            size_kb = current_path.stat().st_size / 1024
            print(f"  現在のログ: {current_path.name} ({size_kb:.1f} KB)")
    else:
        print("ログディレクトリ: 未作成")

    print()

    # ヘルプメッセージ
    if is_running:
        print("使用可能なコマンド:")
        print('  screenocr split "タスク名"  - 新しいタスクを開始')
        print("  screenocr stop             - エージェントを停止")
    else:
        print("使用可能なコマンド:")
        print("  screenocr start            - エージェントを開始")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ScreenOCR Logger の統合管理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  screenocr start                 # エージェントを開始
  screenocr stop                  # エージェントを停止
  screenocr split "新機能の実装"   # タスクを分割
  screenocr split --clear         # 日付ベースに戻す
  screenocr status                # 現在の状態を表示
  screenocr dry-run               # テスト実行（JSONLに保存せず結果表示）
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")

    # start コマンド
    subparsers.add_parser("start", help="launchdエージェントを開始")

    # stop コマンド
    subparsers.add_parser("stop", help="launchdエージェントを停止")

    # split コマンド
    split_parser = subparsers.add_parser("split", help="タスク別にJSONLファイルを分割")
    split_parser.add_argument(
        "description", nargs="?", help="タスクの説明（例: '〇〇機能の実装作業'）"
    )
    split_parser.add_argument(
        "--clear",
        action="store_true",
        help="タスクファイルの設定をクリアして、日付ベースのファイルに戻す",
    )

    # status コマンド
    subparsers.add_parser("status", help="現在の状態を表示")

    # dry-run コマンド
    dry_run_parser = subparsers.add_parser(
        "dry-run", help="テスト実行（5秒待機後にOCR処理、結果を標準出力）"
    )
    dry_run_parser.add_argument(
        "--merge-threshold",
        type=float,
        metavar="THRESHOLD",
        help="類似レコードをマージするしきい値（0.0～1.0、デフォルト: マージしない）",
    )

    args = parser.parse_args()

    # コマンドが指定されていない場合はヘルプを表示
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # コマンドを実行
    if args.command == "start":
        start_agent()
    elif args.command == "stop":
        stop_agent()
    elif args.command == "split":
        split_task(args.description, args.clear)
    elif args.command == "status":
        show_status()
    elif args.command == "dry-run":
        merge_threshold = getattr(args, "merge_threshold", None)
        dry_run(merge_threshold=merge_threshold)


if __name__ == "__main__":
    main()
