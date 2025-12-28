#!/usr/bin/env python3
"""
ScreenOCR Logger - Main Script

毎分スクリーンショットを取得し、Vision FrameworkでOCR処理を行い、
JSONL形式でログを記録するメインスクリプト。
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ローカルモジュールをインポート
from screenshot import get_active_window, take_screenshot
from ocr import perform_ocr


# 設定
JSONL_PATH = Path.home() / ".screenocr_logger.jsonl"
SCREENSHOT_DIR = Path("/tmp/screen-times")
TIMEOUT_SECONDS = 30  # OCRタイムアウト（日本語認識のため長めに設定）
SCREENSHOT_RETENTION_HOURS = 72  # スクリーンショット保持期間（時間）


def save_to_jsonl(timestamp: datetime, window: str, text: str) -> None:
    """
    JSONL形式でログを保存

    Args:
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

    try:
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        print(f"Error: Failed to write to JSONL: {e}", file=sys.stderr)
        raise


def cleanup_old_screenshots() -> None:
    """
    古いスクリーンショット（保持期間を超えたもの）を削除
    """
    try:
        cutoff_time = time.time() - (SCREENSHOT_RETENTION_HOURS * 3600)
        pattern = "screenshot_*.png"
        deleted_count = 0

        for screenshot in SCREENSHOT_DIR.glob(pattern):
            try:
                # ファイルの最終更新時刻を確認
                if screenshot.stat().st_mtime < cutoff_time:
                    screenshot.unlink()
                    deleted_count += 1
            except Exception as file_error:
                # 個別のファイル削除エラーは無視して続行
                print(f"Warning: Failed to delete {screenshot}: {file_error}", file=sys.stderr)
                continue

        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old screenshot(s)")

    except Exception as cleanup_error:
        print(f"Warning: Screenshot cleanup failed: {cleanup_error}", file=sys.stderr)


def main():
    """メイン処理"""
    try:
        # タイムスタンプ取得
        timestamp = datetime.now()

        # アクティブウィンドウ取得
        window, window_bounds = get_active_window()
        print(f"Active window: {window}")
        if window_bounds:
            print(f"Window bounds: {window_bounds}")

        # スクリーンショット取得（ウィンドウ領域のみ）
        screenshot_path = take_screenshot(SCREENSHOT_DIR, window_bounds)
        print(f"Screenshot saved: {screenshot_path}")

        # OCR処理
        text = perform_ocr(screenshot_path, TIMEOUT_SECONDS)
        print(f"OCR completed: {len(text)} characters")

        # JSONL保存
        save_to_jsonl(timestamp, window, text)
        print(f"Log saved to: {JSONL_PATH}")

        # スクリーンショットは保持（72時間後に自動削除される）
        print(f"Screenshot will be kept for {SCREENSHOT_RETENTION_HOURS} hours")

        # 古いスクリーンショットをクリーンアップ
        cleanup_old_screenshots()

    except Exception as main_error:
        print(f"Fatal error: {main_error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
