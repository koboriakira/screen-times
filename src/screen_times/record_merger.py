#!/usr/bin/env python3
"""
Record Merger - 類似レコードのマージ処理

連続するOCRレコードにおいて、テキスト内容がほぼ同一の場合にマージする。
"""

from typing import Any, Dict, Optional

from rapidfuzz import fuzz


def should_merge(prev: Dict[str, Any], curr: Dict[str, Any], threshold: float = 0.90) -> bool:
    """
    マージすべきかどうかの判定

    以下の両方を満たす場合にマージ対象とする：
    1. window が同一であること
    2. テキスト類似度が指定のしきい値以上であること

    Args:
        prev: 前のレコード
        curr: 現在のレコード
        threshold: 類似度のしきい値（0.0～1.0）

    Returns:
        マージすべき場合はTrue
    """
    # windowが異なる場合はマージしない
    if prev.get("window") != curr.get("window"):
        return False

    prev_text = prev.get("text", "")
    curr_text = curr.get("text", "")

    # 両方とも空の場合もマージする
    if not prev_text and not curr_text:
        return True

    # どちらか一方だけが空の場合はマージしない
    if not prev_text or not curr_text:
        return False

    # テキスト類似度を計算（0-100の範囲なので100で割る）
    similarity: float = fuzz.ratio(prev_text, curr_text) / 100.0
    return similarity >= threshold


def merge_records(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, Any]:
    """
    2つのレコードをマージ

    マージ時は以下のルールで統合する：
    - timestamp: 最初のレコードの値を保持
    - timestamp_end: 最後のレコードのtimestampを設定
    - window: 保持
    - text: 最初のレコードの値を保持
    - text_length: 最初のレコードの値を保持
    - merged_count: マージされたレコード数（既存の値に+1）

    Args:
        prev: マージ先のレコード
        curr: マージ元のレコード

    Returns:
        マージされたレコード
    """
    # prevをベースにコピー
    merged = prev.copy()

    # timestamp_endを更新
    merged["timestamp_end"] = curr["timestamp"]

    # merged_countを更新（prevに既にある場合は+1、ない場合は2）
    merged["merged_count"] = prev.get("merged_count", 1) + 1

    return merged


class RecordMerger:
    """
    レコードのマージを管理するクラス

    連続するレコードをバッファリングして、類似度に基づいてマージする。
    """

    def __init__(self, threshold: float = 0.90):
        """
        初期化

        Args:
            threshold: 類似度のしきい値（0.0～1.0、デフォルト0.90）
        """
        self.threshold = threshold
        self.buffer: Optional[Dict[str, Any]] = None

    def add_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        レコードを追加

        前回のレコードとマージすべきかを判定し、マージしない場合は
        前回のレコードを返す。マージする場合はNoneを返す。

        Args:
            record: 追加するレコード

        Returns:
            出力すべきレコード（マージした場合はNone）
        """
        # 最初のレコードの場合はバッファに保存
        if self.buffer is None:
            self.buffer = record
            return None

        # マージすべきか判定
        if should_merge(self.buffer, record, self.threshold):
            # マージしてバッファを更新
            self.buffer = merge_records(self.buffer, record)
            return None
        else:
            # マージしない場合は、バッファを出力して新しいレコードを保存
            output = self.buffer
            self.buffer = record
            return output

    def flush(self) -> Optional[Dict[str, Any]]:
        """
        バッファに残っているレコードを取得

        Returns:
            バッファに残っているレコード（ない場合はNone）
        """
        output = self.buffer
        self.buffer = None
        return output
