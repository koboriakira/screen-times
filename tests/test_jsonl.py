#!/usr/bin/env python3
"""
JSONL操作のユニットテスト
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# scriptsディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_jsonl_write_and_read():
    """JSONLファイルへの書き込みと読み込みのテスト"""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # テストデータ
        test_records = [
            {
                "timestamp": "2025-12-28T12:00:00",
                "window": "TestApp",
                "text": "Test text",
                "text_length": 9,
            },
            {
                "timestamp": "2025-12-28T12:01:00",
                "window": "AnotherApp",
                "text": "日本語テキスト",
                "text_length": 7,
            },
        ]

        # 書き込み
        with open(temp_path, "w", encoding="utf-8") as f:
            for record in test_records:
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")

        # 読み込み
        records = []
        with open(temp_path, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))

        # 検証
        assert len(records) == 2
        assert records[0]["window"] == "TestApp"
        assert records[1]["text"] == "日本語テキスト"

    finally:
        temp_path.unlink()


def test_jsonl_utf8_encoding():
    """UTF-8エンコーディングのテスト"""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # 日本語を含むテストデータ
        test_text = "これは日本語のテストです 🎉"
        record = {
            "timestamp": datetime.now().isoformat(),
            "window": "テストアプリ",
            "text": test_text,
            "text_length": len(test_text),
        }

        # 書き込み
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

        # 読み込み
        with open(temp_path, "r", encoding="utf-8") as f:
            loaded = json.loads(f.readline())

        # 検証
        assert loaded["text"] == test_text
        assert loaded["window"] == "テストアプリ"

    finally:
        temp_path.unlink()


def test_jsonl_append():
    """JSONLファイルへの追記のテスト"""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # 初回書き込み
        record1 = {"id": 1, "data": "first"}
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(record1, f, ensure_ascii=False)
            f.write("\n")

        # 追記
        record2 = {"id": 2, "data": "second"}
        with open(temp_path, "a", encoding="utf-8") as f:
            json.dump(record2, f, ensure_ascii=False)
            f.write("\n")

        # 読み込み
        records = []
        with open(temp_path, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))

        # 検証
        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[1]["id"] == 2

    finally:
        temp_path.unlink()


def test_timestamp_format():
    """タイムスタンプ形式の検証"""
    timestamp = datetime.now()
    iso_string = timestamp.isoformat()

    # ISO 8601形式であることを確認
    assert "T" in iso_string
    assert len(iso_string) >= 19  # YYYY-MM-DDTHH:MM:SS

    # パース可能であることを確認
    parsed = datetime.fromisoformat(iso_string)
    assert parsed.year == timestamp.year
    assert parsed.month == timestamp.month
    assert parsed.day == timestamp.day
