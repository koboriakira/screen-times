#!/usr/bin/env python3
"""
JSONL Manager - JSONLファイルの管理を行うモジュール

日付ベースのファイル分割と手動分割をサポート。
朝5時を基準として日付を判定する。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class JsonlManager:
    """JSONLファイルの管理を行うクラス"""

    def __init__(self, base_dir: Path = Path.home()):
        """
        初期化

        Args:
            base_dir: JSONLファイルを保存するベースディレクトリ
        """
        self.base_dir = base_dir
        self.logs_dir = base_dir / ".screenocr_logs"
        self.logs_dir.mkdir(exist_ok=True)

    def get_effective_date(self, timestamp: datetime) -> datetime:
        """
        朝5時を基準とした実効日付を取得

        5時より前の時刻は前日として扱う。
        例: 2025-12-28 04:59 → 2025-12-27
            2025-12-28 05:00 → 2025-12-28

        Args:
            timestamp: 判定対象のタイムスタンプ

        Returns:
            実効日付（datetime）
        """
        if timestamp.hour < 5:
            # 5時より前なら前日とする
            return (timestamp - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # 5時以降は当日
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_jsonl_path(self, timestamp: Optional[datetime] = None, task_id: Optional[str] = None) -> Path:
        """
        JSONLファイルのパスを取得

        Args:
            timestamp: タイムスタンプ（Noneの場合は現在時刻）
            task_id: タスクID（手動分割時に指定）

        Returns:
            JSONLファイルのPath
        """
        if timestamp is None:
            timestamp = datetime.now()

        effective_date = self.get_effective_date(timestamp)
        date_str = effective_date.strftime("%Y-%m-%d")

        if task_id:
            # 手動分割: 日付 + タスクID + タイムスタンプ
            time_str = timestamp.strftime("%H%M%S")
            filename = f"{date_str}_{task_id}_{time_str}.jsonl"
        else:
            # 自動分割: 日付のみ
            filename = f"{date_str}.jsonl"

        return self.logs_dir / filename

    def write_metadata(self, filepath: Path, description: str, timestamp: Optional[datetime] = None) -> None:
        """
        メタデータをJSONLファイルの1行目に書き込む

        Args:
            filepath: JSONLファイルのパス
            description: タスクの説明
            timestamp: タイムスタンプ（Noneの場合は現在時刻）
        """
        if timestamp is None:
            timestamp = datetime.now()

        metadata = {
            "type": "task_metadata",
            "timestamp": timestamp.isoformat(),
            "description": description,
            "effective_date": self.get_effective_date(timestamp).strftime("%Y-%m-%d")
        }

        # ファイルが存在する場合は既存の内容を読み込む
        existing_lines = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        # メタデータを先頭に書き込み、その後に既存の内容を追加
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)
            f.write("\n")
            for line in existing_lines:
                f.write(line)

    def append_record(self, filepath: Path, timestamp: datetime, window: str, text: str) -> None:
        """
        レコードをJSONLファイルに追記

        Args:
            filepath: JSONLファイルのパス
            timestamp: タイムスタンプ
            window: ウィンドウ名
            text: OCRテキスト
        """
        record = {
            "timestamp": timestamp.isoformat(),
            "window": window,
            "text": text,
            "text_length": len(text)
        }

        with open(filepath, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def get_current_jsonl_path(self, timestamp: Optional[datetime] = None) -> Path:
        """
        現在使用すべきJSONLファイルのパスを取得（自動分割用）

        Args:
            timestamp: タイムスタンプ（Noneの場合は現在時刻）

        Returns:
            JSONLファイルのPath
        """
        return self.get_jsonl_path(timestamp=timestamp, task_id=None)
