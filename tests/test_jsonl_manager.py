#!/usr/bin/env python3
"""
JSONL Manager のユニットテスト
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from screen_times.jsonl_manager import JsonlManager


class TestJsonlManager:
    """JsonlManagerクラスのテスト"""

    def test_get_effective_date_before_5am(self):
        """5時より前の時刻は前日として扱われることをテスト"""
        manager = JsonlManager()

        # 2025-12-28 04:59 → 2025-12-27
        timestamp = datetime(2025, 12, 28, 4, 59, 0)
        effective_date = manager.get_effective_date(timestamp)

        assert effective_date.year == 2025
        assert effective_date.month == 12
        assert effective_date.day == 27
        assert effective_date.hour == 0
        assert effective_date.minute == 0
        assert effective_date.second == 0

    def test_get_effective_date_at_5am(self):
        """5時ちょうどは当日として扱われることをテスト"""
        manager = JsonlManager()

        # 2025-12-28 05:00 → 2025-12-28
        timestamp = datetime(2025, 12, 28, 5, 0, 0)
        effective_date = manager.get_effective_date(timestamp)

        assert effective_date.year == 2025
        assert effective_date.month == 12
        assert effective_date.day == 28

    def test_get_effective_date_after_5am(self):
        """5時より後の時刻は当日として扱われることをテスト"""
        manager = JsonlManager()

        # 2025-12-28 15:30 → 2025-12-28
        timestamp = datetime(2025, 12, 28, 15, 30, 0)
        effective_date = manager.get_effective_date(timestamp)

        assert effective_date.year == 2025
        assert effective_date.month == 12
        assert effective_date.day == 28

    def test_get_jsonl_path_automatic(self):
        """自動分割時のJSONLパス生成をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            jsonl_path = manager.get_jsonl_path(timestamp=timestamp)

            # ファイル名が日付のみであることを確認
            assert jsonl_path.name == "2025-12-28.jsonl"
            assert jsonl_path.parent == Path(tmpdir) / ".screenocr_logs"

    def test_get_jsonl_path_manual_with_task_id(self):
        """手動分割時のJSONLパス生成をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 10, 30, 45)
            task_id = "feature-implementation"
            jsonl_path = manager.get_jsonl_path(timestamp=timestamp, task_id=task_id)

            # ファイル名が日付+タスクID+時刻であることを確認
            assert jsonl_path.name == "2025-12-28_feature-implementation_103045.jsonl"
            assert jsonl_path.parent == Path(tmpdir) / ".screenocr_logs"

    def test_get_jsonl_path_before_5am(self):
        """5時より前の時刻のJSONLパス生成をテスト（前日扱い）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 3, 0, 0)
            jsonl_path = manager.get_jsonl_path(timestamp=timestamp)

            # 前日の日付が使用されることを確認
            assert jsonl_path.name == "2025-12-27.jsonl"

    def test_write_metadata(self):
        """メタデータの書き込みをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            test_file = Path(tmpdir) / "test_metadata.jsonl"
            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            description = "テスト機能の実装"

            manager.write_metadata(test_file, description, timestamp)

            # ファイルが作成されていることを確認
            assert test_file.exists()

            # メタデータが正しく書き込まれていることを確認
            with open(test_file, "r", encoding="utf-8") as f:
                metadata = json.loads(f.readline())

            assert metadata["type"] == "task_metadata"
            assert metadata["description"] == description
            assert metadata["timestamp"] == timestamp.isoformat()
            assert metadata["effective_date"] == "2025-12-28"

    def test_write_metadata_preserves_existing_content(self):
        """既存の内容を保持してメタデータを書き込むことをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_existing.jsonl"

            # 既存のコンテンツを書き込み
            existing_record = {
                "timestamp": "2025-12-28T09:00:00",
                "window": "Test",
                "text": "existing",
            }
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(existing_record, f, ensure_ascii=False)
                f.write("\n")

            # メタデータを追加
            manager = JsonlManager(base_dir=Path(tmpdir))
            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            manager.write_metadata(test_file, "新しいタスク", timestamp)

            # メタデータが1行目に、既存の内容が2行目に存在することを確認
            with open(test_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2
            metadata = json.loads(lines[0])
            existing = json.loads(lines[1])

            assert metadata["type"] == "task_metadata"
            assert existing["window"] == "Test"

    def test_append_record(self):
        """レコードの追記をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            test_file = Path(tmpdir) / "test_append.jsonl"
            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            window = "TestWindow"
            text = "テストテキスト"

            manager.append_record(test_file, timestamp, window, text)

            # レコードが正しく書き込まれていることを確認
            with open(test_file, "r", encoding="utf-8") as f:
                record = json.loads(f.readline())

            assert record["timestamp"] == timestamp.isoformat()
            assert record["window"] == window
            assert record["text"] == text
            assert record["text_length"] == len(text)

    def test_append_multiple_records(self):
        """複数レコードの追記をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            test_file = Path(tmpdir) / "test_multiple.jsonl"

            # 3つのレコードを追記
            for i in range(3):
                timestamp = datetime(2025, 12, 28, 10, i, 0)
                manager.append_record(test_file, timestamp, f"Window{i}", f"Text{i}")

            # 3行書き込まれていることを確認
            with open(test_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 3

            # 各レコードが正しいことを確認
            for i, line in enumerate(lines):
                record = json.loads(line)
                assert record["window"] == f"Window{i}"
                assert record["text"] == f"Text{i}"

    def test_get_current_jsonl_path(self):
        """現在使用すべきJSONLパスの取得をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            jsonl_path = manager.get_current_jsonl_path(timestamp)

            # 自動分割用のパスが返されることを確認
            assert jsonl_path.name == "2025-12-28.jsonl"

    def test_task_file_state_management(self):
        """タスクファイルの状態管理をテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            task_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28_test-task_100000.jsonl"
            task_file.touch()

            # 状態ファイルを設定
            manager._set_current_task_file(task_file, "2025-12-28")

            # 状態ファイルから取得できることを確認
            task_info = manager._get_current_task_file()
            assert task_info is not None
            assert task_info["path"] == str(task_file)
            assert task_info["effective_date"] == "2025-12-28"

            # get_current_jsonl_pathがタスクファイルを返すことを確認
            current_path = manager.get_current_jsonl_path(timestamp)
            assert current_path == task_file

            # 状態をクリア
            manager._clear_current_task_file()

            # クリア後は既存ファイルの中で最新のファイルが返されることを確認
            # （この場合はタスクファイルが最新）
            current_path = manager.get_current_jsonl_path(timestamp)
            assert current_path == task_file

    def test_task_file_auto_switch_on_date_change(self):
        """日付が変わったら自動的に日付ベースのファイルに切り替わることをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            # 12/28のタスクファイルを設定
            timestamp1 = datetime(2025, 12, 28, 10, 0, 0)
            task_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28_test-task_100000.jsonl"
            task_file.touch()
            manager._set_current_task_file(task_file, "2025-12-28")

            # 同じ日付の場合はタスクファイルが返される
            current_path = manager.get_current_jsonl_path(timestamp1)
            assert current_path == task_file

            # 日付が変わった場合（12/29の6時）
            timestamp2 = datetime(2025, 12, 29, 6, 0, 0)
            current_path = manager.get_current_jsonl_path(timestamp2)

            # 日付ベースのファイルに自動切り替え
            assert current_path.name == "2025-12-29.jsonl"

            # 状態ファイルがクリアされていることを確認
            assert manager._get_current_task_file() is None

    def test_task_file_cleared_when_file_deleted(self):
        """タスクファイルが削除された場合に日付ベースに切り替わることをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            task_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28_test-task_100000.jsonl"
            task_file.touch()
            manager._set_current_task_file(task_file, "2025-12-28")

            # タスクファイルを削除
            task_file.unlink()

            # 日付ベースのファイルに自動切り替え
            current_path = manager.get_current_jsonl_path(timestamp)
            assert current_path.name == "2025-12-28.jsonl"

            # 状態ファイルがクリアされていることを確認
            assert manager._get_current_task_file() is None

    def test_get_jsonl_path_with_include_time(self):
        """include_time=Trueで時刻付きファイル名が生成されることをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            timestamp = datetime(2025, 12, 28, 14, 30, 25)
            jsonl_path = manager.get_jsonl_path(timestamp=timestamp, include_time=True)

            # ファイル名が日付+時刻であることを確認
            assert jsonl_path.name == "2025-12-28_143025.jsonl"
            assert jsonl_path.parent == Path(tmpdir) / ".screenocr_logs"

    def test_append_record_auto_split_on_size_exceeded(self):
        """ファイルサイズが上限を超えたら自動的に新ファイルが作成されることをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            # 最初のファイルを作成し、100KBを超えるデータを書き込む
            test_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28.jsonl"
            test_file.parent.mkdir(exist_ok=True)

            # 100KBを超えるダミーデータを作成（約101KB）
            large_text = "x" * (100 * 1024 + 1000)
            timestamp1 = datetime(2025, 12, 28, 10, 0, 0)
            with open(test_file, "w", encoding="utf-8") as f:
                record = {
                    "timestamp": timestamp1.isoformat(),
                    "window": "TestWindow",
                    "text": large_text,
                    "text_length": len(large_text),
                }
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")

            # ファイルサイズが100KBを超えていることを確認
            assert test_file.stat().st_size > manager.MAX_FILE_SIZE_BYTES

            # 新しいレコードを追記すると、新しいファイルが作成されるはず
            timestamp2 = datetime(2025, 12, 28, 10, 5, 30)
            actual_path = manager.append_record(test_file, timestamp2, "TestWindow2", "New text")

            # 新しいファイルが作成されたことを確認
            assert actual_path != test_file
            assert actual_path.name.startswith("2025-12-28_")
            assert actual_path.name.endswith(".jsonl")
            assert actual_path.exists()

            # 新しいファイルにメタデータとレコードが書き込まれていることを確認
            with open(actual_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2  # メタデータ + レコード

            metadata = json.loads(lines[0])
            assert metadata["type"] == "task_metadata"
            assert "Auto-split" in metadata["description"]

            new_record = json.loads(lines[1])
            assert new_record["window"] == "TestWindow2"
            assert new_record["text"] == "New text"

            # 元のファイルはそのまま保持されていることを確認
            assert test_file.exists()

    def test_append_record_no_split_when_size_ok(self):
        """ファイルサイズが上限以下の場合は分割されないことをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            test_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28.jsonl"
            test_file.parent.mkdir(exist_ok=True)

            # 小さなデータを書き込む
            timestamp1 = datetime(2025, 12, 28, 10, 0, 0)
            manager.append_record(test_file, timestamp1, "TestWindow1", "Small text 1")

            # ファイルサイズが100KB未満であることを確認
            assert test_file.stat().st_size < manager.MAX_FILE_SIZE_BYTES

            # 2つ目のレコードを追記
            timestamp2 = datetime(2025, 12, 28, 10, 5, 0)
            actual_path = manager.append_record(
                test_file, timestamp2, "TestWindow2", "Small text 2"
            )

            # 同じファイルに追記されたことを確認
            assert actual_path == test_file

            # 2つのレコードが存在することを確認
            with open(test_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2

    def test_get_current_jsonl_path_returns_latest_file(self):
        """同じ日付の複数ファイルから最新のファイルを返すことをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))
            logs_dir = Path(tmpdir) / ".screenocr_logs"
            logs_dir.mkdir(exist_ok=True)

            # 同じ日付の複数のファイルを作成
            file1 = logs_dir / "2025-12-28.jsonl"
            file2 = logs_dir / "2025-12-28_100000.jsonl"
            file3 = logs_dir / "2025-12-28_103000.jsonl"

            file1.touch()
            file2.touch()
            file3.touch()

            timestamp = datetime(2025, 12, 28, 10, 35, 0)
            current_path = manager.get_current_jsonl_path(timestamp)

            # 最新のファイル（アルファベット順で最後）が返されることを確認
            assert current_path == file3

    def test_append_record_returns_path(self):
        """append_recordが書き込んだファイルパスを返すことをテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = JsonlManager(base_dir=Path(tmpdir))

            test_file = Path(tmpdir) / ".screenocr_logs" / "2025-12-28.jsonl"
            test_file.parent.mkdir(exist_ok=True)

            timestamp = datetime(2025, 12, 28, 10, 0, 0)
            returned_path = manager.append_record(test_file, timestamp, "TestWindow", "Test text")

            # 返されたパスが正しいことを確認
            assert returned_path == test_file
            assert returned_path.exists()
