#!/usr/bin/env python3
"""
ScreenOCR Logger - Main Script

毎分スクリーンショットを取得し、Vision FrameworkでOCR処理を行い、
JSONL形式でログを記録するメインスクリプト。
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# 設定
JSONL_PATH = Path.home() / ".screenocr_logger.jsonl"
SCREENSHOT_DIR = Path("/tmp")
TIMEOUT_SECONDS = 5
DEBUG_KEEP_IMAGES = os.environ.get("DEBUG_KEEP_IMAGES", "0") == "1"


class TimeoutError(Exception):
    """タイムアウトエラー"""
    pass


def timeout_handler(signum, frame):
    """タイムアウトハンドラ"""
    raise TimeoutError("OCR processing timeout")


def get_active_window() -> str:
    """
    AppleScript経由でアクティブウィンドウ名を取得

    Returns:
        アクティブなアプリケーション名
    """
    script_path = Path(__file__).parent / "screenshot_window.applescript"

    try:
        result = subprocess.run(
            ["osascript", str(script_path)],
            capture_output=True,
            text=True,
            timeout=3,
            check=True
        )
        return result.stdout.strip() or "Unknown"
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"Warning: Failed to get active window: {e}", file=sys.stderr)
        return "Unknown"


def take_screenshot() -> Path:
    """
    スクリーンショットを取得

    Returns:
        スクリーンショットのパス
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOT_DIR / f"screenshot_{timestamp}.png"

    try:
        subprocess.run(
            ["screencapture", "-x", str(screenshot_path)],
            check=True,
            timeout=5
        )

        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot was not created: {screenshot_path}")

        return screenshot_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: Failed to take screenshot: {e}", file=sys.stderr)
        raise


def perform_ocr(image_path: Path) -> str:
    """
    Vision FrameworkでOCR処理を実行

    Args:
        image_path: 画像ファイルのパス

    Returns:
        認識されたテキスト
    """
    # pyobjc imports (遅延インポート)
    try:
        from Foundation import NSURL
        from Vision import (
            VNImageRequestHandler,
            VNRecognizeTextRequest,
        )
    except ImportError as e:
        print(f"Error: pyobjc frameworks not found: {e}", file=sys.stderr)
        print("Install with: pip install -r requirements.txt", file=sys.stderr)
        return ""

    # タイムアウト設定
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    try:
        # 画像URLを作成
        url = NSURL.fileURLWithPath_(str(image_path))

        # リクエスト作成
        request = VNRecognizeTextRequest.alloc().init()
        # Accurate recognition level
        request.setRecognitionLevel_(1)  # 1 = VNRequestTextRecognitionLevelAccurate

        # ハンドラ作成と実行
        handler = VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        error = None
        success = handler.performRequests_error_([request], error)

        if not success or error:
            print(f"Error: Vision Framework request failed: {error}", file=sys.stderr)
            return ""

        # 結果取得
        results = request.results()
        if not results:
            print("Warning: No OCR results returned", file=sys.stderr)
            return ""

        print(f"Debug: Found {len(results)} text observations", file=sys.stderr)
        text_lines = []
        for observation in results:
            top_candidate = observation.topCandidates_(1)[0]
            text_lines.append(top_candidate.string())

        return "\n".join(text_lines)

    except TimeoutError:
        print(f"Error: OCR timeout after {TIMEOUT_SECONDS} seconds", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Error: OCR processing failed: {e}", file=sys.stderr)
        return ""
    finally:
        signal.alarm(0)  # タイムアウトキャンセル


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


def main():
    """メイン処理"""
    screenshot_path: Optional[Path] = None

    try:
        # タイムスタンプ取得
        timestamp = datetime.now()

        # アクティブウィンドウ取得
        window = get_active_window()
        print(f"Active window: {window}")

        # スクリーンショット取得
        screenshot_path = take_screenshot()
        print(f"Screenshot saved: {screenshot_path}")

        # OCR処理
        text = perform_ocr(screenshot_path)
        print(f"OCR completed: {len(text)} characters")

        # JSONL保存
        save_to_jsonl(timestamp, window, text)
        print(f"Log saved to: {JSONL_PATH}")

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        # 画像削除
        if screenshot_path and screenshot_path.exists():
            if DEBUG_KEEP_IMAGES:
                print(f"Debug: Keeping image: {screenshot_path}")
            else:
                try:
                    screenshot_path.unlink()
                    print(f"Screenshot deleted: {screenshot_path}")
                except Exception as e:
                    print(f"Warning: Failed to delete screenshot: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
