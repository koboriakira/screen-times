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

from .record_merger import RecordMerger


class JsonlManager:
    """JSONLファイルの管理を行うクラス"""

    # ファイルサイズの上限（100KB = 約50Kトークン）
    MAX_FILE_SIZE_BYTES = 100 * 1024  # 100KB

    def __init__(self, base_dir: Path = Path.home(), merge_threshold: Optional[float] = None):
        """
        初期化

        Args:
            base_dir: JSONLファイルを保存するベースディレクトリ
            merge_threshold: 類似レコードをマージするしきい値（0.0～1.0）
                           Noneの場合はマージを行わない
        """
        self.base_dir = base_dir
        self.logs_dir = base_dir / ".screenocr_logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.state_file = self.logs_dir / ".current_jsonl"
        self.merge_threshold = merge_threshold
        self.merger: Optional[RecordMerger] = None
        if merge_threshold is not None:
            self.merger = RecordMerger(threshold=merge_threshold)

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
            return (timestamp - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            # 5時以降は当日
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_jsonl_path(
        self,
        timestamp: Optional[datetime] = None,
        task_id: Optional[str] = None,
        include_time: bool = False,
    ) -> Path:
        """
        JSONLファイルのパスを取得

        Args:
            timestamp: タイムスタンプ（Noneの場合は現在時刻）
            task_id: タスクID（手動分割時に指定）
            include_time: Trueの場合、ファイル名に時刻を含める（サイズベース分割用）

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
        elif include_time:
            # サイズベース分割: 日付 + 時刻
            time_str = timestamp.strftime("%H%M%S")
            filename = f"{date_str}_{time_str}.jsonl"
        else:
            # 自動分割: 日付のみ（下位互換性のため残す）
            filename = f"{date_str}.jsonl"

        return self.logs_dir / filename

    def write_metadata(
        self, filepath: Path, description: str, timestamp: Optional[datetime] = None
    ) -> None:
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
            "effective_date": self.get_effective_date(timestamp).strftime("%Y-%m-%d"),
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

    def append_record(self, filepath: Path, timestamp: datetime, window: str, text: str) -> Path:
        """
        レコードをJSONLファイルに追記

        マージが有効な場合は、類似レコードを自動的にマージする。
        ファイルサイズが上限（100KB）を超えている場合は、新しいタイムスタンプ付きファイルを作成する。

        Args:
            filepath: JSONLファイルのパス
            timestamp: タイムスタンプ
            window: ウィンドウ名
            text: OCRテキスト

        Returns:
            実際に書き込んだファイルのPath（サイズ超過時は新しいファイルのパス）
        """
        # ファイルサイズチェック: 既存ファイルが上限を超えていたら新ファイルを作成
        if filepath.exists() and filepath.stat().st_size >= self.MAX_FILE_SIZE_BYTES:
            # マージャーがある場合はフラッシュして書き込む
            if self.merger:
                buffered_record = self.merger.flush()
                if buffered_record:
                    self._write_record(filepath, buffered_record)

            # 新しいタイムスタンプ付きファイルを作成
            filepath = self.get_jsonl_path(timestamp=timestamp, include_time=True)
            # メタデータを書き込む
            description = (
                f"Auto-split due to file size " f"exceeding {self.MAX_FILE_SIZE_BYTES} bytes"
            )
            self.write_metadata(
                filepath,
                description=description,
                timestamp=timestamp,
            )

        record = {
            "timestamp": timestamp.isoformat(),
            "window": window,
            "text": text,
            "text_length": len(text),
        }

        # マージが有効な場合
        if self.merger:
            output_record = self.merger.add_record(record)
            if output_record:
                # マージされなかったレコードを書き込む
                self._write_record(filepath, output_record)
        else:
            # マージなしの場合は直接書き込む
            self._write_record(filepath, record)

        return filepath

    def _write_record(self, filepath: Path, record: dict) -> None:
        """
        レコードをJSONLファイルに書き込む

        Args:
            filepath: JSONLファイルのパス
            record: 書き込むレコード
        """
        with open(filepath, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def flush_merger(self, filepath: Path) -> None:
        """
        マージャーのバッファをフラッシュして書き込む

        プログラム終了時などに呼び出す。

        Args:
            filepath: JSONLファイルのパス
        """
        if self.merger:
            buffered_record = self.merger.flush()
            if buffered_record:
                self._write_record(filepath, buffered_record)

    def get_current_jsonl_path(self, timestamp: Optional[datetime] = None) -> Path:
        """
        現在使用すべきJSONLファイルのパスを取得

        手動分割で設定されたタスクファイルがある場合はそれを使用し、
        日付が変わっていたら自動的に日付ベースのファイルに切り替える。
        同じ日付のファイルが複数ある場合は、最新のファイルを返す。

        Args:
            timestamp: タイムスタンプ（Noneの場合は現在時刻）

        Returns:
            JSONLファイルのPath
        """
        if timestamp is None:
            timestamp = datetime.now()

        current_effective_date = self.get_effective_date(timestamp)

        # 状態ファイルから現在のタスクファイル情報を取得
        task_file_info = self._get_current_task_file()

        if task_file_info:
            task_file_path = Path(task_file_info["path"])
            task_effective_date_str = task_file_info.get("effective_date")

            # タスクファイルが存在し、かつ日付が変わっていない場合はそのファイルを使用
            if (
                task_file_path.exists()
                and task_effective_date_str == current_effective_date.strftime("%Y-%m-%d")
            ):
                return task_file_path
            else:
                # 日付が変わった、またはファイルが削除されている場合は状態をクリア
                self._clear_current_task_file()

        # 同じ日付のファイルを検索（タイムスタンプ付きも含む）
        date_str = current_effective_date.strftime("%Y-%m-%d")
        pattern = f"{date_str}*.jsonl"
        existing_files = sorted(self.logs_dir.glob(pattern), reverse=True)

        if existing_files:
            # 最新のファイルを返す（ファイル名の降順でソート済み）
            return existing_files[0]
        else:
            # ファイルがない場合は日付ベースのファイルパスを返す
            return self.get_jsonl_path(timestamp=timestamp, task_id=None, include_time=False)

    def _get_current_task_file(self) -> Optional[dict]:
        """
        状態ファイルから現在のタスクファイル情報を取得

        Returns:
            タスクファイル情報の辞書、または None
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, IOError):
            return None

    def _set_current_task_file(self, filepath: Path, effective_date: str) -> None:
        """
        状態ファイルに現在のタスクファイル情報を保存

        Args:
            filepath: タスクファイルのパス
            effective_date: 実効日付（YYYY-MM-DD形式）
        """
        task_info = {"path": str(filepath), "effective_date": effective_date}

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, ensure_ascii=False)

    def _clear_current_task_file(self) -> None:
        """
        状態ファイルをクリア（日付ベースのファイルに戻る）
        """
        if self.state_file.exists():
            self.state_file.unlink()
