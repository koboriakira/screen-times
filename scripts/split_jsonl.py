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
from jsonl_manager import JsonlManager


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
        help="タスクの説明（例: '〇〇機能の実装作業'）"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.home(),
        help="JSONLファイルを保存するベースディレクトリ（デフォルト: ホームディレクトリ）"
    )

    args = parser.parse_args()

    try:
        # JSONLマネージャーの初期化
        jsonl_manager = JsonlManager(base_dir=args.base_dir)

        # タスクIDを生成
        task_id = generate_task_id(args.description)
        timestamp = datetime.now()

        # 新しいJSONLファイルのパスを取得
        jsonl_path = jsonl_manager.get_jsonl_path(timestamp=timestamp, task_id=task_id)

        # メタデータを書き込み
        jsonl_manager.write_metadata(jsonl_path, args.description, timestamp)

        print(f"✓ 新しいJSONLファイルを作成しました: {jsonl_path}")
        print(f"  タスク: {args.description}")
        print(f"  タスクID: {task_id}")
        print(f"  実効日付: {jsonl_manager.get_effective_date(timestamp).strftime('%Y-%m-%d')}")
        print()
        print("このファイルに今後のログが記録されます。")
        print("注意: 自動分割（日付ベース）は引き続き動作します。")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
