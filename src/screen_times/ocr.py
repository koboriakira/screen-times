#!/usr/bin/env python3
"""
OCR処理モジュール

Vision FrameworkでOCR処理を実行
"""

import signal
import sys
from pathlib import Path


class TimeoutError(Exception):
    """タイムアウトエラー"""

    pass


def timeout_handler(signum, frame):
    """タイムアウトハンドラ"""
    raise TimeoutError("OCR processing timeout")


def perform_ocr(image_path: Path, timeout_seconds: int = 5) -> str:
    """
    Vision FrameworkでOCR処理を実行

    Args:
        image_path: 画像ファイルのパス
        timeout_seconds: タイムアウト時間（秒）

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
            VNRequestTextRecognitionLevelAccurate,
        )
    except ImportError as import_error:
        print(f"Error: pyobjc frameworks not found: {import_error}", file=sys.stderr)
        print("Install with: pip install -r requirements.txt", file=sys.stderr)
        return ""

    # タイムアウト設定
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        # 画像URLを作成
        url = NSURL.fileURLWithPath_(str(image_path))

        # CGImageを読み込み
        image_source = CGImageSourceCreateWithURL(url, None)
        if not image_source:
            print("Error: Failed to create image source", file=sys.stderr)
            return ""

        cg_image = CGImageSourceCreateImageAtIndex(image_source, 0, None)
        if not cg_image:
            print("Error: Failed to get CGImage", file=sys.stderr)
            return ""

        # リクエスト作成
        request = VNRecognizeTextRequest.alloc().init()

        # 日本語と英語を認識するように設定
        request.setRecognitionLanguages_(["ja-JP", "en-US"])

        # 高精度モードを明示的に設定
        request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)

        # 言語補正を有効化（誤認識を減らす）
        request.setUsesLanguageCorrection_(True)

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
