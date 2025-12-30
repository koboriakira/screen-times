#!/usr/bin/env python3
"""
record_mergerモジュールのテスト
"""

from screen_times.record_merger import RecordMerger, merge_records, should_merge


class TestShouldMerge:
    """should_merge関数のテスト"""

    def test_same_window_and_identical_text(self):
        """同じwindowで同じテキストの場合、マージすべき"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }
        assert should_merge(prev, curr, threshold=0.90) is True

    def test_same_window_and_similar_text(self):
        """同じwindowで類似テキスト（90%以上）の場合、マージすべき"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World! This is a test.",
            "text_length": 28,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Hello World! This is a test!",  # 末尾のみ異なる
            "text_length": 28,
        }
        assert should_merge(prev, curr, threshold=0.90) is True

    def test_different_window(self):
        """windowが異なる場合、マージしない"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Firefox",
            "text": "Hello World",
            "text_length": 11,
        }
        assert should_merge(prev, curr, threshold=0.90) is False

    def test_low_similarity(self):
        """類似度が低い場合（90%未満）、マージしない"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Completely different text",
            "text_length": 25,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Another unrelated content here",
            "text_length": 30,
        }
        assert should_merge(prev, curr, threshold=0.90) is False

    def test_both_empty_text(self):
        """両方とも空テキストの場合、マージすべき"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "",
            "text_length": 0,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "",
            "text_length": 0,
        }
        assert should_merge(prev, curr, threshold=0.90) is True

    def test_one_empty_text(self):
        """どちらか一方が空の場合、マージしない"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Some text",
            "text_length": 9,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "",
            "text_length": 0,
        }
        assert should_merge(prev, curr, threshold=0.90) is False


class TestMergeRecords:
    """merge_records関数のテスト"""

    def test_merge_two_records(self):
        """2つのレコードをマージ"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }
        curr = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }

        merged = merge_records(prev, curr)

        assert merged["timestamp"] == "2025-12-29T10:00:00"
        assert merged["timestamp_end"] == "2025-12-29T10:01:00"
        assert merged["window"] == "Chrome"
        assert merged["text"] == "Hello World"
        assert merged["text_length"] == 11
        assert merged["merged_count"] == 2

    def test_merge_already_merged_record(self):
        """すでにマージされたレコードに追加マージ"""
        prev = {
            "timestamp": "2025-12-29T10:00:00",
            "timestamp_end": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
            "merged_count": 2,
        }
        curr = {
            "timestamp": "2025-12-29T10:02:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }

        merged = merge_records(prev, curr)

        assert merged["timestamp"] == "2025-12-29T10:00:00"
        assert merged["timestamp_end"] == "2025-12-29T10:02:00"
        assert merged["merged_count"] == 3


class TestRecordMerger:
    """RecordMergerクラスのテスト"""

    def test_add_first_record(self):
        """最初のレコードはバッファに保存されるだけ"""
        merger = RecordMerger(threshold=0.90)
        record = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }

        output = merger.add_record(record)
        assert output is None

    def test_merge_similar_records(self):
        """類似レコードはマージされる"""
        merger = RecordMerger(threshold=0.90)

        record1 = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }
        record2 = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Chrome",
            "text": "Hello World",
            "text_length": 11,
        }

        output1 = merger.add_record(record1)
        assert output1 is None

        output2 = merger.add_record(record2)
        assert output2 is None  # マージされたのでまだ出力しない

        # フラッシュして確認
        final = merger.flush()
        assert final is not None
        assert final["merged_count"] == 2

    def test_output_different_records(self):
        """異なるレコードは個別に出力される"""
        merger = RecordMerger(threshold=0.90)

        record1 = {
            "timestamp": "2025-12-29T10:00:00",
            "window": "Chrome",
            "text": "First text",
            "text_length": 10,
        }
        record2 = {
            "timestamp": "2025-12-29T10:01:00",
            "window": "Firefox",
            "text": "Second text",
            "text_length": 11,
        }

        output1 = merger.add_record(record1)
        assert output1 is None

        output2 = merger.add_record(record2)
        assert output2 is not None
        assert output2["window"] == "Chrome"
        assert output2["text"] == "First text"

        # フラッシュして2つ目を確認
        final = merger.flush()
        assert final is not None
        assert final["window"] == "Firefox"
        assert final["text"] == "Second text"

    def test_multiple_merges_then_different(self):
        """複数回マージした後、異なるレコードが来た場合"""
        merger = RecordMerger(threshold=0.90)

        records = [
            {
                "timestamp": "2025-12-29T10:00:00",
                "window": "Chrome",
                "text": "Same text",
                "text_length": 9,
            },
            {
                "timestamp": "2025-12-29T10:01:00",
                "window": "Chrome",
                "text": "Same text",
                "text_length": 9,
            },
            {
                "timestamp": "2025-12-29T10:02:00",
                "window": "Chrome",
                "text": "Same text",
                "text_length": 9,
            },
            {
                "timestamp": "2025-12-29T10:03:00",
                "window": "Firefox",
                "text": "Different app",
                "text_length": 13,
            },
        ]

        outputs = []
        for record in records:
            output = merger.add_record(record)
            if output:
                outputs.append(output)

        # 最初の3つがマージされて1つ出力されるはず
        assert len(outputs) == 1
        assert outputs[0]["merged_count"] == 3
        assert outputs[0]["timestamp_end"] == "2025-12-29T10:02:00"

        # フラッシュして最後のを確認
        final = merger.flush()
        assert final is not None
        assert final["window"] == "Firefox"
        assert "merged_count" not in final  # マージされていない

    def test_flush_empty_buffer(self):
        """空のバッファをフラッシュ"""
        merger = RecordMerger(threshold=0.90)
        output = merger.flush()
        assert output is None
