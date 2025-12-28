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
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# 設定
JSONL_PATH = Path.home() / ".screenocr_logger.jsonl"
SCREENSHOT_DIR = Path("/tmp")
TIMEOUT_SECONDS = 5
SCREENSHOT_RETENTION_HOURS = 72  # スクリーンショット保持期間（時間）
DEBUG_KEEP_IMAGES = os.environ.get("DEBUG_KEEP_IMAGES", "0") == "1"


class TimeoutError(Exception):
    """タイムアウトエラー"""
    pass


def timeout_handler(signum, frame):
    """タイムアウトハンドラ"""
    raise TimeoutError("OCR processing timeout")


def get_active_window() -> tuple[str, Optional[tuple[int, int, int, int]]]:
    """
    AppleScript経由でアクティブウィンドウ名と位置を取得

    Returns:
        (アプリケーション名, ウィンドウ位置 (x, y, width, height) または None)
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
        app_name = result.stdout.strip() or "Unknown"

        # PyObjCでウィンドウ情報を取得
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )

            # 画面上の全ウィンドウ情報を取得
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )

            # アクティブなアプリのウィンドウを探す
            # 正規化して比較用の文字列を作成
            normalized_app_name = app_name.lower().replace('-', '').replace(' ', '')

            for window in window_list:
                owner_name = window.get('kCGWindowOwnerName', '')
                layer = window.get('kCGWindowLayer', 0)

                # レイヤー0（通常のウィンドウ）のみ対象
                if layer != 0:
                    continue

                # 正規化して比較
                normalized_owner = owner_name.lower().replace('-', '').replace(' ', '')

                # 部分一致または完全一致で判定
                # (例: "wezterm-gui" と "WezTerm"、"Electron" と "Code")
                if (normalized_app_name in normalized_owner or
                    normalized_owner in normalized_app_name or
                    normalized_app_name == normalized_owner):
                    bounds = window.get('kCGWindowBounds', {})
                    if bounds:
                        x = int(bounds['X'])
                        y = int(bounds['Y'])
                        w = int(bounds['Width'])
                        h = int(bounds['Height'])
                        print(f"Debug: Matched window - Owner: {owner_name}, Bounds: ({x}, {y}, {w}, {h})", file=sys.stderr)
                        return (app_name, (x, y, w, h))

            return (app_name, None)

        except Exception as bounds_error:
            print(f"Warning: Could not get window bounds: {bounds_error}", file=sys.stderr)
            return (app_name, None)

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as get_window_error:
        print(f"Warning: Failed to get active window: {get_window_error}", file=sys.stderr)
        return ("Unknown", None)


def take_screenshot(window_bounds: Optional[tuple[int, int, int, int]] = None) -> Path:
    """
    スクリーンショットを取得

    Args:
        window_bounds: ウィンドウの位置とサイズ (x, y, w, h)。Noneの場合は画面全体

    Returns:
        スクリーンショットのパス
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOT_DIR / f"screenshot_{timestamp}.png"

    try:
        if window_bounds:
            x, y, w, h = window_bounds
            # -R オプションで特定の領域をキャプチャ
            cmd = ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", str(screenshot_path)]
        else:
            # 画面全体をキャプチャ（フォールバック）
            cmd = ["screencapture", "-x", str(screenshot_path)]

        subprocess.run(cmd, check=True, timeout=5)

        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot was not created: {screenshot_path}")

        return screenshot_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as screenshot_error:
        print(f"Error: Failed to take screenshot: {screenshot_error}", file=sys.stderr)
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
        from Cocoa import NSURL
        from Quartz import CGImageSourceCreateWithURL, CGImageSourceCreateImageAtIndex
        from Vision import (
            VNImageRequestHandler,
            VNRecognizeTextRequest,
        )
    except ImportError as import_error:
        print(f"Error: pyobjc frameworks not found: {import_error}", file=sys.stderr)
        print("Install with: pip install -r requirements.txt", file=sys.stderr)
        return ""

    # タイムアウト設定
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    try:
        # 画像URLを作成
        url = NSURL.fileURLWithPath_(str(image_path))

        # CGImageを読み込み
        image_source = CGImageSourceCreateWithURL(url, None)
        if not image_source:
            print(f"Error: Failed to create image source", file=sys.stderr)
            return ""

        cg_image = CGImageSourceCreateImageAtIndex(image_source, 0, None)
        if not cg_image:
            print(f"Error: Failed to get CGImage", file=sys.stderr)
            return ""

        # リクエスト作成（認識レベルは設定しない - デフォルトでAccurate）
        request = VNRecognizeTextRequest.alloc().init()

        # ハンドラ作成と実行
        handler = VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, {})
        success, error = handler.performRequests_error_([request], None)

        if not success or error:
            print(f"Error: Vision Framework request failed: {error}", file=sys.stderr)
            return ""

        # 結果取得
        results = request.results()
        if not results:
            print("Warning: No OCR results returned", file=sys.stderr)
            return ""

        print(f"Debug: Found {len(results)} text observations", file=sys.stderr)

        # テキストを結合
        text_lines = []
        for observation in results:
            top_candidate = observation.topCandidates_(1)[0]
            text_lines.append(top_candidate.string())

        return "\n".join(text_lines)

    except Exception as ocr_error:
        print(f"Error: OCR processing failed: {ocr_error}", file=sys.stderr)
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
        screenshot_path = take_screenshot(window_bounds)
        print(f"Screenshot saved: {screenshot_path}")

        # OCR処理
        text = perform_ocr(screenshot_path)
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
