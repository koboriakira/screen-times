#!/usr/bin/env python3
"""
JSONL Split Command - 手動でJSONLファイルを分割するコマンド

タスクの概要とともに新しいJSONLファイルを開始します。
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# ローカルモジュールをインポート
from .jsonl_manager import JsonlManager


def generate_task_id(description: str) -> str:
    """
    タスク説明からタスクIDを生成

    Args:
        description: タスクの説明

    Returns:
        タスクID（英数字とハイフン）
    """
    # 簡易的な実装: 最初の20文字を使用し、スペースをハイフンに変換
    task_id = description[:20].replace(" ", "-").replace("　", "-")
    # 使用できない文字を除去
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    task_id = "".join(c for c in task_id if c in allowed_chars)
    return task_id or "task"


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="手動でJSONLファイルを分割し、新しいタスクを開始します。"
    )
    parser.add_argument(
        "description",
        nargs="?",
        help="タスクの説明（例: '〇〇機能の実装作業'）。省略すると日付ベースのファイルに戻ります。",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.home(),
        help="JSONLファイルを保存するベースディレクトリ（デフォルト: ホームディレクトリ）",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="タスクファイルの設定をクリアして、日付ベースのファイルに戻す",
    )

    args = parser.parse_args()

    try:
        # JSONLマネージャーの初期化
        jsonl_manager = JsonlManager(base_dir=args.base_dir)

        # --clear オプションまたは説明なしの場合は日付ベースに戻す
        if args.clear or not args.description:
            jsonl_manager._clear_current_task_file()
            timestamp = datetime.now()
            effective_date = jsonl_manager.get_effective_date(timestamp)
            current_path = jsonl_manager.get_current_jsonl_path(timestamp)
            print(f"✓ 日付ベースのファイルに戻しました: {current_path}")
            print(f"  実効日付: {effective_date.strftime('%Y-%m-%d')}")
            return

        # タスクIDを生成
        task_id = generate_task_id(args.description)
        timestamp = datetime.now()

        # 新しいJSONLファイルのパスを取得
        jsonl_path = jsonl_manager.get_jsonl_path(timestamp=timestamp, task_id=task_id)

        # メタデータを書き込み
        jsonl_manager.write_metadata(jsonl_path, args.description, timestamp)

        # 状態ファイルを更新して、このタスクファイルを現在の書き込み先として設定
        effective_date = jsonl_manager.get_effective_date(timestamp)
        jsonl_manager._set_current_task_file(jsonl_path, effective_date.strftime("%Y-%m-%d"))

        print(f"✓ 新しいJSONLファイルを作成しました: {jsonl_path}")
        print(f"  タスク: {args.description}")
        print(f"  タスクID: {task_id}")
        print(f"  実効日付: {effective_date.strftime('%Y-%m-%d')}")
        print()
        print("このファイルに今後のログが記録されます。")
        print("日付が変わると（朝5時を過ぎると）、自動的に日付ベースのファイルに切り替わります。")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
